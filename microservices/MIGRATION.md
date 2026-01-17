# Monolith to Microservices Migration Plan

## Phase 1: Infrastructure Setup (COMPLETED)
- Containerize all services.
- Set up independent databases.
- Implement API Gateway.

## Phase 2: Data Migration
1. **Users**: Extract from monolith DB to `auth_db`.
2. **Academic Metadata**: Extract from monolith DB to `user_db`.
3. **Chat History**: Extract from monolith DB to `chat_db`.
4. **Vector Data**: Re-ingest documents into `rag-service` (Qdrant) or migrate existing collections.

## Phase 3: Incremental Routing
1. Update Flutter app to point to the new Gateway URL (Port 8080).
2. Start by routing `/api/auth` to `auth-service`.
3. Route `/api/chat` to `chat-service` (pointing to the same Qdrant if possible).
4. Gradually move other endpoints.

## Phase 4: Observability & Hardening
1. Add Prometheus metrics.
2. Add Jaeger/Tempo for distributed tracing.
3. Implement circuit breakers for inter-service calls (e.g., chat -> rag).
