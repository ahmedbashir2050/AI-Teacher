from sqlalchemy.orm import Session
from app.models import chat as chat_models
from app.schemas import chat as chat_schemas
from app.core.qdrant_db import get_qdrant_client, COLLECTION_NAME
from qdrant_client import models
from sentence_transformers import SentenceTransformer
import os
from openai import OpenAI

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_chat_history(db: Session, user_id: str, book_id: int, limit: int = 8):
    return db.query(chat_models.ChatHistory).filter(
        chat_models.ChatHistory.user_id == user_id,
        chat_models.ChatHistory.book_id == book_id
    ).order_by(chat_models.ChatHistory.timestamp.desc()).limit(limit).all()

def save_chat_message(db: Session, user_id: str, message: chat_schemas.ChatMessageCreate):
    db_message = chat_models.ChatHistory(
        user_id=user_id,
        **message.model_dump()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def search_book_chunks(book_id: int, query: str, top_k: int = 3):
    qdrant_client = get_qdrant_client()
    query_embedding = embedding_model.encode(query, convert_to_tensor=True).tolist()

    search_result = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="book_id",
                    match=models.MatchValue(value=book_id),
                )
            ]
        ),
        limit=top_k
    )
    return [hit.payload['text'] for hit in search_result]

def generate_response(chat_history: list, retrieved_chunks: list, user_question: str) -> str:
    """
    Generates a response using the provided chat history, retrieved chunks, and user question.
    """
    if not retrieved_chunks:
        return "هذا السؤال خارج المقرر"

    # Build the prompt
    history_str = "\n".join([f"{msg.role}: {msg.message}" for msg in reversed(chat_history)])
    chunks_str = "\n".join(retrieved_chunks)

    prompt = f"""
أنت مدرس جامعي ذكي.
هذه محادثة مستمرة مع طالب حول كتاب محدد.
أجب فقط باستخدام محتوى هذا الكتاب.
لا تستخدم أي معرفة خارجية.

سياق المحادثة:
{history_str}

محتوى الكتاب:
{chunks_str}

السؤال:
{user_question}

إذا لم تجد الإجابة، قل حرفيًا:
"هذا السؤال خارج المقرر"
    """

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful university instructor."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
