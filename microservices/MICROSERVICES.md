# AI-Teacher Production Microservices Architecture

## 🏗️ Architecture Overview
The system is a production-grade, highly available microservices mesh designed to serve 100k+ concurrent users.

### Core Services:
- **NGINX (Edge Gateway)**: Single public entry point. Handles SSL termination, IP-based rate limiting, security headers, and response caching.
- **API Gateway**: FastAPI-based (v1). Performs JWT validation, Redis-based token blacklist check, RBAC enforcement, per-user rate limiting, and request routing with identity injection (`X-User-Id`, `X-User-Role`).
- **Auth Service**: Manages users, JWT issuance (Access/Refresh), and session revocation.
- **User Service**: Manages academic hierarchy (Faculty, Department, Semester, Course, Book) and user profiles.
- **Chat Service (AI Tutor)**: Core AI logic, multi-stage RAG pipeline orchestration, and pedagogical structured responses. Supports soft-delete for sessions.
- **RAG Service**: PDF ingestion, chunking, embedding generation, and vector retrieval via Qdrant.
- **Exam Service**: Automated exam generation and student attempt tracking.
- **Notification Service**: Async delivery of system events via Celery/Redis.

## 🚦 Scale & Performance Strategy
- **Horizontal Scaling**: Core services (`chat`, `rag`, `exam`) run with 3-5+ replicas. NGINX acts as the primary load balancer.
- **Database Hardening**:
  - **PgBouncer**: Integrated for transaction pooling (supports 10k+ connections) on port 6432.
  - **Read Replicas**: All services support `READ_DATABASE_URL` and `ReadSessionLocal` to offload read traffic.
  - **Migrations**: Automated database migrations via Alembic integrated into the CI/CD pipeline and container entrypoints.
- **Standardized Caching**: Robust Redis caching layer in `core/cache.py` with MD5 key hashing and Pydantic model serialization.
- **Async Mesh**: Offloads heavy tasks (PDF processing, Exam generation, Notifications) to Celery/Redis workers.
- **Vector Isolation**: Qdrant collections use physical sharding (4 shards) and replication (2x). Data is logically partitioned by `faculty_id` and `semester_id`.

## 🔐 Security & Governance
- **Trust Boundary**: Gateway validates JWT and checks revocation status. Downstream services trust injected headers but enforce academic context.
- **RBAC**: Role-Based Access Control (`admin`, `academic`, `student`) enforced at the edge.
- **Audit Logging**: Structured JSON audit logs for all security and business events across all services.
- **Data Isolation**: Strict isolation in vector search and relational queries using academic context filters.
- **Hallucination Guardrails**: Multi-stage groundedness checks in the RAG pipeline to ensure AI responses are based strictly on curriculum context.
- **Hardened Nginx**: CSP headers, XSS protection, HSTS, and frame-ancestors enforced.

## 📈 Observability & Monitoring
- **Distributed Tracing**: OpenTelemetry integrated across all services for request tracing.
- **Structured Logging**: All services use JSON logging with `X-Request-ID` correlation.
- **Prometheus/Grafana**: Full stack monitoring with DNS-based service discovery for scaled replicas.
- **Health Checks**: Standard `/health` and `/metrics` endpoints for orchestration and monitoring.

## 🛠️ CI/CD & DevOps
- **GitHub Actions**: Multi-stage pipeline:
  1. **Lint & Test**: Code quality checks with Ruff and unit testing.
  2. **Migration Check**: Ensures Alembic migrations are in sync with models.
  3. **Security Scan**: Vulnerability scanning with Trivy.
  4. **Build & Push**: Build versioned Docker images.
- **Docker Hardening**: All service containers run as non-root users (`appuser`) with an automated `entrypoint.sh` for database migrations.

## 🚀 Deployment Instructions
1.  **Configure Environment**: Copy `.env.example` to `.env` and fill in secrets (JWT, OpenAI, Redis, DB).
2.  **Infrastructure**: Ensure Redis, PostgreSQL (via PgBouncer), and Qdrant are reachable.
3.  **Start Services**: `docker-compose up -d --scale chat-service=5 --scale rag-service=5`
4.  **Access**: Entry point is `http://localhost:80`.

## 📜 Scaling Assumptions
- **User Load**: Optimized for 100k+ concurrent users via Nginx load balancing and service replication.
- **LLM Latency**: Mitigated via 6h-24h Redis caching of embeddings and common answers.
- **Fault Tolerance**: Retries with exponential backoff implemented in Gateway proxy logic.
- **DB Concurrency**: Managed by PgBouncer and Read Replicas.
