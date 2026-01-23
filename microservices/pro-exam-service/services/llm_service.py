import json
import logging
from core.config import settings
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_pro_exam(self, context: list[dict]) -> dict:
        formatted_chunks = []
        for i, chunk in enumerate(context):
            formatted_chunks.append(
                f"Chunk [{i}] (Source: {chunk.get('source')}, Page: {chunk.get('page')}):\n{chunk.get('text')}"
            )
        context_str = "\n\n".join(formatted_chunks)

        prompt = f"""
Based ONLY on the provided academic text, generate a professional university-level exam in Arabic.
The exam must have exactly 4 sections:

Section 1: Matching (A↔B) - 5 pairs.
Section 2: Matching (A↔B) - 5 pairs.
Section 3: True/False - 10 statements.
Section 4: Multiple Choice Questions (MCQ) - 10 questions, each with 4 options.

Every question must be linked to a source page from the provided chunks.

Format the output as a JSON object with the following structure:
{{
  "sections": [
    {{
      "section_id": "matching_1",
      "type": "matching",
      "title": "Matching Question 1",
      "questions": [
        {{ "pair_id": 1, "item_a": "...", "item_b": "...", "source_page": "page number" }},
        ... (exactly 5 pairs)
      ]
    }},
    {{
      "section_id": "matching_2",
      "type": "matching",
      "title": "Matching Question 2",
      "questions": [
        {{ "pair_id": 1, "item_a": "...", "item_b": "...", "source_page": "page number" }},
        ... (exactly 5 pairs)
      ]
    }},
    {{
      "section_id": "tf",
      "type": "tf",
      "title": "True/False Statements",
      "questions": [
        {{ "id": 1, "statement": "...", "correct_answer": true, "source_page": "page number" }},
        ... (exactly 10 statements)
      ]
    }},
    {{
      "section_id": "mcq",
      "type": "mcq",
      "title": "Multiple Choice Questions",
      "questions": [
        {{ "id": 1, "question": "...", "options": ["opt1", "opt2", "opt3", "opt4"], "correct_answer": "opt1", "source_page": "page number" }},
        ... (exactly 10 questions)
      ]
    }}
  ]
}}

Academic Text:
{context_str}
"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error in LLM generation: {e}")
            raise

llm_service = LLMService()
