import os
import time

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

        self.model = "gemini-3.5-flash-lite"

    def _generate_with_retry(self, **kwargs):

        max_retries = 3

        for attempt in range(max_retries):

            try:

                return self.client.models.generate_content(
                    **kwargs
                )

            except Exception as e:

                error_message = str(e)

                if "503" not in error_message and "UNAVAILABLE" not in error_message:
                    raise

                if attempt == max_retries - 1:
                    raise RuntimeError(
                        "Gemini is temporarily unavailable after "
                        f"{max_retries} attempts. Please try again later."
                    ) from e

                wait_time = 2 ** attempt

                print(
                    f"Gemini temporarily unavailable. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    def generate_response(self, prompt):

        response = self._generate_with_retry(
            model=self.model,
            contents=prompt
        )

        return response.text

    def generate_json_response(self, prompt):

        response = self._generate_with_retry(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return response.text