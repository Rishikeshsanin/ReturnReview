from __future__ import annotations
import re

from app.models.response_models import ReviewOutput, VisualEvidence, PolicyReference

PROHIBITED_UNSUPPORTED_PHRASES = (
    "internal damage",
    "customer caused",
    "user caused",
    "fraud",
    "fraudulent",
    "counterfeit",
    "inauthentic",
    "damage occurred during",
)


def validate_review(
    review: ReviewOutput,
    evidence: VisualEvidence,
    policy: PolicyReference | None,
) -> ReviewOutput:
    """Deterministically check that LLM output stays inside the evidence boundary."""
    problems: list[str] = []
    evidence_by_image: dict[str, set[str]] = {}
    for finding in evidence.findings:
        evidence_by_image.setdefault(finding.image_id, set()).add(finding.defect_type.lower())

    for item in review.visual_findings:
        image_id = item.evidence_image_id
        text = item.finding.lower()
        if image_id not in evidence_by_image:
            problems.append(f"Visual claim references unknown evidence image '{image_id}'.")
            continue
        known_types = evidence_by_image[image_id]
        if known_types and not any(label.replace("_", " ") in text or label in text for label in known_types if label != "unknown"):
            if "unknown" not in known_types:
                problems.append(f"Visual claim for image '{image_id}' does not name a supported defect class.")

    combined = " ".join(
        [review.case_summary, review.review_status]
        + [x.finding for x in review.visual_findings]
        + list(review.missing_information)
        + list(review.uncertainties)
    ).lower()
    for phrase in PROHIBITED_UNSUPPORTED_PHRASES:
        if phrase in combined:
            problems.append(f"Unsupported causal/sensitive claim detected: '{phrase}'.")

    confidence_complement = re.search(
        r"\b(?:leaving|means?|implies?)\s+(?:an?\s+)?\d+(?:\.\d+)?%\s+(?:margin\s+of\s+)?uncertainty\b",
        combined,
    )
    if confidence_complement and "confidence" in combined:
        problems.append(
            "Unsupported confidence arithmetic detected: model confidence must not be converted into complementary uncertainty."
        )

    if review.policy_reference:
        if policy is None or review.policy_reference.policy_id != policy.policy_id:
            problems.append("Review references a policy that was not retrieved for this case.")

    if problems:
        safe = review.model_copy(deep=True)
        safe.unsupported_claims_detected = True
        safe.uncertainties = list(dict.fromkeys([*safe.uncertainties, *problems]))
        safe.recommended_action = (
            "insufficient_evidence" if not evidence.category_verified else "manual_review"
        )
        safe.review_status = (
            "Category verification incomplete; evidence is insufficient for a visual-damage review."
            if not evidence.category_verified
            else "Grounding guard flagged the draft for human review."
        )
        return safe

    safe = review.model_copy(deep=True)
    safe.unsupported_claims_detected = False
    if not evidence.category_verified:
        safe.recommended_action = "insufficient_evidence"
        safe.review_status = (
            "Category verification incomplete; evidence is insufficient for a visual-damage review."
        )
    return safe
