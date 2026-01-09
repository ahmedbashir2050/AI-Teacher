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
