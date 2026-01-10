<<<<<<< Updated upstream
# AI Teacher – Curriculum-Based AI Teaching System (RAG-powered)

## 🎯 Project Overview

AI Teacher is a sophisticated, backend system designed to function as an AI-powered academic tutor. Its core purpose is to answer questions, provide summaries, and generate educational materials like flashcards and exams based *exclusively* on a provided curriculum (e.g., a university textbook).

**🚨 Important:** This is an educational academic system, not a general chatbot. All answers are generated strictly from the curriculum content. The system will not use any external knowledge and is designed to prevent hallucinations. If a question cannot be answered from the provided text, it will respond with: **"هذا السؤال خارج المقرر"** (This question is outside the curriculum).

## 🧠 Core Architecture: Retrieval-Augmented Generation (RAG)

This project is built on a Retrieval-Augmented Generation (RAG) pipeline to ensure all responses are grounded in the curriculum.

The process is as follows:
1.  **Load & Chunk**: The curriculum (PDF document) is loaded and broken down into smaller, manageable text chunks.
2.  **Embed & Store**: Each chunk is converted into a numerical representation (embedding) using an AI model and stored in a specialized **Qdrant** vector database.
3.  **Retrieve**: When a user asks a question, the question is also converted into an embedding. The system then searches the Qdrant database to find the most relevant text chunks from the curriculum.
4.  **Prompt & Generate**: The retrieved chunks are injected into a carefully crafted prompt, along with the user's original question. This entire package is sent to a Large Language Model (LLM) like OpenAI's GPT-4o, which generates a final answer based *only* on the provided context.

This architecture ensures accuracy and prevents the model from using its general knowledge, adhering strictly to the source material.

## 🐳 Setup and Installation

This project is fully containerized using Docker, making setup straightforward.

### Prerequisites
*   Docker and Docker Compose installed.
*   An OpenAI API key.

### Instructions
1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd ai-teacher
    ```

2.  **Create an environment file:**
    Create a `.env` file in the project root and add your OpenAI API key:
    ```
    OPENAI_API_KEY=your_openai_api_key_here
    ```

3.  **Run the application:**
    ```bash
    docker-compose up --build
    ```
    This command will build the FastAPI container, pull the Qdrant image, and start both services. The API will be available at `http://localhost:8000`.

## 📚 API Usage

You can interact with the API through its documentation at `http://localhost:8000/docs` or by sending requests directly.

### 1. Ingest a Document
First, you must upload a curriculum PDF to populate the vector database.

*   **Endpoint:** `POST /api/ingest`
*   **Body:** `multipart/form-data` with a PDF file.

**Example (`curl`):**
```bash
curl -X POST "http://localhost:8000/api/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/sample_book.pdf"
```

### 2. Chat with the AI Teacher
Ask a question based on the ingested curriculum.

*   **Endpoint:** `POST /api/chat`
*   **Body (JSON):**
    ```json
    {
      "question": "What is the core concept of chapter one?"
    }
    ```

### 3. Summarize a Chapter
Get a summary of a specific topic.

*   **Endpoint:** `POST /api/summarize`
*   **Body (JSON):**
    ```json
    {
      "chapter": "Introduction to Microeconomics",
      "style": "bullet"
    }
    ```
    *   `style` can be `simple`, `exam`, or `bullet`.

### 4. Generate Flashcards
Create question-answer flashcards for studying.

*   **Endpoint:** `POST /api/flashcards`
*   **Body (JSON):**
    ```json
    {
      "chapter": "The Laws of Thermodynamics",
      "count": 5
    }
    ```

### 5. Generate an Exam
Create a university-style exam.

*   **Endpoint:** `POST /api/exam`
*   **Body (JSON):**
    ```json
    {
      "chapter": "Cellular Biology",
      "mcq": 5,
      "theory": 2
    }
    ```
=======
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
>>>>>>> Stashed changes
