"""
FARIS API Response Schemas

Pydantic models for serializing API responses with complete type safety.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FailureType(str, Enum):
    """
    Core failure taxonomy for LLM outputs.
    
    This is a research-backed classification that covers the most common
    and impactful failure modes in LLM systems.
    """
    HALLUCINATION = "hallucination"
    LOGICAL_INCONSISTENCY = "logical_inconsistency"
    MISSING_ASSUMPTIONS = "missing_assumptions"
    OVERCONFIDENCE = "overconfidence"
    SCOPE_VIOLATION = "scope_violation"
    UNDERSPECIFICATION = "underspecification"


class Severity(str, Enum):
    """Severity levels for detected failures."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Overall risk level for deployment decisions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClaimAnalysis(BaseModel):
    """
    Analysis result for an individual claim extracted from the LLM answer.
    
    Each claim is analyzed independently to provide precise identification
    of problematic statements.
    """
    claim_id: str = Field(
        ...,
        description="Unique identifier for this claim"
    )
    claim_text: str = Field(
        ...,
        description="The extracted claim text"
    )
    is_verifiable: bool = Field(
        ...,
        description="Whether this claim can be verified from the given context"
    )
    is_supported: bool = Field(
        ...,
        description="Whether this claim is supported by evidence"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the analysis of this claim"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="List of identified issues with this claim"
    )


class FailureDetail(BaseModel):
    """
    Detailed information about a detected failure mode.
    
    Each failure includes evidence and is linked to specific claims
    for explainability.
    """
    failure_type: FailureType = Field(
        ...,
        description="Classification of the failure type"
    )
    detected: bool = Field(
        ...,
        description="Whether this failure type was detected"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this detection"
    )
    severity: Severity = Field(
        ...,
        description="Severity level of this failure"
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Evidence supporting this failure detection"
    )
    related_claim_ids: list[str] = Field(
        default_factory=list,
        description="IDs of claims related to this failure"
    )
    explanation: str = Field(
        ...,
        description="Human-readable explanation of this failure"
    )


class Recommendation(BaseModel):
    """
    Actionable recommendation to address detected failures.
    
    Recommendations are tied to specific failure types and provide
    concrete steps for mitigation.
    """
    recommendation_id: str = Field(
        ...,
        description="Unique identifier for this recommendation"
    )
    priority: int = Field(
        ...,
        ge=1,
        le=5,
        description="Priority level (1 = highest, 5 = lowest)"
    )
    failure_type: FailureType = Field(
        ...,
        description="The failure type this recommendation addresses"
    )
    title: str = Field(
        ...,
        description="Short title for the recommendation"
    )
    description: str = Field(
        ...,
        description="Detailed description of the recommended action"
    )
    implementation_hint: Optional[str] = Field(
        default=None,
        description="Technical hint for implementing this recommendation"
    )


class RiskAssessment(BaseModel):
    """
    Quantified risk assessment for deployment decisions.
    
    The risk score is calculated using a deterministic, explainable formula:
    risk = Σ (failure_confidence × severity_weight × domain_multiplier)
    """
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall risk score (0-1)"
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Categorical risk level"
    )
    domain: str = Field(
        ...,
        description="Domain used for risk calculation"
    )
    domain_multiplier: float = Field(
        ...,
        description="Risk multiplier applied for this domain"
    )
    contributing_factors: list[dict] = Field(
        default_factory=list,
        description="Breakdown of factors contributing to the risk score"
    )
    explanation: str = Field(
        ...,
        description="Human-readable explanation of the risk assessment"
    )


class ExecutionMetadata(BaseModel):
    """Metadata about the analysis execution."""
    
    analysis_id: UUID = Field(
        ...,
        description="Unique identifier for this analysis"
    )
    timestamp: datetime = Field(
        ...,
        description="When the analysis was performed"
    )
    processing_time_ms: int = Field(
        ...,
        description="Total processing time in milliseconds"
    )
    model_used: str = Field(
        ...,
        description="LLM model used for analysis"
    )
    version: str = Field(
        ...,
        description="FARIS version that performed the analysis"
    )


