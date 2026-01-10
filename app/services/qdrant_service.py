from qdrant_client import QdrantClient, models
from app.config import QDRANT_URL
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self, collection_name: str = "ai-teacher"):
        """
        Initializes the QdrantService.
        """
        logger.info(f"Connecting to Qdrant at {QDRANT_URL}")
        self.client = QdrantClient(url=QDRANT_URL)
        self.collection_name = collection_name

    def create_collection_if_not_exists(self, vector_size: int, distance=models.Distance.COSINE):
        """
        Creates a new collection in Qdrant if it doesn't already exist.
        """
        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists.")
            # You might want to add a check here to ensure the vector size matches
        except Exception as e:
            logger.info(f"Collection '{self.collection_name}' not found. Creating new collection.")
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=distance),
            )
            logger.info(f"Successfully created collection '{self.collection_name}'.")

    def upsert_points(self, points: list[models.PointStruct]):
        """
        Upserts (inserts or updates) a batch of points into the collection.
        """
        if not points:
            logger.warning("Upsert operation called with no points.")
            return

        logger.info(f"Upserting {len(points)} points into collection '{self.collection_name}'.")
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True  # Wait for the operation to complete
        )
        logger.info("Upsert operation completed.")

    def search(self, vector: list[float], limit: int = 5) -> list[models.ScoredPoint]:
        """
        Performs a similarity search for a given vector.
        """
        logger.info(f"Performing search in '{self.collection_name}' with a vector of size {len(vector)}.")
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
            with_payload=True  # Ensure the payload (the text) is returned
        )
        logger.info(f"Search found {len(search_result)} results.")
        return search_result

# Singleton instance
qdrant_service = QdrantService()
