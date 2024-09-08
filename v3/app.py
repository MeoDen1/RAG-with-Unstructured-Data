import os
from langchain_community.graphs import Neo4jGraph
import LLM, EmbeddingModel
from LLM import GeminiModel
from EmbeddingModel import GeminiEmbeddingModel
import cypher_query as cq
from prompts import community_answer_prompts, global_answer_prompts

class App:
    def __init__(self, llm: LLM, em: EmbeddingModel):
        # Connect to database
        
        NEO4J_URL = os.getenv('NEO4J_URL')
        NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
        NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
        NEO4J_DATABASE = os.getenv('NEO4J_DATABASE')

        print("Connecting to Database...")
        try:
            self.__kg = Neo4jGraph(NEO4J_URL, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE)
            print("Connect successfully!")
        except:
            raise NameError("Can not connect to Database")

        self.__llm = llm
        self.__gem = em
        self.__vector_index = "christmas_carol"

    def get_answers(self, query: str, communities):
        """
        Collect answers from relevant communities
        """
        answers = []

        for community in communities:
            summary, findings = community[1], community[4]
            prompt = community_answer_prompts.get_prompts(query, [summary, findings])
            
            try:
                answer = self.__llm.generate(prompt)
            except Exception as exp:
                print(f"Error counter: {exp} \n")
                continue

            # Filter answer
            if answer.find("<UNKNOWN>") != -1:
                continue

            answers.append(answer)

        return answers



    def generate(self, query: str):
        embedding_query = self.__gem.embed(query)
        communities = cq.get_search_result(self.__kg, self.__vector_index, 20, embedding_query)
        
        answers = self.get_answers(query, communities)

        prompt = global_answer_prompts.get_prompts(answers)
        global_answer = self.__llm.generate(prompt)

        return global_answer