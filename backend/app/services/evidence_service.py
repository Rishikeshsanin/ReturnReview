from sqlalchemy.orm import Session
from app.models.database_models import ReturnCase
from app.models.response_models import VisualEvidence, DefectEvidence


def build_visual_evidence(db: Session, case: ReturnCase) -> VisualEvidence:
    findings: list[DefectEvidence] = []
    scores: list[float] = []
    verified = True if case.images else False
    uncertainties: list[str] = []

    for image in case.images:
        inspection = image.inspection
        if inspection is None:
            verified = False
            continue
        if inspection.product_similarity is not None:
            scores.append(inspection.product_similarity)
        verified = verified and inspection.product_verified
        for f in inspection.findings:
            findings.append(DefectEvidence(
                finding_id=f.id,
                image_id=image.id,
                defect_type=f.defect_type,
                confidence=f.confidence,
                bbox=f.bbox_json,
                mask_path=f.mask_path,
                affected_area_percent=f.affected_area_percent,
            ))
            if f.defect_type == "unknown":
                uncertainties.append(f"Finding {f.id} has not been confidently classified.")

    return VisualEvidence(
        case_id=case.id,
        product_category=case.product_category,
        category_verified=verified,
        verification_score=max(scores) if scores else None,
        findings=findings,
        uncertainties=uncertainties,
    )
