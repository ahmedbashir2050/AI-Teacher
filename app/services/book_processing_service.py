from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pdfminer.high_level import extract_text
from qdrant_client import QdrantClient, models
from app.core.qdrant_db import get_qdrant_client, COLLECTION_NAME
import uuid
import io

# Load a pre-trained model for generating embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def process_and_store_book(book_id: int, file_content: bytes):
    """
    Processes a PDF file, extracts text, chunks it, generates embeddings,
    and stores them in the Qdrant vector database.
    """
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
                    "book_id": book_id,
                    "text": chunk,
                    # You could add more metadata here like chapter, page number if available
                }
            )
        )

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True
    )

    return {"message": f"Book {book_id} processed and stored successfully."}
