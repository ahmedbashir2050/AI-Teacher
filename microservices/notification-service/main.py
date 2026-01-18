from fastapi import FastAPI
from pydantic import BaseModel
from tasks import send_notification_task
from prometheus_fastapi_instrumentator import Instrumentator
from core.observability import setup_logging, setup_tracing, instrument_app

# Setup observability
logger = setup_logging("notification-service")
setup_tracing("notification-service")

app = FastAPI(title="Notification Service", version="1.0.0")
Instrumentator().instrument(app).expose(app)
instrument_app(app, "notification-service")

class Notification(BaseModel):
    user_id: str
    message: str
    type: str # 'email', 'fcm', etc.

@app.post("/notify")
async def send_notification(notification: Notification):
    send_notification_task.delay(
        notification.user_id,
        notification.message,
        notification.type
    )
    return {"status": "queued"}

@app.get("/health")
def health():
    return {"status": "ok"}
