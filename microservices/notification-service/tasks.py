from core.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.send_notification_task", bind=True, max_retries=3)
def send_notification_task(self, user_id: str, message: str, notification_type: str):
    try:
        # Logic to send notification (e.g., via Email, FCM, etc.)
        logger.info(f"[NOTIFICATION] Sending {notification_type} to {user_id}: {message}")
        # In a real scenario, you'd call an external API here (SendGrid, Firebase, etc.)
        return {"status": "sent", "user_id": user_id}
    except Exception as exc:
        logger.error(f"Error sending notification: {exc}")
        self.retry(exc=exc, countdown=60)
