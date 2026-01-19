from prometheus_client import Counter, Histogram

# Metrics for Library Service
BOOK_UPLOAD_LATENCY = Histogram(
    "book_upload_latency_seconds",
    "Latency of book uploads in seconds"
)

BOOK_DOWNLOAD_COUNT = Counter(
    "book_download_total",
    "Total number of book downloads",
    ["faculty_id", "department_id"]
)

RAG_INGESTION_TRIGGER_COUNT = Counter(
    "rag_ingestion_trigger_total",
    "Total number of RAG ingestion tasks triggered"
)
