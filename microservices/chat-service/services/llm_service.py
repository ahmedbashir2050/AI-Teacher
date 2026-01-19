import hashlib
import json
import logging

import redis.asyncio as aioredis
from core.config import settings
from openai import APIError, AsyncOpenAI

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
            self.redis = await aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
        return self.redis

    async def get_chat_completion(
        self, messages: list[dict], model: str = "gpt-4o", temperature: float = 0.1
    ) -> str:
        """
        Gets a chat completion from the OpenAI model with a list of messages.
        Production-grade: Default temperature set to 0.1 for determinism.
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

    async def detect_intent_and_rewrite_query(
        self, user_message: str, history: str
    ) -> dict:
        """
        Detects user intent and rewrites the query for RAG with caching.
        """
        cache_key = (
            f"intent:{hashlib.md5((user_message + history).encode()).hexdigest()}"
        )
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
            {
                "role": "user",
                "content": f"History: {history}\n\nStudent Message: {user_message}",
            },
        ]
        response_text = await self.get_chat_completion(messages, model="gpt-4o-mini")
        try:
            # Simple cleanup for potential markdown blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            result = json.loads(response_text)
            await redis.setex(cache_key, 3600, json.dumps(result))  # Cache for 1 hour
            return result
        except Exception:
            return {
                "intent": "GENERAL",
                "mode": "UNDERSTANDING",
                "rewritten_query": user_message,
            }

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
        chunks_formatted = "\n".join(
            [f"[{i}] {chunk}" for i, chunk in enumerate(chunks)]
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Query: {query}\n\nChunks:\n{chunks_formatted}",
            },
        ]
        response_text = await self.get_chat_completion(messages, model="gpt-4o-mini")
        try:
            indices = [
                int(idx.strip())
                for idx in response_text.split(",")
                if idx.strip().isdigit()
            ]
            return [chunks[i] for i in indices if i < len(chunks)]
        except Exception:
            return chunks[:3]  # Fallback to top 3

    async def summarize_learning_state(self, current_summary: str, history: str) -> str:
        """
        Summarizes the user's learning state based on the conversation history.
        Deterministic and scoped.
        """
        system_prompt = """
Update the student's academic learning state summary.
Focus strictly on:
1. Specific academic concepts understood.
2. Specific concepts the student struggles with.
3. Progress toward curriculum goals.
Refuse to include any personal info or non-academic content.
Keep it concise and objective.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Current Summary: {current_summary}\n\nRecent History: {history}",
            },
        ]
        return await self.get_chat_completion(
            messages, model="gpt-4o-mini", temperature=0.0
        )

    async def check_groundedness(self, answer: str, context: str) -> bool:
        """
        Checks if the generated answer is grounded in the provided context.
        Returns True if grounded, False otherwise.
        """
        system_prompt = """
You are a strict academic auditor.
Verify if the following answer is fully supported by the provided context.
If the answer contains information NOT in the context, or contradicts it, return 'FALSE'.
If the answer is fully supported, return 'TRUE'.
Only return 'TRUE' or 'FALSE'.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nAnswer: {answer}"},
        ]
        response = await self.get_chat_completion(
            messages, model="gpt-4o-mini", temperature=0.0
        )
        return "TRUE" in response.upper()

    async def get_chat_completion_with_validation(
        self, messages: list[dict], context: str = None
    ) -> dict:
        """
        Enforces structured output validation and groundedness after LLM call.
        Returns a dict with 'answer' and 'source' info.
        """
        # Request JSON output
        messages.append(
            {
                "role": "system",
                "content": "You MUST return a JSON object with 'answer' and 'source' (book, page) keys. Ensure the 'answer' follows the Arabic structure: التعريف، الشرح، مثال، ملخص.",
            }
        )
        response_text = await self.get_chat_completion(
            messages, model="gpt-4o", temperature=0.1
        )

        try:
            # Simple cleanup for potential markdown blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            result = json.loads(response_text)
        except Exception:
            # Fallback if LLM failed to return valid JSON
            logger.error(f"Failed to parse LLM response as JSON: {response_text}")
            return {
                "answer": "عذراً، حدث خطأ في معالجة الإجابة بشكل صحيح.",
                "source": {"book": "N/A", "page": "N/A"},
            }

        # Groundedness Check
        if context and result.get("answer"):
            is_grounded = await self.check_groundedness(result["answer"], context)
            if not is_grounded:
                logger.warning("Hallucination detected! Groundedness check failed.")
                return {
                    "answer": "عذراً، هذا السؤال خارج نطاق المحتوى المقرر حالياً. أنا مصمم للمساعدة في محتوى المنهج الدراسي فقط لضمان دقة المعلومات.",
                    "source": {"book": "System", "page": "N/A"},
                    "hallucination": True,
                }

        return result

    async def get_cached_rag_results(
        self, query: str, collection: str, faculty: str, semester: str
    ):
        redis = await self._get_redis()
        key = f"rag_cache:{faculty}:{semester}:{hashlib.md5((query + collection).encode()).hexdigest()}"
        cached = await redis.get(key)
        return json.loads(cached) if cached else None

    async def cache_rag_results(
        self, query: str, collection: str, faculty: str, semester: str, results: list
    ):
        redis = await self._get_redis()
        key = f"rag_cache:{faculty}:{semester}:{hashlib.md5((query + collection).encode()).hexdigest()}"
        await redis.setex(key, 3600 * 6, json.dumps(results))  # 6 hours cache

    async def get_cached_response(self, faculty: str, semester: str, question: str):
        redis = await self._get_redis()
        norm_q = question.strip().lower()
        key = (
            f"ans_cache:{faculty}:{semester}:{hashlib.md5(norm_q.encode()).hexdigest()}"
        )
        return await redis.get(key)

    async def cache_response(
        self, faculty: str, semester: str, question: str, response: str
    ):
        if len(response) < 50:
            return  # Don't cache short/error responses
        redis = await self._get_redis()
        norm_q = question.strip().lower()
        key = (
            f"ans_cache:{faculty}:{semester}:{hashlib.md5(norm_q.encode()).hexdigest()}"
        )
        await redis.setex(key, 3600 * 24, response)  # 24 hours cache

    async def get_embedding(
        self, text: str, model: str = "text-embedding-3-small"
    ) -> list[float]:
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

            await redis.setex(
                cache_key, 86400, json.dumps(embedding)
            )  # Cache for 24 hours
            return embedding
        except APIError as e:
            logger.error(f"OpenAI API error during embedding: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_embedding: {e}")
            raise


# Singleton instance
llm_service = LLMService()
