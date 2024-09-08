from dotenv import load_dotenv
import os
from llama_index.embeddings.gemini import GeminiEmbedding

class EmbeddingModel:
    def __init__(self):
        load_dotenv()
        pass

    def embed(self, text: str):
        pass


class GeminiEmbeddingModel(EmbeddingModel):
    def __init__(self, model_name="models/embedding-001"):
        super().__init__()
        GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        # Check if api key is valid
        assert GOOGLE_API_KEY

        self.__embed_model = GeminiEmbedding(model_name, api_key=GOOGLE_API_KEY)

    def embed(self, text: str):
        return self.__embed_model.get_text_embedding(text)