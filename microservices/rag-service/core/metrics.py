from prometheus_client import Counter, Histogram

RETRIEVER_REFRESH_LATENCY = Histogram(
    "retriever_refresh_latency_seconds",
    "Time taken to refresh retriever caches"
)

RETRIEVER_REFRESH_TOTAL = Counter(
    "retriever_refresh_total",
    "Total number of retriever refresh operations"
)
