"""
FARIS Database Models

SQLAlchemy ORM models for persisting analysis results, failures, and audit trails.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def generate_uuid() -> str:
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class AnalysisCase(Base):
    """
    Main table storing analysis cases.
    
    Each row represents one complete analysis of an LLM output,
    including the original input, analysis results, and metadata.
    """
    __tablename__ = "analysis_cases"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    
    # Original input
    question: Mapped[str] = mapped_column(Text, nullable=False)
    llm_answer: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(String(50), default="general")
    
    # Model metadata (JSON for flexibility)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Analysis results summary
    failure_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    
    # Full explanation
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing metadata
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    analysis_model: Mapped[str] = mapped_column(String(100), default="llama3.1:8b")
    faris_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    failures: Mapped[list["DetectedFailure"]] = relationship(
        "DetectedFailure",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    claims: Mapped[list["Claim"]] = relationship(
        "Claim",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<AnalysisCase(id={self.id}, risk_level={self.risk_level})>"


class DetectedFailure(Base):
    """
    Table storing individual detected failures.
    
    Each failure is linked to an analysis case and includes
    detailed evidence and confidence scores.
    """
    __tablename__ = "detected_failures"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Failure classification
    failure_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Evidence and explanation
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    related_claim_ids: Mapped[list] = mapped_column(JSON, default=list)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    
    # Relationships
    case: Mapped["AnalysisCase"] = relationship(
        "AnalysisCase",
        back_populates="failures",
    )
    
    def __repr__(self) -> str:
        return f"<DetectedFailure(type={self.failure_type}, severity={self.severity})>"


class Claim(Base):
    """
    Table storing extracted claims from LLM answers.
    
    Each claim is analyzed independently for precise
    identification of problematic statements.
    """
    __tablename__ = "claims"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Claim content
    claim_id: Mapped[str] = mapped_column(String(50), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Analysis results
    is_verifiable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_supported: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    issues: Mapped[list] = mapped_column(JSON, default=list)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    
    # Relationships
    case: Mapped["AnalysisCase"] = relationship(
        "AnalysisCase",
        back_populates="claims",
    )
    
    def __repr__(self) -> str:
        return f"<Claim(id={self.claim_id}, supported={self.is_supported})>"


class Recommendation(Base):
    """
    Table storing recommendations for addressing failures.
    
    Each recommendation is linked to specific failure types
    and provides actionable guidance.
    """
    __tablename__ = "recommendations"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analysis_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Recommendation content
    recommendation_id: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    failure_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    implementation_hint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    
    # Relationships
    case: Mapped["AnalysisCase"] = relationship(
        "AnalysisCase",
        back_populates="recommendations",
    )
    
    def __repr__(self) -> str:
        return f"<Recommendation(id={self.recommendation_id}, priority={self.priority})>"


class FailurePattern(Base):
    """
    Table for storing discovered failure patterns.
    
    Used for pattern recognition and similar failure retrieval.
    """
    __tablename__ = "failure_patterns"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    
    # Pattern identification
    pattern_type: Mapped[str] = mapped_column(String(50), nullable=False)
    pattern_signature: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Statistics
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    avg_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Example cases (JSON array of case IDs)
    example_case_ids: Mapped[list] = mapped_column(JSON, default=list)
    
    # Timestamps
    first_seen: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<FailurePattern(type={self.pattern_type}, count={self.occurrence_count})>"
