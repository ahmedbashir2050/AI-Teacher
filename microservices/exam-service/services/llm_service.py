from openai import AsyncOpenAI, APIError
from ..core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        """
        Initializes the LLMService with the OpenAI API key.
        """
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def get_chat_completion(self, prompt: str, model: str = "gpt-4o") -> str:
        """
        Gets a chat completion from the OpenAI model.
        """
        try:
            logger.info(f"Requesting chat completion with model {model}")
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0, # Keep it deterministic for academic use cases
            )
            content = response.choices[0].message.content
            logger.info("Successfully received chat completion")
            return content
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return "عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى لاحقاً."
        except Exception as e:
            logger.error(f"Unexpected error in get_chat_completion: {e}")
            return "عذراً، حدث خطأ غير متوقع."

    async def get_embedding(self, text: str, model: str = "text-embedding-3-small") -> list[float]:
        """
        Generates an embedding for a given text.
        """
        try:
            logger.info(f"Generating embedding with model {model}")
            # Ensure text is not empty and within limits (simplified)
            text = text.replace("\n", " ")
            response = await self.client.embeddings.create(input=[text], model=model)
            embedding = response.data[0].embedding
            logger.info("Successfully generated embedding")
            return embedding
        except APIError as e:
            logger.error(f"OpenAI API error during embedding: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_embedding: {e}")
            raise

# Singleton instance
llm_service = LLMService()
