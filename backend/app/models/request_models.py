from typing import Literal
from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    external_case_id: str = Field(min_length=2, max_length=100)
    product_name: str = Field(min_length=2, max_length=160)
    product_category: Literal["cardboard_box"] = "cardboard_box"
    customer_reason: str = Field(min_length=3, max_length=2000)


class ReviewerDecisionCreate(BaseModel):
    action: Literal["APPROVE", "REJECT", "REQUEST_MORE_EVIDENCE"]
    notes: str | None = Field(default=None, max_length=4000)
    edited_review_json: dict | None = None
