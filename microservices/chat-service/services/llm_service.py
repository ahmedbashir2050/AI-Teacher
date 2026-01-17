from openai import AsyncOpenAI, APIError
from ..core.config import settings
import logging
import aioredis
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        """
        Initializes the LLMService with the OpenAI API key and Redis.
        """
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.redis = None

    async def _get_redis(self):
        if self.redis is None:
            self.redis = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        return self.redis

    async def get_chat_completion(self, messages: list[dict], model: str = "gpt-4o", temperature: float = 0.0) -> str:
        """
        Gets a chat completion from the OpenAI model with a list of messages.
        """
        try:
            logger.info(f"Requesting chat completion with model {model}")
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
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

    async def detect_intent_and_rewrite_query(self, user_message: str, history: str) -> dict:
        """
        Detects user intent and rewrites the query for RAG with caching.
        """
        cache_key = f"intent:{hashlib.md5((user_message + history).encode()).hexdigest()}"
        redis = await self._get_redis()

        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        system_prompt = """
Analyze the student message and history.
Identify intent: DEFINITION, EXAMPLE, EXAM_STYLE, REVISION, CONFUSED, OUTSIDE_SYLLABUS, or GENERAL.
Identify mode: UNDERSTANDING, EXAM, or QUESTION_PREDICTION.
Rewrite the query to be optimized for vector search in academic material.

Output JSON:
{
  "intent": "...",
  "mode": "...",
  "rewritten_query": "..."
}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"History: {history}\n\nStudent Message: {user_message}"}
        ]
        response_text = await self.get_chat_completion(messages, model="gpt-4o-mini")
        try:
            # Simple cleanup for potential markdown blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            result = json.loads(response_text)
            await redis.setex(cache_key, 3600, json.dumps(result)) # Cache for 1 hour
            return result
        except:
            return {"intent": "GENERAL", "mode": "UNDERSTANDING", "rewritten_query": user_message}

    async def rerank_results(self, query: str, chunks: list[str]) -> list[str]:
        """
        Reranks RAG chunks based on relevance to the query.
        """
        if not chunks:
            return []

        system_prompt = """
You are an academic reranker. Rate each chunk's relevance to the user query from 0 to 10.
Return only the indices of the most relevant chunks (score > 7) in order of relevance, as a comma-separated list.
Example: 2, 0, 4
"""
        chunks_formatted = "\n".join([f"[{i}] {chunk}" for i, chunk in enumerate(chunks)])
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\n\nChunks:\n{chunks_formatted}"}
        ]
        response_text = await self.get_chat_completion(messages, model="gpt-4o-mini")
        try:
            indices = [int(idx.strip()) for idx in response_text.split(",") if idx.strip().isdigit()]
            return [chunks[i] for i in indices if i < len(chunks)]
        except:
            return chunks[:3] # Fallback to top 3

    async def summarize_learning_state(self, current_summary: str, history: str) -> str:
        """
        Summarizes the user's learning state based on the conversation history.
        """
        system_prompt = """
Update the student's learning state summary.
Focus on: topics understood, topics they struggle with, and overall progress.
Keep it concise and in English for internal use.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current Summary: {current_summary}\n\nRecent History: {history}"}
        ]
        return await self.get_chat_completion(messages, model="gpt-4o-mini")

    async def get_embedding(self, text: str, model: str = "text-embedding-3-small") -> list[float]:
        """
        Generates an embedding for a given text with caching.
        """
        cache_key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
        redis = await self._get_redis()

        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        try:
            logger.info(f"Generating embedding with model {model}")
            # Ensure text is not empty and within limits (simplified)
            text = text.replace("\n", " ")
            response = await self.client.embeddings.create(input=[text], model=model)
            embedding = response.data[0].embedding
            logger.info("Successfully generated embedding")

            await redis.setex(cache_key, 86400, json.dumps(embedding)) # Cache for 24 hours
            return embedding
        except APIError as e:
            logger.error(f"OpenAI API error during embedding: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_embedding: {e}")
            raise

# Singleton instance
llm_service = LLMService()
