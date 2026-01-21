from fastapi import APIRouter, Depends, Header, Request, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from core.services import user_service
from core.audit import log_audit
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

router = APIRouter(prefix="/admin")

class TeacherAssignmentRequest(BaseModel):
    faculty_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    semester_id: Optional[UUID] = None

@router.post("/teachers/{teacher_id}/assign")
def assign_teacher(
    request: Request,
    teacher_id: UUID,
    assignment: TeacherAssignmentRequest,
    db: Session = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header(...)
):
    if x_user_role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")

    teacher = user_service.get_user_by_id(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if teacher.role != "teacher":
        raise HTTPException(status_code=400, detail="User is not a teacher")

    update_data = assignment.model_dump(exclude_unset=True)
    updated_teacher = user_service.update_profile(db, teacher_id, update_data)

    log_audit(
        user_id=x_user_id,
        action="TEACHER_ASSIGNED",
        resource="user",
        resource_id=str(teacher_id),
        status="success",
        metadata=update_data,
        request_id=getattr(request.state, "request_id", None)
    )
    return updated_teacher
