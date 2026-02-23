"""API schemas module."""

from app.api.schemas.requests import (
    AnalysisRequest,
    ModelMetadata,
    Domain,
)
from app.api.schemas.responses import (
    AnalysisResponse,
    FailureDetail,
    ClaimAnalysis,
    RiskAssessment,
    Recommendation,
    CaseListResponse,
    CaseDetail,
    TaxonomyResponse,
    FailureTypeInfo,
    HealthResponse,
)

__all__ = [
    # Requests
    "AnalysisRequest",
    "ModelMetadata",
    "Domain",
    # Responses
    "AnalysisResponse",
    "FailureDetail",
    "ClaimAnalysis",
    "RiskAssessment",
    "Recommendation",
    "CaseListResponse",
    "CaseDetail",
    "TaxonomyResponse",
    "FailureTypeInfo",
    "HealthResponse",
]
