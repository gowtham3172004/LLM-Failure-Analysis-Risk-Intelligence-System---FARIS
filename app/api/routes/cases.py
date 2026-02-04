"""
FARIS Cases API Routes

Endpoints for managing and retrieving analysis cases.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.responses import (
    AnalysisResponse,
    CaseDetail,
    CaseListResponse,
    CaseSummary,
    ClaimAnalysis,
    ErrorResponse,
    ExecutionMetadata,
    FailureDetail,
    FailureType,
    Recommendation,
    RiskAssessment,
    RiskLevel,
    Severity,
)
from app.config import get_settings
from app.db.database import get_db
from app.db.repositories.cases import CaseRepository

router = APIRouter(prefix="/api/cases", tags=["Cases"])
settings = get_settings()


@router.get(
    "",
    response_model=CaseListResponse,
    summary="List Analysis Cases",
    description="Retrieve a paginated list of analysis cases with optional filtering.",
)
async def list_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    failure_detected: Optional[bool] = Query(None, description="Filter by failure status"),
    db: AsyncSession = Depends(get_db),
) -> CaseListResponse:
    """
    List analysis cases with pagination and filtering.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        domain: Optional domain filter
        risk_level: Optional risk level filter
        failure_detected: Optional failure status filter
        db: Database session
    
    Returns:
        Paginated list of cases
    """
    repo = CaseRepository(db)
    
    cases, total = await repo.list_cases(
        page=page,
        page_size=page_size,
        domain=domain,
        risk_level=risk_level,
        failure_detected=failure_detected,
    )
    
    # Convert to summaries
    summaries = []
    for case in cases:
        summaries.append(CaseSummary(
            case_id=UUID(case.id),
            question_preview=case.question[:100] + "..." if len(case.question) > 100 else case.question,
            failure_detected=case.failure_detected,
            failure_count=case.failure_count,
            risk_level=RiskLevel(case.risk_level),
            risk_score=case.risk_score,
            domain=case.domain,
            created_at=case.created_at,
        ))
    
    has_more = (page * page_size) < total
    
    return CaseListResponse(
        cases=summaries,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get(
    "/{case_id}",
    response_model=CaseDetail,
    responses={
        404: {"description": "Case not found", "model": ErrorResponse},
    },
    summary="Get Case Details",
    description="Retrieve complete details for a specific analysis case.",
)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CaseDetail:
    """
    Get detailed information about an analysis case.
    
    Args:
        case_id: The case UUID
        db: Database session
    
    Returns:
        Complete case details including analysis results
    
    Raises:
        HTTPException: If case not found
    """
    repo = CaseRepository(db)
    case = await repo.get_by_id(str(case_id))
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )
    
    # Build failures
    failures = []
    for f in case.failures:
        try:
            failure_type = FailureType(f.failure_type)
        except ValueError:
            failure_type = FailureType.HALLUCINATION
        
        try:
            severity = Severity(f.severity)
        except ValueError:
            severity = Severity.MEDIUM
        
        failures.append(FailureDetail(
            failure_type=failure_type,
            detected=True,
            confidence=f.confidence,
            severity=severity,
            evidence=f.evidence or [],
            related_claim_ids=f.related_claim_ids or [],
            explanation=f.explanation or "",
        ))
    
    # Build claims
    claims = []
    for c in case.claims:
        claims.append(ClaimAnalysis(
            claim_id=c.claim_id,
            claim_text=c.claim_text,
            is_verifiable=c.is_verifiable,
            is_supported=c.is_supported,
            confidence=c.confidence,
            issues=c.issues or [],
        ))
    
    # Build recommendations
    recommendations = []
    for r in case.recommendations:
        try:
            failure_type = FailureType(r.failure_type)
        except ValueError:
            failure_type = FailureType.HALLUCINATION
        
        recommendations.append(Recommendation(
            recommendation_id=r.recommendation_id,
            priority=r.priority,
            failure_type=failure_type,
            title=r.title,
            description=r.description,
            implementation_hint=r.implementation_hint,
        ))
    
    # Build risk assessment
    try:
        risk_level = RiskLevel(case.risk_level)
    except ValueError:
        risk_level = RiskLevel.LOW
    
    risk_assessment = RiskAssessment(
        risk_score=case.risk_score,
        risk_level=risk_level,
        domain=case.domain,
        domain_multiplier=settings.domain_multipliers.get(case.domain, 1.0),
        contributing_factors=[],
        explanation="",
    )
    
    # Build metadata
    metadata = ExecutionMetadata(
        analysis_id=UUID(case.id),
        timestamp=case.created_at,
        processing_time_ms=case.processing_time_ms,
        model_used=case.analysis_model,
        version=case.faris_version,
    )
    
    # Build failure types list
    failure_types = list(set(f.failure_type for f in failures))
    
    # Build analysis response
    analysis = AnalysisResponse(
        failure_detected=case.failure_detected,
        failure_types=failure_types,
        failures=failures,
        claims=claims,
        risk_assessment=risk_assessment,
        recommendations=recommendations,
        explanation=case.explanation or "Analysis complete.",
        metadata=metadata,
    )
    
    return CaseDetail(
        case_id=UUID(case.id),
        question=case.question,
        llm_answer=case.llm_answer,
        context=case.context,
        domain=case.domain,
        model_name=case.model_name,
        analysis=analysis,
        created_at=case.created_at,
    )


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Case not found", "model": ErrorResponse},
    },
    summary="Delete Case",
    description="Delete an analysis case and all related data.",
)
async def delete_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an analysis case.
    
    Args:
        case_id: The case UUID
        db: Database session
    
    Raises:
        HTTPException: If case not found
    """
    repo = CaseRepository(db)
    deleted = await repo.delete(str(case_id))
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )


@router.get(
    "/statistics/summary",
    summary="Get Statistics",
    description="Get aggregate statistics about analysis cases.",
)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get aggregate statistics.
    
    Args:
        db: Database session
    
    Returns:
        Statistics dictionary
    """
    repo = CaseRepository(db)
    stats = await repo.get_statistics()
    return stats
