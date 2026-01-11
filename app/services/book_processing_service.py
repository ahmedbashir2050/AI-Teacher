from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pdfminer.high_level import extract_text
from qdrant_client import QdrantClient, models
from app.core.qdrant_db import get_qdrant_client, create_collection_if_not_exists
import uuid
import io

# Load a pre-trained model for generating embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def process_and_store_book(book_id: uuid.UUID, faculty_id: uuid.UUID, semester_id: uuid.UUID, file_content: bytes):
    """
    Processes a PDF file, extracts text, chunks it, generates embeddings,
    and stores them in the Qdrant vector database.
    """
    collection_name = f"faculty_{faculty_id}_semester_{semester_id}"
    create_collection_if_not_exists(collection_name)

    # 1. Extract text from the PDF
    text = extract_text(io.BytesIO(file_content))

    # 2. Chunk the text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)

    # 3. Generate embeddings for each chunk
    embeddings = embedding_model.encode(chunks, convert_to_tensor=True)

    # 4. Store in Qdrant
    qdrant_client = get_qdrant_client()
    points = []
    for i, chunk in enumerate(chunks):
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[i].tolist(),
                payload={
                    "book_id": str(book_id),
                    "text": chunk,
                    "chapter": "Chapter 1", # Placeholder
                    "page_number": i + 1 # Placeholder
                }
            )
        )

    qdrant_client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True
    )

    return collection_name
