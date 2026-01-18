# AI-Teacher Production Microservices Architecture

## 🏗️ Architecture Overview
The system is transformed into a production-grade, highly available microservices mesh.

### Components:
1.  **NGINX (Edge Gateway)**: Single public entry point. Handles SSL termination, IP-based rate limiting, and static/response caching.
2.  **API Gateway (Auth & Routing)**: FastAPI-based internal gateway. Performs JWT validation, per-user rate limiting, and routes requests to downstream services with identity headers (`X-User-Id`, `X-User-Role`).
3.  **Microservices**: Replicated services (rag, chat, exam, etc.) handling core business logic.
4.  **Celery Workers**: Asynchronous task processors for heavy operations (Exam generation, PDF ingestion).
5.  **Redis**: Multi-purpose layer for caching, rate limiting, and message brokering.
6.  **PgBouncer**: Connection pooler for PostgreSQL to handle thousands of concurrent DB connections.
7.  **Qdrant**: Scaled vector database with physical sharding and replication.
8.  **Monitoring Stack**: Prometheus and Grafana for full observability.

## 🚦 Scale Strategy (100k+ Users)
- **Horizontal Scaling**: All services are stateless and run with multiple replicas.
- **Async Processing**: Long-running AI tasks are offloaded to workers, returning a `task_id` to the client.
- **Connection Pooling**: PgBouncer prevents database connection exhaustion.
- **Caching**: Multi-level caching (NGINX edge, Redis application-level, Redis LLM-level).
- **Qdrant Sharding**: Collections are sharded across nodes to handle massive vector searches.

## 🔐 Security Hardening
- **Zero Trust Internal Network**: Only NGINX is exposed. All other services communicate over a private network.
- **Centralized Auth**: JWT validation is strictly enforced at the API Gateway.
- **Identity Propagation**: Identity headers are injected by the Gateway and trusted by downstream services.

## 📈 Observability
- **Metrics**: `/metrics` endpoints on all services (Prometheus format).
- **Logging**: Centralized logs with `X-Request-ID` correlation.
- **Dashboards**: Grafana dashboards for system health and performance.

## 🚀 Deployment
1.  Set environment variables in `.env`.
2.  Run `docker-compose up --build -d`.
3.  Access the system via NGINX on port 80.
4.  Monitor via Grafana on port 3000.

## ⚠️ Breaking Changes
- **Async Operations**: `/api/exams/generate` and `/api/rag/ingest` now return a `task_id` and status `accepted`. Clients should poll or wait for notifications.
