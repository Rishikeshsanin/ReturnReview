from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from fastapi import HTTPException
from app.models.database_models import ReturnCase, CaseImage


def get_case_or_404(db: Session, case_id: str) -> ReturnCase:
    stmt = select(ReturnCase).where(ReturnCase.id == case_id).options(
        selectinload(ReturnCase.images).selectinload(CaseImage.inspection),
        selectinload(ReturnCase.reviews),
        selectinload(ReturnCase.decisions),
    )
    case = db.scalar(stmt)
    if not case:
        raise HTTPException(404, "Return case not found")
    return case
