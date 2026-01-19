from services.llm_service import llm_service


async def generate_embedding(text: str) -> list[float]:
    """
    Generates an embedding for a given text using the LLM service.
    """
    return await llm_service.get_embedding(text)
