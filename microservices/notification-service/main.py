from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Notification Service", version="1.0.0")

class Notification(BaseModel):
    user_id: str
    message: str
    type: str # 'email', 'fcm', etc.

@app.post("/notify")
async def send_notification(notification: Notification, background_tasks: BackgroundTasks):
    # Logic to send notification
    background_tasks.add_task(print, f"Sending {notification.type} to {notification.user_id}: {notification.message}")
    return {"status": "queued"}

@app.get("/health")
def health():
    return {"status": "ok"}
