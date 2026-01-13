from app.models.db import ChatMessage

def create_teacher_prompt(retrieved_context: list[str], user_question: str, chat_history: list[ChatMessage] = None) -> str:
    """
    Creates the final prompt for the LLM using the mandatory Arabic template.
    """
    context_str = "\n\n---\n\n".join(retrieved_context)

    if chat_history:
        history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in chat_history])
    else:
        history_str = "No history"

    prompt = f"""
أنت مدرس جامعي ذكي.
أجب فقط باستخدام المحتوى المرفق أدناه.
لا تضف أي معلومة من خارج المحتوى.
إذا لم تجد الإجابة داخل المحتوى، قل حرفيًا:
"هذا السؤال خارج المقرر".

المحتوى:
{context_str}

تاريخ المحادثة:
{history_str}

السؤال:
{user_question}
"""
    return prompt.strip()
