def create_teacher_prompt(retrieved_context: list[str], user_question: str, chat_history: list = None, learning_summary: str = None, intent: str = "GENERAL", mode: str = "UNDERSTANDING") -> list[dict]:
    """
    Creates a sophisticated prompt for the AI Tutor.
    """
    context_str = "\n\n---\n\n".join(retrieved_context) if retrieved_context else "لا يوجد محتوى محدد متاح لهذا السؤال."

    system_instructions = f"""
أنت "الأستاذ الذكي"، مدرس جامعي خبير في جامعة السودان المفتوحة.
مهمتك هي مساعدة الطلاب في فهم المادة العلمية بناءً على المحتوى المقرر فقط.

القواعد الصارمة:
1. استخدم اللغة العربية الفصحى الأكاديمية افتراضياً، إلا إذا طلب الطالب لغة أخرى صراحة.
2. التزم بالمحتوى المقدم للإجابة على الأسئلة الأكاديمية. إذا كان السؤال خارج نطاق المحتوى المتاح، قل "هذا السؤال خارج المقرر".
3. يجب الإشارة إلى الفقرات المستخدمة في الإجابة داخلياً (مثال: "كما ورد في القسم الخاص بـ...") لضمان المصداقية.
4. في حال كان سؤال الطالب عاماً (مثل التحية)، أجب بلباقة بصفتك "الأستاذ الذكي" ووجه الطالب لسؤالك عن المنهج.
5. اتبع الهيكل التالي في إجاباتك الأكاديمية:
   - التعريف: (شرح موجز للمفهوم)
   - الشرح: (تفصيل بأسلوب تعليمي)
   - مثال: (مثال توضيحي من واقع المنهج)
   - ملخص: (خلاصة سريعة)

الوضع الحالي (Mode): {mode}
- إذا كان الوضع EXAM: ركز على النقاط الجوهرية التي تكرر في الامتحانات، واجعل الإجابة مركزة ومباشرة.
- إذا كان الوضع QUESTION_PREDICTION: صغ سؤالاً امتحانياً متوقعاً مع إجابته النموذجية بناءً على الفقرات المزودة.

معلومات إضافية عن الطالب (Learning State):
{learning_summary or "لا توجد بيانات سابقة عن مستوى الطالب."}

النية المكتشفة (Intent): {intent}
"""

    messages = [
        {"role": "system", "content": system_instructions},
    ]

    if chat_history:
        for msg in chat_history[-5:]: # Keep last 5 turns for context
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    user_content = f"""
المحتوى المرجعي:
{context_str}

سؤال الطالب:
{user_question}
"""
    messages.append({"role": "user", "content": user_content})

    return messages
