from fastapi import HTTPException
from app.models.database_models import CaseStatus

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    CaseStatus.DRAFT.value: {CaseStatus.READY_FOR_INSPECTION.value},
    CaseStatus.READY_FOR_INSPECTION.value: {CaseStatus.PROCESSING_CV.value},
    CaseStatus.PROCESSING_CV.value: {CaseStatus.CV_COMPLETE.value, CaseStatus.READY_FOR_INSPECTION.value, CaseStatus.ERROR.value},
    CaseStatus.CV_COMPLETE.value: {CaseStatus.GENERATING_REVIEW.value, CaseStatus.PROCESSING_CV.value},
    CaseStatus.GENERATING_REVIEW.value: {CaseStatus.READY_FOR_REVIEW.value, CaseStatus.CV_COMPLETE.value, CaseStatus.ERROR.value},
    CaseStatus.READY_FOR_REVIEW.value: {
        CaseStatus.APPROVED.value,
        CaseStatus.REJECTED.value,
        CaseStatus.MORE_EVIDENCE_REQUIRED.value,
        CaseStatus.GENERATING_REVIEW.value,
    },
    CaseStatus.MORE_EVIDENCE_REQUIRED.value: {CaseStatus.READY_FOR_INSPECTION.value},
    CaseStatus.APPROVED.value: set(),
    CaseStatus.REJECTED.value: set(),
    CaseStatus.ERROR.value: {CaseStatus.READY_FOR_INSPECTION.value},
}


def transition(current: str, target: str) -> str:
    if current == target:
        return current
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(409, f"Invalid case transition: {current} -> {target}")
    return target
