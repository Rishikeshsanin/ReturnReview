from sqlalchemy.orm import Session
from app.models.database_models import AuditEvent


def record_event(db: Session, case_id: str, event_type: str, payload: dict | None = None) -> None:
    db.add(AuditEvent(case_id=case_id, event_type=event_type, payload_json=payload or {}))
