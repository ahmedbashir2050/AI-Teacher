from app.services.llm_service import llm_service

def generate_embedding(text: str) -> list[float]:
    """
    Generates an embedding for a given text using the LLM service.
    """
    return llm_service.get_embedding(text)
