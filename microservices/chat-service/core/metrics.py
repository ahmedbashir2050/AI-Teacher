from prometheus_client import Counter, Histogram

# AI Teacher Performance Metrics
ANSWERS_TOTAL = Counter(
    "ai_teacher_answers_total",
    "Total number of AI-generated answers",
    ["faculty_id", "status"]
)

HALLUCINATIONS_BLOCKED_TOTAL = Counter(
    "ai_teacher_hallucinations_blocked_total",
    "Total number of hallucinations blocked by guardrails"
)

SIMILARITY_SCORE = Histogram(
    "ai_teacher_rag_similarity_score",
    "RAG similarity scores for retrieved chunks",
    buckets=[0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]
)

VERIFIED_ANSWERS_TOTAL = Counter(
    "ai_teacher_verified_answers_total",
    "Total number of answers verified by admins",
    ["is_verified"]
)

STUDENT_FEEDBACK_TOTAL = Counter(
    "ai_teacher_student_feedback_total",
    "Total student feedback on AI answers",
    ["is_correct"]
)

ANSWER_LATENCY = Histogram(
    "ai_teacher_answer_latency_seconds",
    "Time taken to generate an AI answer",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0]
)
