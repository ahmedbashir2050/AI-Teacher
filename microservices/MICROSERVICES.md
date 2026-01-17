# AI-Teacher Microservices Architecture

This document describes the production-grade microservices architecture for the AI-Teacher platform.

## 🏗️ Directory Structure
```
microservices/
├── api-gateway/          # Thin proxy, JWT validation, Global rate limiting
├── auth-service/         # User Auth, JWT Issuance, PostgreSQL (auth_db)
├── user-service/         # Profiles, Academics Hierarchy, PostgreSQL (user_db)
├── chat-service/         # Sessions, Messages, LLM Integration, PostgreSQL (chat_db)
├── rag-service/          # PDF Ingestion, Vector Search, Qdrant + PostgreSQL (rag_db)
├── exam-service/         # Exam Generation/Grading, PostgreSQL (exam_db)
├── notification-service/ # Async Notifications (Skeleton)
└── docker-compose.yml    # Local orchestration
```

## 🔐 Security & Identity
- **Auth Service** is the only one that issues JWTs.
- **API Gateway** validates JWTs for all protected routes.
- **Gateway** extracts `sub` (User ID) and `role` from JWT and passes them as `X-User-Id` and `X-User-Role` headers to downstream services.
- **Trust Boundary**: Downstream services enforce that identity headers are present and originate from the internal network.

## 🆔 Request Correlation
- **X-Request-ID** is generated/forwarded by the Gateway and propagated across all service-to-service calls.
- This allows end-to-end tracing of a single request across the entire microservices mesh.

## 🚦 Rate Limiting
- **Global**: Enforced at the API Gateway (e.g., 100 req/min).
- **Per-User**: Enforced in `chat-service` (20 req/min/user) using Redis and `X-User-Id` as the identifier.

## 📡 API Contracts (Key Endpoints)

### Gateway (8080)
- `POST /api/auth/register` -> `auth-service:8000/auth/register`
- `POST /api/auth/login` -> `auth-service:8000/auth/login`
- `POST /api/chat/chat` -> `chat-service:8000/chat`
- `POST /api/rag/ingest` -> `rag-service:8000/ingest`
- `POST /api/rag/search` -> `rag-service:8000/search`
- `POST /api/exams/generate` -> `exam-service:8000/generate`

## 🛠️ Local Development
1. `cd microservices`
2. `cp .env.example .env` (Update with your keys)
3. `docker-compose up --build`

## 🚀 National Scale Readiness
- **Async I/O**: All LLM and inter-service calls use `AsyncOpenAI` and `httpx.AsyncClient` to maximize concurrency.
- **Fault Tolerance**: Bounded retries (tenacity) and explicit timeouts protect against cascading failures.
- **Statelessness**: All containers are stateless and safe for horizontal scaling (K8s ready).
