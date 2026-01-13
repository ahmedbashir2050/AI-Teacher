from celery import Celery
from app.config import settings

"""
Celery worker configuration and entrypoint.

To run the worker:
celery -A app.core.celery_worker.celery_app worker --loglevel=info
"""

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
)

if __name__ == '__main__':
    celery_app.start()
