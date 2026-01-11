from google.cloud import firestore
import datetime
import uuid
import os

# Use a mock client for testing if the emulator is not running
if os.environ.get("FIRESTORE_EMULATOR_HOST"):
    db = firestore.Client()
else:
    from unittest.mock import MagicMock
    db = MagicMock()


def get_last_messages(user_id: str, book_id: uuid.UUID, limit: int = 6):
    """
    Retrieves the last N messages from a chat session.
    """
    chat_ref = db.collection("users").document(user_id).collection("chats").where("bookId", "==", str(book_id)).limit(1)
    chat_docs = list(chat_ref.stream())

    if not chat_docs:
        return []

    chat_id = chat_docs[0].id
    messages_ref = db.collection("users").document(user_id).collection("chats").document(chat_id).collection("messages").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    messages = [doc.to_dict() for doc in messages_ref.stream()]
    return messages

def save_message(user_id: str, book_id: uuid.UUID, role: str, content: str):
    """
    Saves a message to a chat session.
    """
    chat_ref = db.collection("users").document(user_id).collection("chats").where("bookId", "==", str(book_id)).limit(1)
    chat_docs = list(chat_ref.stream())

    if chat_docs:
        chat_id = chat_docs[0].id
    else:
        chat_id = str(uuid.uuid4())
        db.collection("users").document(user_id).collection("chats").document(chat_id).set({
            "bookId": str(book_id),
            "lastMessage": content,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })

    message_id = str(uuid.uuid4())
    db.collection("users").document(user_id).collection("chats").document(chat_id).collection("messages").document(message_id).set({
        "role": role,
        "content": content,
        "timestamp": firestore.SERVER_TIMESTAMP
    })
