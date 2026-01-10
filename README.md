# AI Teacher Backend

This project is a FastAPI backend for an AI Teacher application. It provides a structured academic hierarchy, per-book chat memory, and admin-only book upload functionality.

## Objective

The primary objective of this backend is to support a robust and scalable AI Teacher application with the following key features:

-   **Per-Book Chat Memory:** Each chat session is tied to a specific user and book, ensuring that conversations are isolated and contextually relevant.
-   **Academic Hierarchy:** The application implements a clear academic structure: College → Department → Semester → Course → Book.
-   **Admin-only Book Upload:** Only admin users are authorized to upload and process books, maintaining control over the curriculum content.
-   **Strict RAG Scoping:** The Retrieval-Augmented Generation (RAG) is strictly scoped to the selected book, preventing the AI from using external knowledge and ensuring that answers are based solely on the provided material.

## Features

-   **Modular Services:** The codebase is organized into modular services for academic structure, chat memory, and book processing.
-   **Pydantic Models:** All API endpoints use Pydantic models for data validation and serialization.
-   **SQLAlchemy ORM:** The application uses SQLAlchemy for database interactions, with models for all entities.
-   **Qdrant Vector Database:** Book chunks and their embeddings are stored in a Qdrant vector database for efficient similarity search.
-   **Role-Based Access Control (RBAC):** The application enforces RBAC, with distinct roles for "admin" and "student" users.

## API Endpoints

### Academic Structure

-   `GET /api/colleges`: Retrieve a list of all colleges.
-   `GET /api/departments/{college_id}`: Retrieve a list of departments for a given college.
-   `GET /api/semesters/{department_id}`: Retrieve a list of semesters for a given department.
-   `GET /api/courses/{semester_id}`: Retrieve a list of courses for a given semester.
-   `GET /api/books/{course_id}`: Retrieve a list of books for a given course.

### Admin

-   `POST /api/admin/upload-book`: Upload a book (PDF) to the system. This endpoint is restricted to admin users.

### Chat

-   `POST /api/chat`: Initiate a chat session with a specific book.

## How to Run

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up the environment variables:**
    -   `DATABASE_URL`: The connection string for your PostgreSQL database.
    -   `QDRANT_URL`: The URL for your Qdrant instance.

4.  **Run the application:**
    ```bash
    uvicorn app.main:app --reload
    ```

The application will be available at `http://localhost:8000`.
