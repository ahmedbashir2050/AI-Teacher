def create_teacher_prompt(retrieved_context: list[str], user_question: str, chat_history: list = None) -> str:
    """
    Creates the final prompt for the LLM using the mandatory Arabic template.
    """
    context_str = "\n\n---\n\n".join(retrieved_context)

    history_str = ""
    if chat_history:
        for msg in chat_history:
            if hasattr(msg, 'role'):
                role = msg.role
                content = msg.content
            else:
                role = msg.get('role')
                content = msg.get('content')
            history_str += f"{role}: {content}\n"
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
