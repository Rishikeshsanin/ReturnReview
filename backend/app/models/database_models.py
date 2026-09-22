from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from sqlalchemy import String, Text, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CaseStatus(str, Enum):
    DRAFT = "DRAFT"
    READY_FOR_INSPECTION = "READY_FOR_INSPECTION"
    PROCESSING_CV = "PROCESSING_CV"
    CV_COMPLETE = "CV_COMPLETE"
    GENERATING_REVIEW = "GENERATING_REVIEW"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    MORE_EVIDENCE_REQUIRED = "MORE_EVIDENCE_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


class ReturnCase(Base):
    __tablename__ = "return_cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    external_case_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    product_name: Mapped[str] = mapped_column(String(160))
    product_category: Mapped[str] = mapped_column(String(80), default="cardboard_box")
    customer_reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default=CaseStatus.DRAFT.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    images: Mapped[list["CaseImage"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    reviews: Mapped[list["AIReview"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    decisions: Mapped[list["ReviewerDecision"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class CaseImage(Base):
    __tablename__ = "case_images"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("return_cases.id", ondelete="CASCADE"), index=True)
    image_path: Mapped[str] = mapped_column(Text)
    view_label: Mapped[str] = mapped_column(String(40), default="unspecified")
    width: Mapped[int] = mapped_column(default=0)
    height: Mapped[int] = mapped_column(default=0)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_warning: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case: Mapped["ReturnCase"] = relationship(back_populates="images")
    inspection: Mapped["CVInspection | None"] = relationship(back_populates="image", uselist=False, cascade="all, delete-orphan")


class CVInspection(Base):
    __tablename__ = "cv_inspections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_image_id: Mapped[str] = mapped_column(ForeignKey("case_images.id", ondelete="CASCADE"), unique=True)
    model_version: Mapped[str] = mapped_column(String(120))
    product_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    image: Mapped["CaseImage"] = relationship(back_populates="inspection")
    findings: Mapped[list["DefectFinding"]] = relationship(back_populates="inspection", cascade="all, delete-orphan")


class DefectFinding(Base):
    __tablename__ = "defect_findings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    inspection_id: Mapped[str] = mapped_column(ForeignKey("cv_inspections.id", ondelete="CASCADE"), index=True)
    defect_type: Mapped[str] = mapped_column(String(80), default="unknown")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    bbox_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    mask_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_area_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    inspection: Mapped["CVInspection"] = relationship(back_populates="findings")


class AIReview(Base):
    __tablename__ = "ai_reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("return_cases.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(40), default="deterministic")
    model_name: Mapped[str] = mapped_column(String(120), default="fallback")
    prompt_version: Mapped[str] = mapped_column(String(40), default="v1")
    review_json: Mapped[dict] = mapped_column(JSON)
    recommendation: Mapped[str] = mapped_column(String(80))
    unsupported_claim_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case: Mapped["ReturnCase"] = relationship(back_populates="reviews")


class ReviewerDecision(Base):
    __tablename__ = "reviewer_decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("return_cases.id", ondelete="CASCADE"), index=True)
    reviewer_action: Mapped[str] = mapped_column(String(60))
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_review_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case: Mapped["ReturnCase"] = relationship(back_populates="decisions")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(String(36), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
