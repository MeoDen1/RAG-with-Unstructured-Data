from dotenv import load_dotenv
import os

from openai import OpenAI
import google.generativeai as genai


class LLM:
    """
    Large Language Model interface
    """
    def __init__(self) -> None:
        load_dotenv()
        pass

    def generate(self, prompt: str) -> str:
        """
        Generate LLM's response from `prompt` text
        """
        pass



class GeminiModel(LLM):
    """
    Gemini model
    """
    def __init__(self, model_name="gemini-1.0-pro-latest") -> None:
        super().__init__()
        GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        # Check if api key is valid
        assert GOOGLE_API_KEY

        genai.configure(api_key=GOOGLE_API_KEY)
        self.__gen_model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> str:
        return self.__gen_model.generate_content(prompt).text
    


class OpenAIModel(LLM):
    """
    OpenAI model
    """
    def __init__(self, model_name="gpt-4o") -> None:
        super().__init__()
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model_name

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"content": prompt}
            ]
        )

        return response.choices[0].message.content