from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class DefectEvidence(BaseModel):
    finding_id: str
    image_id: str
    defect_type: str
    confidence: float = Field(ge=0, le=1)
    bbox: list[float] | None = None
    mask_path: str | None = None
    affected_area_percent: float | None = None


class VisualEvidence(BaseModel):
    case_id: str
    product_category: str
    category_verified: bool
    verification_score: float | None
    findings: list[DefectEvidence]
    uncertainties: list[str] = []


class PolicyReference(BaseModel):
    policy_id: str
    name: str
    section: str
    text: str


class ReviewOutput(BaseModel):
    case_summary: str
    visual_findings: list[dict]
    policy_reference: PolicyReference | None
    review_status: str
    recommended_action: Literal[
        "manual_review",
        "request_more_evidence",
        "no_visible_damage_detected",
        "policy_mismatch",
        "insufficient_evidence",
    ]
    missing_information: list[str] = []
    uncertainties: list[str] = []
    unsupported_claims_detected: bool = False


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    external_case_id: str
    product_name: str
    product_category: str
    customer_reason: str
    status: str
    created_at: datetime
    updated_at: datetime
