#!/bin/bash
set -e

# Run migrations if alembic is configured
if [ -f "alembic.ini" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Start service
echo "Starting service..."
exec "$@"
