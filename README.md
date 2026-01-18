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

This project is a production-grade microservices mesh designed for high availability and scalability.

### Architecture Highlights
- **Microservices Mesh**: 7 specialized services (Auth, User, Chat, RAG, Exam, Notification, Gateway).
- **Production Infrastructure**: NGINX Edge, PgBouncer pooling, Redis caching, Qdrant vector database.
- **Observability**: Full OpenTelemetry, Prometheus, and Grafana integration.
- **Security**: Hardened NGINX, JWT with revocation, RBAC, and structured Audit Logging.
- **CI/CD**: Automated multi-stage GitHub Actions pipeline with security scanning.

For detailed architecture information, see [microservices/MICROSERVICES.md](microservices/MICROSERVICES.md).

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
    cd microservices
    docker-compose up --build
    ```
    The production gateway will be available at `http://localhost:80`.

## 📚 API Usage (via Gateway)

The entry point for all API calls is the NGINX Edge Gateway at `http://localhost:80`. All academic endpoints require a valid JWT in the `Authorization` header.

### 1. Ingest a Document (Admin/Academic)
Upload a curriculum PDF to populate the vector database.

*   **Endpoint:** `POST /api/rag/ingest?collection_name=math&faculty_id=F1&semester_id=S1`
*   **Body:** `multipart/form-data` with a PDF file.

### 2. Chat with the AI Teacher
Ask a question based on the curriculum. Requires academic context.

*   **Endpoint:** `POST /api/chat/chat`
*   **Body (JSON):**
    ```json
    {
      "message": "Explain the concept of derivatives.",
      "collection_name": "math",
      "faculty_id": "F1",
      "semester_id": "S1"
    }
    ```

### 3. Generate an Exam
Create a university-style exam with MCQ and Theory questions.

*   **Endpoint:** `POST /api/exams/generate`
*   **Body (JSON):**
    ```json
    {
      "course_id": "MATH101",
      "collection_name": "math",
      "mcq_count": 5,
      "theory_count": 2
    }
    ```

### 4. User Profiles
Update your academic context to get personalized tutoring.

*   **Endpoint:** `PUT /api/users/me`
*   **Body (JSON):**
    ```json
    {
      "full_name": "Sudanese Student",
      "faculty_id": "F1",
      "department_id": "D1",
      "semester_id": "S1"
    }
    ```
