import numpy as np
import pandas as pd
import pymupdf
import networkx as nx
from dotenv import load_dotenv
import os

from langchain.text_splitter import CharacterTextSplitter
from langchain_community.graphs import Neo4jGraph
import google.generativeai as genai
from llama_index.embeddings.gemini import GeminiEmbedding

# NOTE
# This is just a clear structure of the system

# Load environment
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
NEO4J_URL = os.getenv('NEO4J_URL')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE')

genai.configure(api_key=GOOGLE_API_KEY)


class KG:
    def __init__(self):
        # Init model
        self.embed_model = GeminiEmbedding(
            model_name="models/embedding-001", api_key=GOOGLE_API_KEY
        )

        # Init kg
        self.kg = Neo4jGraph(url=NEO4J_URL, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE)
        
        # Init generative AI
        self.gen_model = genai.GenerativeModel('gemini-1.0-pro-latest')
    
    def get_chunks(self, file_path: str):
        """
        Read data from `file_path`, return list of chunk nodes
        """
        # Read string from pdf
        doc = pymupdf.open(file_path)
        doc_text = '\n\n'.join([doc[i].get_text() for i in range(2, len(doc))])

        # Create chunks
        text_splitter = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=1500,
            chunk_overlap=200,
        )

        chunks = text_splitter.split_text(doc_text)

        # Embedding chunks
        embed_chunks = []
        count = 0

        for chunk in chunks:
            embed_chunks.append(self.embed_model.get_text_embedding(chunk))
            count += 1
            if count % 10 == 0:
                print("Chunk count: %d" % count)

        return [{'chunk': chunks[i], 'embedding': embed_chunks[i]} for i in range(len(chunk))]



    def build_graph(self, docId: str, title: str, author: str, file_path: str):
        """
        Build knowledge graph base on data of `file_path` following graph structure v1
        """


        # Create document node
        query = """
        MERGE (d: Document {docId: $docId})
        SET d.title = $title,
            d.author = $author
        """

        self.kg.query(query, params={'docId': docId, 'title': title, 'author': author})


        print("Getting data...")
        data = self.get_chunks(file_path)

        print("Building graph...")

        # Create first chunk as head of linked list
        query = """
        MERGE (c: Chunk {chunkId: $firstChunkId)
        SET c.text = $row.chunk
        WITH c
        CALL db.create.setNodeVectorProperty(c, "embedding", $row.embedding) 

        MATCH (d: Document {docId: $docId})
        MERGE (c)-[:PART_OF]->(d)
        """

        self.kg.query(query, params={"row": data[0], "firstChunkId": docId + "-chunk-0000", "docId": docId})

        # Add other chunks to the graph
        query = """
        MERGE (c: Chunk {chunkId: $chunkId})
        SET c.text = $row.chunk
        WITH c
        CALL db.create.setNodeVectorProperty(c, "embedding", $row.embedding) 

        MATCH (d: Document {docId: $docId})
        MERGE (c)-[:PART_OF]->(d)
        WITH c
        MATCH (c1: Chunk {chunkId: $prevChunkId})
        MERGE (c1)-[:NEXT]->(c)
        """
        node_count = 0
        for i in range(1, len(data)):
            chunkId = docId + "-chunk-" + str(i).zfill(4)
            prevChunkId = docId + "-chunk-" + str(i - 1).zfill(4)
            
            self.kg.query(query, params={"chunkId": chunkId, "prevChunkId": prevChunkId, "docId": docId, "row": data[i]})

            if (node_count + 1) % 100 == 0:
                print("Node count: %d" % (node_count + 1))

            node_count += 1

        print("Total nodes are created: %d" % (node_count + 1)) 

        # Create index for chunks
        query = """
        CREATE VECTOR INDEX chunks
        FOR (c: Chunk)
        ON c.embedding
        OPTIONS {indexConfig: {
            `vector.dimensions`: 768,
            `vector.similarity_function`: 'cosine'
        }}
        """

        self.kg.query(query)
        print("Indexes have been created")

    
    def create_prompt(self, query: str, info: list[str]):
        ret = '\n- '
        prompt = f"I have the following information: \n- {ret.join(info)} \
        \nNow, i want you only take those information and answer the following question \
        \n\n{query} \n \
        \nRemember, only take info from information list. \
        \nIf the information list is empty or irrelevant, return 'Can not provide any information'"
        return prompt
    
    
    def chat(self, question: str):
        question_embedding = self.embed_model.get_text_embedding(question)

        query = """
        CALL db.index.vector.queryNodes("chunks", 10, $question_embedding)
        YIELD node, score
        RETURN node.text, score, 
        [(prev:Chunk)-[:NEXT]->(node) | prev.text] AS prevChunk,
        [(node)-[:NEXT]->(next:Chunk) | next.text] AS nextChunk
        """

        result = self.kg.query(query, params={"question_embedding": question_embedding})

        info_list = []
        # Retrieve information and create prompt
        for row in result:
            prev_chunk = row['prevChunk'][0] if len(row['prevChunk']) != 0 else ""
            next_chunk = row['nextChunk'][0] if len(row['nextChunk']) != 0 else ""

            info = prev_chunk + "\n" + row['node.text'] + "\n" + next_chunk
            info_list.append(info)

        prompt = self.create_prompt(question, info_list)


        return self.gen_model.generate_content(prompt).text