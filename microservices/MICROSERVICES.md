# Service Registry & Local Development

This directory contains the source code for the AI-Teacher microservices. For the full system architecture, see [ARCHITECTURE.md](../ARCHITECTURE.md).

## 🚀 Quick Start (Docker Compose)

To start the entire stack locally:

```bash
cd microservices
docker-compose up -d
```

## 📦 Services

- **api-gateway**: Entry point with RBAC and Rate Limiting.
- **auth-service**: Identity provider.
- **user-service**: Academic data and profiles.
- **chat-service**: AI Tutor core logic.
- **rag-service**: Document search and ingestion.
- **exam-service**: AI exam generation.
- **notification-service**: Async alerts (Email/FCM).

## 🧪 Testing

Run tests across all services:
```bash
pytest .
```

## 🔄 Migrations

Each service manages its own migrations via Alembic.
```bash
cd auth-service
alembic upgrade head
```
