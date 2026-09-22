from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.database_models import (
    ReturnCase, CaseImage, CVInspection, DefectFinding, AIReview,
    ReviewerDecision, AuditEvent, CaseStatus,
)
from app.models.request_models import CaseCreate, ReviewerDecisionCreate
from app.models.response_models import CaseOut
from app.services.case_service import get_case_or_404
from app.services.image_service import validate_and_store
from app.services.cv_service import cv_service, CVUnavailable
from app.services.evidence_service import build_visual_evidence
from app.services.agent_service import run_review_agent
from app.services.audit_service import record_event
from app.services.status_service import transition

router = APIRouter(prefix="/api/cases", tags=["cases"])
ALLOWED_VIEWS = {"front", "back", "left", "right", "top", "bottom", "unspecified"}


@router.post("", response_model=CaseOut, status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    exists = db.scalar(select(ReturnCase).where(ReturnCase.external_case_id == payload.external_case_id))
    if exists:
        raise HTTPException(409, "A case with this case/order ID already exists")
    case = ReturnCase(**payload.model_dump())
    db.add(case)
    db.flush()
    record_event(db, case.id, "CASE_CREATED")
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db)):
    return list(db.scalars(select(ReturnCase).order_by(ReturnCase.created_at.desc())).all())


@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = get_case_or_404(db, case_id)
    evidence = build_visual_evidence(db, case)
    latest_review = case.reviews[-1].review_json if case.reviews else None
    latest_decision = case.decisions[-1].reviewer_action if case.decisions else None
    events = list(db.scalars(
        select(AuditEvent).where(AuditEvent.case_id == case.id).order_by(AuditEvent.created_at.asc())
    ).all())
    return {
        "case": CaseOut.model_validate(case),
        "images": [
            {
                "id": i.id,
                "view_label": i.view_label,
                "quality_score": i.quality_score,
                "quality_warning": i.quality_warning,
                "image_path": i.image_path,
                "image_url": f"/media/{i.image_path}",
            }
            for i in case.images
        ],
        "evidence": evidence,
        "ai_review": latest_review,
        "human_decision": latest_decision,
        "timeline": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "payload": e.payload_json,
                "created_at": e.created_at,
            }
            for e in events
        ],
    }


@router.post("/{case_id}/images", status_code=201)
async def upload_image(
    case_id: str,
    image: UploadFile = File(...),
    view_label: str = Form("unspecified"),
    db: Session = Depends(get_db),
):
    case = get_case_or_404(db, case_id)
    if case.status not in {
        CaseStatus.DRAFT.value,
        CaseStatus.READY_FOR_INSPECTION.value,
        CaseStatus.MORE_EVIDENCE_REQUIRED.value,
        CaseStatus.ERROR.value,
    }:
        raise HTTPException(409, f"Images cannot be added while case is {case.status}")
    if len(case.images) >= 4:
        raise HTTPException(409, "MVP supports a maximum of 4 images per case")
    if view_label not in ALLOWED_VIEWS:
        raise HTTPException(422, f"Unsupported view label. Use one of: {', '.join(sorted(ALLOWED_VIEWS))}")

    stored = await validate_and_store(case.id, image)
    row = CaseImage(
        case_id=case.id,
        view_label=view_label,
        image_path=stored["path"],
        width=stored["width"],
        height=stored["height"],
        quality_score=stored["quality_score"],
        quality_warning=stored["quality_warning"],
    )
    db.add(row)
    case.status = transition(case.status, CaseStatus.READY_FOR_INSPECTION.value)
    db.flush()
    record_event(db, case.id, "IMAGE_UPLOADED", {"image_id": row.id, "view_label": view_label})
    db.commit()
    return {"image_id": row.id, **stored}


@router.post("/{case_id}/inspect")
def inspect_case(case_id: str, db: Session = Depends(get_db)):
    case = get_case_or_404(db, case_id)
    if len(case.images) < 2:
        raise HTTPException(400, "Upload at least 2 product views before inspection")
    if len(case.images) > 4:
        raise HTTPException(400, "MVP supports at most 4 product views")
    case.status = transition(case.status, CaseStatus.PROCESSING_CV.value)
    db.commit()
    try:
        for image in case.images:
            if image.inspection:
                continue
            result = cv_service.inspect(image.image_path, image.id)
            inspection = CVInspection(
                case_image_id=image.id,
                model_version=result["model_version"],
                product_similarity=result["product_similarity"],
                product_verified=result["product_verified"],
                latency_ms=result["latency_ms"],
                raw_evidence={"finding_count": len(result["findings"])},
            )
            db.add(inspection)
            db.flush()
            for finding in result["findings"]:
                db.add(DefectFinding(
                    inspection_id=inspection.id,
                    defect_type=finding["defect_type"],
                    confidence=finding["confidence"],
                    bbox_json=finding["bbox"],
                    mask_path=finding.get("mask_path"),
                    affected_area_percent=finding["affected_area_percent"],
                ))
        case.status = transition(case.status, CaseStatus.CV_COMPLETE.value)
        record_event(db, case.id, "CV_COMPLETED")
        db.commit()
    except CVUnavailable as exc:
        case.status = transition(case.status, CaseStatus.READY_FOR_INSPECTION.value)
        record_event(db, case.id, "CV_UNAVAILABLE", {"reason": str(exc)})
        db.commit()
        raise HTTPException(503, str(exc)) from exc
    return get_case(case_id, db)


@router.post("/{case_id}/ai-review")
def create_ai_review(case_id: str, db: Session = Depends(get_db)):
    case = get_case_or_404(db, case_id)
    case.status = transition(case.status, CaseStatus.GENERATING_REVIEW.value)
    db.commit()
    review, meta = run_review_agent(db, case)
    row = AIReview(
        case_id=case.id,
        provider=meta["provider"],
        model_name=meta["model"],
        prompt_version="v1",
        review_json=review.model_dump(),
        recommendation=review.recommended_action,
        unsupported_claim_flag=review.unsupported_claims_detected,
        latency_ms=meta["latency_ms"],
    )
    db.add(row)
    case.status = transition(case.status, CaseStatus.READY_FOR_REVIEW.value)
    record_event(db, case.id, "AI_REVIEW_CREATED", {
        "provider": meta["provider"],
        "model": meta["model"],
        "tool_calls": meta.get("tool_calls", []),
        "grounding_guard": meta.get("grounding_guard"),
        "unsupported_claims_detected": review.unsupported_claims_detected,
    })
    db.commit()
    return review


@router.post("/{case_id}/decision")
def record_decision(case_id: str, payload: ReviewerDecisionCreate, db: Session = Depends(get_db)):
    case = get_case_or_404(db, case_id)
    mapping = {
        "APPROVE": CaseStatus.APPROVED.value,
        "REJECT": CaseStatus.REJECTED.value,
        "REQUEST_MORE_EVIDENCE": CaseStatus.MORE_EVIDENCE_REQUIRED.value,
    }
    target = mapping[payload.action]
    case.status = transition(case.status, target)
    row = ReviewerDecision(
        case_id=case.id,
        reviewer_action=payload.action,
        reviewer_notes=payload.notes,
        edited_review_json=payload.edited_review_json,
    )
    db.add(row)
    record_event(db, case.id, "REVIEWER_DECISION", {
        "action": payload.action,
        "review_edited": payload.edited_review_json is not None,
    })
    db.commit()
    return {"case_id": case.id, "status": case.status, "decision": payload.action}
