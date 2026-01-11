from qdrant_client import QdrantClient
import os
from typing import Optional

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL)
    return _client


def create_collection_if_not_exists(collection_name: str):
    qdrant_client = get_qdrant_client()
    try:
        qdrant_client.get_collection(collection_name=collection_name)
    except Exception:
        qdrant_client.recreate_collection(
            collection_name=collection_name,
            vectors_config={"size": 384, "distance": "Cosine"}
        )
