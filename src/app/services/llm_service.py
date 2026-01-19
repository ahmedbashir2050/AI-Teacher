import logging

from config import OPENAI_API_KEY
from openai import APIError, OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, api_key: str = OPENAI_API_KEY):
        """
        Initializes the LLMService.
        """
        if not api_key:
            logger.error("OpenAI API key is missing.")
            raise ValueError("OpenAI API key is required and was not found.")
        self.client = OpenAI(api_key=api_key)
        logger.info("LLMService initialized successfully.")

    def get_embedding(
        self, text: str, model: str = "text-embedding-3-small"
    ) -> list[float]:
        """
        Generates an embedding for the given text.
        """
        logger.info(f"Generating embedding for text using model '{model}'.")
        try:
            # The API expects a list of texts, even if it's just one.
            response = self.client.embeddings.create(
                input=[text.replace("\n", " ")], model=model
            )
            logger.info("Embedding generated successfully.")
            return response.data[0].embedding
        except APIError as e:
            logger.error(f"OpenAI API error during embedding generation: {e}")
            raise  # Re-raise the exception to be handled by the caller

    def get_chat_completion(self, prompt: str, model: str = "gpt-4o") -> str:
        """
        Gets a chat completion from the OpenAI API using a structured prompt.
        """
        logger.info(f"Requesting chat completion using model '{model}'.")
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    # No system message is needed as the prompt is highly specific
                    {"role": "user", "content": prompt}
                ],
            )
            completion = response.choices[0].message.content
            logger.info("Chat completion received successfully.")
            return completion
        except APIError as e:
            logger.error(f"OpenAI API error during chat completion: {e}")
            raise  # Re-raise the exception


# Singleton instance
llm_service = LLMService()
