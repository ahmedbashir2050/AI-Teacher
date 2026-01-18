# AI-Teacher Production Microservices Architecture

## 🏗️ Architecture Overview
The system is a production-grade, highly available microservices mesh designed to serve 100k+ concurrent users.

### Core Services:
- **NGINX (Edge Gateway)**: Single public entry point. Handles SSL, IP-based rate limiting, security headers, and response caching.
- **API Gateway**: FastAPI-based. Performs JWT validation, per-user rate limiting (Redis), and routes requests with identity injection.
- **Auth Service**: Manages users, JWT issuance, and authentication.
- **User Service**: Manages academic hierarchy (Faculty, Department, Semester, Course, Book) and user profiles.
- **Chat Service (AI Tutor)**: Core AI logic, RAG pipeline orchestration, and pedagogical structured responses.
- **RAG Service**: PDF ingestion, chunking, embedding, and vector retrieval.
- **Exam Service**: Automated exam generation and student attempt tracking.
- **Notification Service**: Async delivery of system events via Celery.

## 🚦 Scale & Performance Strategy
- **Horizontal Scaling**: Core services (`chat`, `rag`, `exam`) run with 3-5+ replicas.
- **Database Hardening**:
  - **PgBouncer**: Integrated for transaction pooling (supports 10k+ connections).
  - **Read Replicas**: All services support `READ_DATABASE_URL` to offload load from the primary writer.
- **Standardized Caching**: Standardized Redis caching layer in `core/cache.py` used by all services for expensive DB/LLM calls.
- **Async Mesh**: Offloads heavy tasks (PDF processing, Exam generation) to Celery/Redis workers.
- **Vector Isolation**: Qdrant collections use physical sharding (4 shards) and replication (2x). Data is logically partitioned by `faculty_id`, `department_id`, and `semester_id`.

## 🔐 Security & Governance
- **Trust Boundary**: Gateway validates JWT and injects `X-User-Id`, `X-User-Role`. Downstream services enforce these headers.
- **Data Isolation**: Strict multi-tenant-like isolation in vector search and relational queries using academic context filters.
- **Hardened Nginx**: CSP headers, XSS protection, and frame-ancestors enforced at the edge.

## 📈 Observability & Monitoring
- **Distributed Tracing**: OpenTelemetry integrated across all services for request tracing.
- **Structured Logging**: All services use JSON logging with `X-Request-ID` correlation.
- **Prometheus/Grafana**: Full stack monitoring with DNS-based service discovery for scaled replicas.
- **Health Checks**: Standard `/health` endpoints for orchestration readiness.

## 🛠️ CI/CD & DevOps
- **GitHub Actions**: Automated pipeline for building and pushing tagged Docker images.
- **Docker Best Practices**: Optimized `.dockerignore`, image versioning, and non-root execution (recommended).

## 🚀 Deployment Instructions
1.  **Configure Environment**: Copy `.env.example` to `.env` and fill in secrets (JWT, OpenAI).
2.  **Infrastructure**: Ensure Redis and PostgreSQL are reachable.
3.  **Start Services**: `docker-compose up -d --scale chat-service=5 --scale rag-service=5`
4.  **Access**: Entry point is `http://localhost:80`.

## 📜 Scaling Assumptions
- **User Load**: Optimized for 100k+ users via Nginx load balancing and service replication.
- **LLM Latency**: Mitigated via 6h-24h Redis caching of embeddings and common answers.
- **DB Concurrency**: Managed by PgBouncer and Read Replicas.
