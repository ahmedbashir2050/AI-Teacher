# RAG Ingestion & Retrieval Strategy

This document outlines the strategy for Retrieval-Augmented Generation (RAG) used in the AI Teacher system.

## Ingestion Pipeline

The ingestion pipeline is responsible for processing academic content (Books, Documents) and making it searchable.

### 1. Ingestion Process
- **Trigger**: Library Service triggers ingestion after a book is uploaded to S3.
- **Task**: `tasks.ingest_document_task` (Celery).
- **Steps**:
    1. **Download**: Fetch the PDF from S3.
    2. **Extraction**: Use `pypdf` to extract text from the PDF.
    3. **Chunking**: `RecursiveCharacterTextSplitter` with chunk size 500 and overlap 50.
    4. **Embedding**: Generate vectors using `text-embedding-3-small` (or equivalent).
    5. **Indexing**: Store vectors in Qdrant with comprehensive metadata.

### 2. Metadata & Isolation
To prevent cross-faculty or cross-semester leakage, every point in Qdrant includes:
- `book_id`
- `faculty_id`
- `department_id`
- `semester`

### 3. Retrieval Strategy
Retrieval is strictly scoped based on the student's context.

- **Filters**: Every query sent to Qdrant MUST include a filter for `faculty_id`, `department_id`, and `semester`.
- **Top-k**: Returns the top 5 most relevant chunks.
- **Score Threshold**: A minimum similarity score of 0.7 is required for context to be considered valid.

## Observability

- **Metrics**: `rag_ingestion_seconds` tracks the time taken for the ingestion pipeline.
- **Audit**: Every ingestion completion is logged with chunk counts and book ID.
