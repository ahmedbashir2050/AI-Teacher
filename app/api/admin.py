from fastapi import APIRouter, Depends, HTTPException, status
from app.models.responses import MessageResponse
from app.core.security import ADMIN_ACCESS
from app.config import settings
from datetime import datetime, timedelta
from app.repository import user_repository
from app.db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.delete("/admin/purge-chat-history", response_model=MessageResponse)
async def purge_chat_history(current_user: dict = ADMIN_ACCESS):
    """
    Purges chat history older than the configured retention period.
    NOTE: This endpoint is not yet implemented.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="This feature is not yet implemented.")

@router.get("/admin/audit-logs", response_model=MessageResponse)
async def export_audit_logs(current_user: dict = ADMIN_ACCESS):
    """
    Exports audit logs.
    NOTE: This endpoint is not yet implemented.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="This feature is not yet implemented.")

@router.put("/admin/deactivate-user/{user_id}", response_model=MessageResponse)
async def deactivate_user(user_id: int, db: Session = Depends(get_db), current_user: dict = ADMIN_ACCESS):
    """
    Deactivates a user.
    Requires ADMIN access.
    """
    user = user_repository.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.disabled = True
    db.commit()

    return {"message": f"User '{user.username}' has been deactivated."}
