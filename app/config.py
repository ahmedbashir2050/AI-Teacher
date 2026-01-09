import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_key = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
