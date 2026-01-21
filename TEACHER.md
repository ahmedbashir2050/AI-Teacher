# Teacher Role & Panel Documentation

This document describes the Teacher Role implementation and the Teacher Panel backend functionality.

## 🎯 Objective
Enable teachers to manage and review AI-generated content and monitor student performance without full administrative privileges. Teachers are restricted to the faculty they are assigned to.

## 🔑 Key Features
1. **Review AI Answers**
   - Access AI-generated answers from students in their faculty.
   - Approve or reject answers.
   - Add teacher comments for pedagogical guidance.
2. **Curriculum Management**
   - View, upload, and update books/materials for their faculty.
   - Restricted from modifying other faculties' content.
3. **Student Performance Monitoring**
   - Track aggregate student progress in exams.
   - View AI Confidence Scores (RAG similarity scores) for student queries.

## 🛠️ Implementation Details

### Data Model Updates
In `chat-service`, the `AnswerAuditLog` model now includes:
- `verified_by_teacher`: Boolean indicating teacher review status.
- `teacher_comment`: Text field for teacher feedback.
- `rag_confidence_score`: Float representing the similarity score from the RAG pipeline.

### RBAC & Security
- **API Gateway**: Enforces the `teacher` role and injects the `X-User-Faculty` header into downstream requests.
- **Service Level**: Downstream services (Chat, Library, Exam) check the `X-User-Role` and `X-User-Faculty` to ensure teachers only access data within their scope.

### New API Endpoints

#### Public Gateway Endpoints (V1)
| Endpoint | Method | Description | Role |
| :--- | :--- | :--- | :--- |
| `/api/v1/answers/{id}/verify` | `POST` | Verify an AI answer | Teacher, Admin |
| `/api/v1/answers/{id}/feedback` | `POST` | Provide feedback on an AI answer | Teacher, Admin |
| `/api/v1/curriculum/{id}/approve` | `POST` | Approve/Reject course material | Teacher, Admin |
| `/api/v1/students/{id}/ai-confidence` | `GET` | Get a student's average AI confidence | Teacher, Admin |
| `/api/v1/courses/{id}/progress` | `GET` | Get course-wide student progress | Teacher, Admin |
| `/api/v1/teachers/{id}/assign` | `POST` | Assign teacher to faculty/dept | Admin |

#### Service Internal Endpoints

**Chat Service**
| Endpoint | Method | Description | Role |
| :--- | :--- | :--- | :--- |
| `/teacher/answers` | `GET` | Fetch answers for review (faculty scoped) | Teacher, Admin |
| `/teacher/answers/{id}/verify` | `POST` | Approve/Reject an answer with comments | Teacher, Admin |
| `/teacher/students/{id}/ai-confidence` | `GET` | Get AI confidence for a student | Teacher, Admin |
| `/teacher/performance` | `GET` | Get aggregate AI performance stats | Teacher, Admin |

**Exam Service**
| Endpoint | Method | Description | Role |
| :--- | :--- | :--- | :--- |
| `/teacher/performance` | `GET` | Get aggregate exam stats | Teacher, Admin |
| `/teacher/courses/{id}/progress` | `GET` | Get student progress for a course | Teacher, Admin |

**Library Service**
| Endpoint | Method | Description | Role |
| :--- | :--- | :--- | :--- |
| `/admin/books` | `POST/PUT/DELETE` | Manage books (faculty restricted) | Teacher, Admin |
| `/admin/curriculum/{id}/approve` | `POST` | Approve curriculum material | Teacher, Admin |

## 🧪 RBAC Rules
1. **Faculty Isolation**: Teachers can ONLY access data (answers, exams, books) where the `faculty_id` matches their own `X-User-Faculty-Id`.
2. **Action Restrictions**:
   - Teachers CAN upload/delete books in their faculty.
   - Teachers CANNOT create new faculties or departments (Admin only).
   - Teachers CAN verify student answers.
   - Teachers CAN view performance statistics.

## 📡 API Examples

### Fetch Answers for Review
**Request**: `GET /api/v1/teacher/chat/answers`
**Headers**: `Authorization: Bearer <token>`, `X-User-Faculty-Id: <uuid>`

**Response**:
```json
[
  {
    "id": "uuid-1",
    "user_id": "student-uuid",
    "question_text": "What is the capital of France?",
    "ai_answer": "The capital is Paris.",
    "rag_confidence_score": 0.98,
    "verified_by_teacher": false,
    "teacher_comment": null,
    "is_correct": true
  }
]
```

### Verify Answer
**Request**: `POST /api/v1/answers/uuid-1/verify`
**Body**:
```json
{
  "verified": true,
  "comment": "Perfect answer!",
  "custom_tags": ["high-quality", "accurate"]
}
```

### Course Progress retrieval
**Request**: `GET /api/v1/courses/physics-101/progress`
**Response**:
```json
[
  {
    "student_id": "uuid-student-1",
    "avg_score": 85.5,
    "exams_taken": 3
  }
]
```

## 📊 Audit Logging
All teacher actions are logged in the structured audit trail with `request_id` for full traceability.
- **Action**: `teacher_verify`, `BOOK_UPLOADED`, `BOOK_UPDATED`, `BOOK_DELETED`.
- **Metadata**: Includes verification status, comments, tags, and book details.

## 🔄 Sequence: Teacher Review Flow
```mermaid
sequenceDiagram
    participant T as Teacher
    participant G as API Gateway
    participant C as Chat Service
    participant DB as Chat DB

    T->>G: GET /api/v1/teacher/chat/answers
    G->>C: GET /teacher/answers (X-User-Faculty=Law)
    C->>DB: Query AnswerAuditLog JOIN ChatSession WHERE faculty=Law
    DB-->>C: List of Answers
    C-->>G: Answers JSON
    G-->>T: Answers JSON

    T->>G: POST /api/v1/teacher/chat/verify/{id} {verified: true, comment: "Correct!"}
    G->>C: POST /teacher/verify/{id}
    C->>DB: Update AnswerAuditLog
    C->>C: Log Audit Event
    C-->>G: Success
    G-->>T: Success
```
