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

BOOK_SELECTION_OPERATIONS = Counter(
    "book_selection_operations_total",
    "Total number of book selection operations",
    ["action"] # action=add, remove
)

AVAILABLE_BOOKS_REQUESTS = Counter(
    "available_books_requests_total",
    "Total requests for available books"
)
