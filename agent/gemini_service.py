import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


class GeminiService:

    def __init__(self):

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = "gemini-3.1-flash-lite"


    def generate_response(self, prompt):

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return response.text


    def generate_json_response(self, prompt):

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return response.text