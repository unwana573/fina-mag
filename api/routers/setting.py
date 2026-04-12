from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.models import User
from api.services.notification_service import NotificationService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/settings", tags=["Settings"])


class NotificationUpdate(BaseModel):
    budget_alerts: Optional[bool] = None
    transaction_alerts: Optional[bool] = None
    weekly_digest: Optional[bool] = None


@router.get("/notifications")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationService(db).get_or_create(current_user.id)


@router.put("/notifications")
def update_notifications(
    body: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return NotificationService(db).update(current_user.id, data)