from app.models.response_models import DefectEvidence
from app.services.evidence_service import aggregate_findings


def test_multi_view_findings_are_aggregated_by_defect_type():
    rows = [
        DefectEvidence(
            finding_id="f1",
            image_id="front",
            defect_type="tear",
            confidence=0.82,
            affected_area_percent=4.0,
        ),
        DefectEvidence(
            finding_id="f2",
            image_id="side",
            defect_type="tear",
            confidence=0.91,
            affected_area_percent=5.5,
        ),
        DefectEvidence(
            finding_id="f3",
            image_id="top",
            defect_type="dent_or_crush",
            confidence=0.73,
            affected_area_percent=7.0,
        ),
    ]

    result = aggregate_findings(rows)

    assert [row.defect_type for row in result] == ["tear", "dent_or_crush"]
    assert result[0].max_confidence == 0.91
    assert result[0].supporting_image_ids == ["front", "side"]
    assert result[0].finding_ids == ["f1", "f2"]
    assert result[0].max_affected_area_percent == 5.5
