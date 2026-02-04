"""
FARIS Analysis API Routes

Main endpoints for LLM failure analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.requests import AnalysisRequest, BatchAnalysisRequest
from app.api.schemas.responses import AnalysisResponse, ErrorResponse
from app.db.database import get_db
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Analyze LLM Output",
    description="""
    Analyze an LLM output for potential failure modes.
    
    This endpoint performs comprehensive failure analysis including:
    - Hallucination detection
    - Logical inconsistency detection
    - Missing assumptions detection
    - Overconfidence detection
    - Scope violation detection
    - Underspecification risk detection
    
    The analysis returns:
    - Detected failures with evidence
    - Claim-level analysis
    - Risk score and level
    - Actionable recommendations
    """,
)
async def analyze_llm_output(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """
    Analyze an LLM output for potential failures.
    
    Args:
        request: Analysis request containing question and LLM answer
        db: Database session for persistence
    
    Returns:
        Complete analysis results
    
    Raises:
        HTTPException: If analysis fails
    """
    try:
        service = AnalysisService(db=db)
        response = await service.analyze(request, persist=True)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post(
    "/analyze/quick",
    response_model=AnalysisResponse,
    summary="Quick Analysis (No Persistence)",
    description="Perform analysis without saving to database. Faster for testing.",
)
async def analyze_llm_output_quick(
    request: AnalysisRequest,
) -> AnalysisResponse:
    """
    Quick analysis without database persistence.
    
    Useful for testing and development.
    
    Args:
        request: Analysis request
    
    Returns:
        Analysis results (not persisted)
    """
    try:
        service = AnalysisService(db=None)
        response = await service.analyze(request, persist=False)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post(
    "/analyze/batch",
    response_model=list[AnalysisResponse],
    summary="Batch Analysis",
    description="Analyze multiple LLM outputs in a single request.",
)
async def analyze_batch(
    request: BatchAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> list[AnalysisResponse]:
    """
    Analyze multiple LLM outputs.
    
    Args:
        request: Batch of analysis requests
        db: Database session
    
    Returns:
        List of analysis results
    """
    service = AnalysisService(db=db)
    results = []
    
    for single_request in request.requests:
        try:
            response = await service.analyze(single_request, persist=True)
            results.append(response)
        except Exception as e:
            # For batch, we continue on individual failures
            # Could also return partial results with errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Batch analysis failed at item {len(results)}: {str(e)}",
            )
    
    return results
