# Library & Book Upload System

This document describes the Library and Book Upload system integrated with the AI Teacher microservices architecture.

## Overview

The Library system provides a production-grade pipeline for managing academic books, ensuring secure storage, student-level access control, and automated RAG (Retrieval-Augmented Generation) ingestion.

## Domain Model

- **Faculty**: Academic faculties (e.g., Engineering, Medicine).
- **Department**: Departments within a faculty (e.g., Computer Science, Electrical Engineering).
- **Book**: Academic books belonging to a specific Faculty, Department, and Semester.
  - Attributes: UUID, title, language, file_key, file_hash, uploaded_by, is_active.

## API Endpoints

### Admin Endpoints (RBAC: admin, super_admin)

- `POST /api/v1/admin/books`: Upload a new book (multipart/form-data).
  - Validates file type (PDF) and size (50MB).
  - Performs hash-based duplicate detection.
  - Triggers RAG ingestion automatically.
- `PUT /api/v1/admin/books/{id}`: Update book metadata.
- `DELETE /api/v1/admin/books/{id}`: Soft delete a book.
- `GET /api/v1/admin/books`: List books with pagination and filters (faculty, department, semester).

### Student Endpoints

- `GET /api/v1/books/{id}/download`: Securely download a book.
  - Validates student eligibility based on their Faculty, Department, and Semester.
  - Generates a short-lived (15 min) signed URL.

## Secure Storage

Books are stored in S3-compatible storage (AWS S3 or MinIO) using a deterministic path:
`/books/{faculty_name}/{department_name}/{semester}/{book_id}.pdf`

Raw storage URLs are never exposed to the public.

## RAG Ingestion Flow

1. Admin uploads a book.
2. Library Service stores the file in S3 and saves metadata in the database.
3. Library Service triggers a Celery task in the RAG Service.
4. RAG Service downloads the file from S3, extracts text, chunks it, generates embeddings, and stores them in Qdrant.
5. Metadata in Qdrant is scoped by `book_id`, `faculty_id`, `department_id`, and `semester` to ensure isolation.
