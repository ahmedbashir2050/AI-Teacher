from .embeddings import generate_embedding
from services.qdrant_service import qdrant_service

async def retrieve_relevant_chunks(query: str, top_k: int = 5) -> list[str]:
    """
    Retrieves the most relevant text chunks for a given query.
    """
    # 1. Generate query embedding
    query_vector = await generate_embedding(query)

    # 2. Search Qdrant for similar vectors
    search_results = qdrant_service.search(vector=query_vector, limit=top_k)

    # 3. Extract the text from the payload
    relevant_chunks = [point.payload["text"] for point in search_results]

    return relevant_chunks
