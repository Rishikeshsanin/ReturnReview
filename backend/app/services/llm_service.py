from app.models.response_models import ReviewOutput, VisualEvidence, PolicyReference

SYSTEM_PROMPT = """You are ReturnReview, an evidence-based product return inspection assistant.
Only make claims supported by structured CV evidence, case metadata, and retrieved policy.
Never infer invisible internal damage, cause, customer intent, authenticity, fraud, or who caused damage.
Never make the final approve/reject decision. Clearly state uncertainty and cite evidence_image_id for each visual finding.
Return output matching the provided JSON schema."""


def deterministic_review(
    evidence: VisualEvidence,
    policy: PolicyReference | None,
    customer_reason: str,
) -> ReviewOutput:
    if not evidence.category_verified:
        action = "insufficient_evidence"
        status = "Category verification incomplete."
    elif not evidence.findings:
        action = "no_visible_damage_detected"
        status = "No visible damage finding is available from the CV pipeline."
    elif any(f.defect_type == "unknown" for f in evidence.findings):
        action = "manual_review"
        status = "Visible damage is localized but at least one defect type remains uncertain."
    else:
        action = "manual_review"
        status = "Visible damage evidence is available for human review."

    visual_findings = [
        {
            "finding": f"Visible {f.defect_type} localized by the CV pipeline.",
            "evidence_image_id": f.image_id,
            "confidence": f.confidence,
            "affected_area_percent": f.affected_area_percent,
        }
        for f in evidence.findings
    ]

    return ReviewOutput(
        case_summary=f"Returned {evidence.product_category}; customer reason recorded as: {customer_reason}",
        visual_findings=visual_findings,
        policy_reference=policy,
        review_status=status,
        recommended_action=action,
        missing_information=[] if policy else ["Applicable return policy was not found."],
        uncertainties=evidence.uncertainties,
        unsupported_claims_detected=False,
    )
