from sqlalchemy.orm import Session
from app.models.database_models import ReturnCase
from app.models.response_models import VisualEvidence, DefectEvidence, AggregatedDefect


def aggregate_findings(findings: list[DefectEvidence]) -> list[AggregatedDefect]:
    """Simple MVP multi-view aggregation.

    Findings are grouped by predicted defect type. This intentionally does not
    claim geometric cross-view identity; it records which views support the
    same case-level defect class and preserves every source finding ID.
    """
    groups: dict[str, list[DefectEvidence]] = {}
    for finding in findings:
        groups.setdefault(finding.defect_type, []).append(finding)

    aggregated: list[AggregatedDefect] = []
    for defect_type, rows in groups.items():
        areas = [r.affected_area_percent for r in rows if r.affected_area_percent is not None]
        aggregated.append(AggregatedDefect(
            defect_type=defect_type,
            max_confidence=max(r.confidence for r in rows),
            supporting_image_ids=sorted({r.image_id for r in rows}),
            finding_ids=[r.finding_id for r in rows],
            max_affected_area_percent=max(areas) if areas else None,
        ))

    return sorted(aggregated, key=lambda r: r.max_confidence, reverse=True)


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

    aggregated = aggregate_findings(findings)
    for row in aggregated:
        if len(row.supporting_image_ids) > 1:
            uncertainties.append(
                f"{row.defect_type} appears in {len(row.supporting_image_ids)} views; "
                "the MVP groups these as supporting evidence but does not assert exact cross-view geometric identity."
            )

    return VisualEvidence(
        case_id=case.id,
        product_category=case.product_category,
        category_verified=verified,
        verification_score=max(scores) if scores else None,
        findings=findings,
        aggregated_defects=aggregated,
        uncertainties=uncertainties,
    )
