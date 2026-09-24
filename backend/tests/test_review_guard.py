from app.models.response_models import DefectEvidence, VisualEvidence, PolicyReference, ReviewOutput
from app.services.review_guard import validate_review


def evidence():
    return VisualEvidence(
        case_id="c1",
        product_category="cardboard_box",
        category_verified=True,
        verification_score=0.9,
        findings=[DefectEvidence(
            finding_id="f1",
            image_id="img1",
            defect_type="tear",
            confidence=0.88,
            bbox=[0,0,10,10],
        )],
    )


def policy():
    return PolicyReference(policy_id="P1", name="Policy", section="Visible damage", text="Manual review.")


def test_guard_accepts_grounded_claim():
    review = ReviewOutput(
        case_summary="Visible return evidence is available.",
        visual_findings=[{"finding":"Visible tear localized by CV.","evidence_image_id":"img1","confidence":0.88}],
        policy_reference=policy(),
        review_status="Ready for human review.",
        recommended_action="manual_review",
    )
    assert validate_review(review, evidence(), policy()).unsupported_claims_detected is False


def test_guard_flags_unknown_evidence_reference():
    review = ReviewOutput(
        case_summary="Evidence reviewed.",
        visual_findings=[{"finding":"Visible tear localized by CV.","evidence_image_id":"missing","confidence":0.88}],
        policy_reference=policy(),
        review_status="Ready.",
        recommended_action="manual_review",
    )
    guarded = validate_review(review, evidence(), policy())
    assert guarded.unsupported_claims_detected is True
    assert guarded.recommended_action == "manual_review"


def test_review_output_visual_findings_are_typed():
    schema = ReviewOutput.model_json_schema()
    visual_items = schema["properties"]["visual_findings"]["items"]
    assert "additionalProperties" not in visual_items


def test_guard_flags_confidence_complement_as_unsupported():
    review = ReviewOutput(
        case_summary="Visible dent or crush evidence is available.",
        visual_findings=[{
            "finding":"Visible tear localized by CV.",
            "evidence_image_id":"img1",
            "confidence":0.88,
        }],
        policy_reference=policy(),
        review_status="Ready for human review.",
        recommended_action="manual_review",
        uncertainties=[
            "The CV model confidence is 82%, leaving an 18% margin of uncertainty."
        ],
    )
    guarded = validate_review(review, evidence(), policy())
    assert guarded.unsupported_claims_detected is True
    assert any("confidence arithmetic" in item.lower() for item in guarded.uncertainties)


def test_guard_forces_insufficient_evidence_when_category_verification_fails():
    category_failed = VisualEvidence(
        case_id="c2",
        product_category="cardboard_box",
        category_verified=False,
        verification_score=0.2,
        findings=[],
    )
    review = ReviewOutput(
        case_summary="The expected product category could not be verified.",
        visual_findings=[],
        policy_reference=policy(),
        review_status="More images may help.",
        recommended_action="request_more_evidence",
    )
    guarded = validate_review(review, category_failed, policy())
    assert guarded.unsupported_claims_detected is False
    assert guarded.recommended_action == "insufficient_evidence"
    assert "category verification incomplete" in guarded.review_status.lower()
