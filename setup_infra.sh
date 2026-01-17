# Auth Service
cat <<EOF > microservices/auth-service/requirements.txt
fastapi[all]
uvicorn[standard]
sqlalchemy
psycopg2-binary
pydantic-settings
pydantic[email]
python-jose[cryptography]
passlib[bcrypt]
python-multipart
EOF

# User Service
cat <<EOF > microservices/user-service/requirements.txt
fastapi[all]
uvicorn[standard]
sqlalchemy
psycopg2-binary
pydantic-settings
EOF

# Chat Service
cat <<EOF > microservices/chat-service/requirements.txt
fastapi[all]
uvicorn[standard]
sqlalchemy
psycopg2-binary
pydantic-settings
openai
redis
aioredis
httpx
fastapi-limiter
EOF

# RAG Service
cat <<EOF > microservices/rag-service/requirements.txt
fastapi[all]
uvicorn[standard]
sqlalchemy
psycopg2-binary
pydantic-settings
qdrant-client
openai
pypdf
langchain-text-splitters
tiktoken
langchain-openai
EOF

# Exam Service
cat <<EOF > microservices/exam-service/requirements.txt
fastapi[all]
uvicorn[standard]
sqlalchemy
psycopg2-binary
pydantic-settings
openai
EOF

# Notification Service
cat <<EOF > microservices/notification-service/requirements.txt
fastapi[all]
uvicorn[standard]
pydantic
EOF

# API Gateway
cat <<EOF > microservices/api-gateway/requirements.txt
fastapi[all]
uvicorn[standard]
httpx
python-jose[cryptography]
pydantic-settings
fastapi-limiter
redis
aioredis
EOF

# Base Dockerfile
cat <<EOF > microservices/Dockerfile.base
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Copy Dockerfile to all services
for service in auth-service user-service chat-service rag-service exam-service notification-service api-gateway; do
    cp microservices/Dockerfile.base microservices/$service/Dockerfile
done
