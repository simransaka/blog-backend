import json
import time
import random
import logging

from google import genai
from google.genai import types
from google.oauth2 import service_account
from google.api_core.exceptions import ResourceExhausted


class GeminiClient:

    def __init__(
        self,
        service_account_path: str,
        location: str = "global",
        model_name: str = "gemini-2.5-flash",
    ):
        self.logger = logging.getLogger(__name__)

        self.location = location
        self.model_name = model_name

        # Load service account JSON
        try:
            with open(service_account_path, "r") as file:
                service_account_info = json.load(file)

        except (FileNotFoundError, json.JSONDecodeError):
            self.logger.exception(
                "Failed to load service account JSON."
            )
            raise

        # Extract project ID from service account JSON
        self.project_id = service_account_info["project_id"]

        # Initialize service account credentials
        self.credentials = (
            service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=[
                    "https://www.googleapis.com/auth/cloud-platform"
                ],
            )
        )

        # Initialize Vertex AI Gemini client
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
            credentials=self.credentials,
        )

        self.logger.info(
            f"Gemini client initialized successfully. "
            f"Project: {self.project_id}, "
            f"Model: {self.model_name}, "
            f"Location: {self.location}"
        )

    def generate_response(
        self,
        prompt: str,
        max_retries: int = 3,
        base_delay: int = 2,
    ):
        """
        Generate Gemini response with exponential backoff
        on ResourceExhausted errors.
        """

        for attempt in range(1, max_retries + 1):

            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=2048,
                    ),
                )

                return response

            except ResourceExhausted:

                if attempt < max_retries:

                    wait = (
                        base_delay * (2 ** (attempt - 1))
                        + random.uniform(0, 1)
                    )

                    self.logger.warning(
                        f"Resource exhausted "
                        f"(attempt {attempt}/{max_retries}). "
                        f"Retrying in {wait:.1f}s..."
                    )

                    time.sleep(wait)

                else:
                    self.logger.exception(
                        "Resource exhausted after maximum retries."
                    )
                    raise

            except Exception:
                self.logger.exception(
                    "Error while generating Gemini response."
                )
                raise

    def close(self):
        """Close Gemini client connection."""
        self.client.close()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    gemini = GeminiClient(
        service_account_path="service-account.json",
        location="global",
        model_name="gemini-2.5-flash",
    )

    try:
        prompt = """
        Explain how Retrieval Augmented Generation (RAG) works.
        """

        response = gemini.generate_response(prompt)

        print("\nGemini Response:\n")
        print(response.text)

    except Exception as e:
        logging.error(f"Gemini execution failed: {e}")

    finally:
        gemini.close()