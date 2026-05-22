from sqlalchemy.orm import Session
from api.models import AuditLog

def log(
    db: Session,
    action: str,
    user_id: int = None,
    entity: str = None,
    entity_id: int = None,
    detail: str = None,
):
    """
    Write an immutable audit log entry.

    Usage:
        log(db, action="user.login", user_id=1)
        log(db, action="transaction.created", user_id=1, entity="transaction", entity_id=5)
        log(db, action="user.password_changed", user_id=1)
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(entry)
    db.commit()