import numpy as np
import pandas as pd
import os
import torch
import pymupdf
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv
import google.generativeai as genai

# NOTE: .env contain API_KEY field

# This is just a clear structure of simple RAG. Go to notebook_v1 for more detail

load_dotenv()

API_KEY = os.getenv('API_KEY')
genai.configure(api_key=API_KEY)


class RAGv1:
    def __init__(self, file_path: str, chunk_size=32) -> None:
        # Load embedding model
        self.load_embedded_model()

        # Load gemini model
        self.gen_model = genai.GenerativeModel('gemini-1.0-pro-latest')

        # Generate chunks
        chunks = self.load_document(file_path, chunk_size)
        # chunks: list of object {chunk_id, page, text}

        # Build vector store
        self.text = [chunk['text'] for chunk in chunks]
        self.vector_store = {}

        batch_size = 1000

        vectors = []
        num_batch = len(chunks) // batch_size

        for i in range(num_batch + 1):
            print(f"Embedding batch {i + 1}")
            vectors += self.get_embedding(self.text[i * batch_size : (i + 1) * batch_size])

        for id, vector in vectors:
            self.vector_store[id] = np.array(vector, dtype=np.float32)

        
            
    def load_document(self, file_path: str, chunk_size=32):
        """
        Loads pdf from `file_path` and generate list of chunks from the file
        """
        doc = pymupdf.open(file_path)
        output = []

        chunk_id = 0
        for i, page in enumerate(doc):
            # Get text per page
            text = page.get_text()

            # Clean text
            text = self.clean_text(text)

            words = text.split(' ')
            for j in range(0, len(words) - chunk_size + 1, 2):
                chunk = ' '.join(words[j:j + chunk_size])

                output.append({
                    'chunk_id': chunk_id,
                    'page': i,
                    'text': chunk,
                })

                chunk_id += 1
        
        return output  
        
       
    def clean_text(self, text: str):
        """
        Remove escaped and special characters from `text`
        """
        # filter = ''.join([chr(i) for i in range(1, 32)])
        # text = text.translate(str.maketrans('', '', filter)).strip()
        text = text.replace('-\n', '')
        text = text.replace('\n', ' ')
        text = text.replace(u'\xa0', u' ')

        while text.find('  ') != -1:
            text = text.replace('  ', ' ') 

        return text

    
    def load_embedded_model(self, model_name: str="BAAI/bge-small-en-v1.5"):
        """
        Load model to embed string
        """
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(self.device)

        assert self.tokenizer is not None
        assert self.model is not None

    def get_embedding(self, text: list[str] | str):
        inputs = self.tokenizer(text, return_tensors='pt', padding=True, truncation=True).to(self.device)

        with torch.no_grad():
            # reduce mean in sequence length axis
            output = self.model(**inputs).last_hidden_state.mean(dim=1)

        return output.tolist()
    
    def cosine_similarity(self, a, b):
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0
        else:
            return np.dot(a, b) / (norm_a * norm_b)
        
    def get_matches(self, vector_store, query: str, top_k: int=100):
        # Embedding query
        ce_output = self.get_embedding(query)[0] # (1, 384)

        scores = {}

        for vector_key in vector_store:
            vector_item = vector_store[vector_key]
            scores[vector_key] = self.cosine_similarity(ce_output, vector_item)

        def func(e):
            return e[1]
        
        # Sorted by cosine scores
        scores = sorted(scores.items(), key=func, reverse=True)[:top_k]
        ids = [score[0] for score in scores]

        return scores, ids
    
    def create_prompt(self, query: str, info: list[str]):
        ret = '\n- '
        prompt = f"I have the following information: \n- {ret.join(info)} \
        \nNow, i want you taking those information and answer the following question \
        \n\n{query} \n \
        \nMake sure the answers are detail and as exploratory as possible. Only take info from information list."
        return prompt

    def call(self, query: str):
        scores, match_ids = self.get_matches(self.vector_store, query)

        info = [self.text for id in match_ids]

        prompt = self.create_prompt(query, info)

        return self.gen_model.generate_content(prompt).text