class AnalysisResponse(BaseModel):
    """
    Complete analysis response returned by the FARIS API.
    
    This is the primary output that developers receive, containing:
    - Failure detection results
    - Claim-level analysis
    - Risk assessment
    - Actionable recommendations
    - Full execution metadata for auditing
    """
    # Core results
    failure_detected: bool = Field(
        ...,
        description="Whether any failure was detected"
    )
    failure_types: list[FailureType] = Field(
        default_factory=list,
        description="List of detected failure types"
    )
    
    # Detailed analysis
    failures: list[FailureDetail] = Field(
        default_factory=list,
        description="Detailed information about each detected failure"
    )
    claims: list[ClaimAnalysis] = Field(
        default_factory=list,
        description="Analysis of individual claims in the answer"
    )
    
    # Risk assessment
    risk_assessment: RiskAssessment = Field(
        ...,
        description="Quantified risk assessment"
    )
    
    # Recommendations
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Actionable recommendations to address failures"
    )
    
    # Summary
    explanation: str = Field(
        ...,
        description="Overall explanation of the analysis results"
    )
    
    # Metadata
    metadata: ExecutionMetadata = Field(
        ...,
        description="Execution metadata for auditing"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "failure_detected": True,
                    "failure_types": ["hallucination", "overconfidence"],
                    "failures": [
                        {
                            "failure_type": "hallucination",
                            "detected": True,
                            "confidence": 0.85,
                            "severity": "high",
                            "evidence": ["Claim about founding date is not verifiable"],
                            "related_claim_ids": ["c2"],
                            "explanation": "The answer contains an unsupported factual claim."
                        }
                    ],
                    "claims": [
                        {
                            "claim_id": "c1",
                            "claim_text": "Paris is the capital of France",
                            "is_verifiable": True,
                            "is_supported": True,
                            "confidence": 0.95,
                            "issues": []
                        }
                    ],
                    "risk_assessment": {
                        "risk_score": 0.67,
                        "risk_level": "medium",
                        "domain": "general",
                        "domain_multiplier": 1.0,
                        "contributing_factors": [],
                        "explanation": "Moderate risk due to detected hallucination."
                    },
                    "recommendations": [
                        {
                            "recommendation_id": "r1",
                            "priority": 1,
                            "failure_type": "hallucination",
                            "title": "Add source verification",
                            "description": "Implement retrieval-augmented generation.",
                            "implementation_hint": "Use RAG with verified sources"
                        }
                    ],
                    "explanation": "Analysis detected potential hallucination.",
                    "metadata": {
                        "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "processing_time_ms": 1250,
                        "model_used": "llama3.1:8b",
                        "version": "1.0.0"
                    }
                }
            ]
        }
    }


class CaseSummary(BaseModel):
    """Summary of an analysis case for list views."""
    
    case_id: UUID = Field(..., description="Unique case identifier")
    question_preview: str = Field(..., description="Preview of the question")
    failure_detected: bool = Field(..., description="Whether failures were detected")
    failure_count: int = Field(..., description="Number of failures detected")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    risk_score: float = Field(..., description="Risk score")
    domain: str = Field(..., description="Analysis domain")
    created_at: datetime = Field(..., description="When the analysis was performed")


class CaseListResponse(BaseModel):
    """Response for listing analysis cases."""
    
    cases: list[CaseSummary] = Field(
        default_factory=list,
        description="List of analysis case summaries"
    )
    total: int = Field(..., description="Total number of cases")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


class CaseDetail(BaseModel):
    """Full details of an analysis case including original input."""
    
    case_id: UUID = Field(..., description="Unique case identifier")
    question: str = Field(..., description="Original question")
    llm_answer: str = Field(..., description="Original LLM answer")
    context: Optional[str] = Field(None, description="Original context if provided")
    domain: str = Field(..., description="Analysis domain")
    model_name: Optional[str] = Field(None, description="Model that generated the answer")
    analysis: AnalysisResponse = Field(..., description="Complete analysis results")
    created_at: datetime = Field(..., description="When the analysis was performed")


class FailureTypeInfo(BaseModel):
    """Information about a failure type in the taxonomy."""
    
    type: FailureType = Field(..., description="Failure type identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed description")
    examples: list[str] = Field(default_factory=list, description="Example scenarios")
    detection_signals: list[str] = Field(
        default_factory=list,
        description="Signals used to detect this failure"
    )
    severity_weight: float = Field(..., description="Default severity weight")
    mitigation_strategies: list[str] = Field(
        default_factory=list,
        description="Strategies to mitigate this failure type"
    )


class TaxonomyResponse(BaseModel):
    """Complete failure taxonomy reference."""
    
    version: str = Field(..., description="Taxonomy version")
    failure_types: list[FailureTypeInfo] = Field(
        default_factory=list,
        description="All failure types in the taxonomy"
    )
    last_updated: datetime = Field(..., description="When taxonomy was last updated")


class HealthResponse(BaseModel):
    """API health check response."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current timestamp")
    components: dict[str, str] = Field(
        default_factory=dict,
        description="Status of individual components"
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
