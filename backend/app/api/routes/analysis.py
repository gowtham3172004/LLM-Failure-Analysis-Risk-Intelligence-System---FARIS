"""
FARIS Analysis API Routes

Single unified analysis endpoint with optional Truth Engine ingestion.
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.requests import AnalysisRequest, Domain
from app.api.schemas.responses import AnalysisResponse, ErrorResponse
from app.db.database import get_db
from app.services.analysis_service import AnalysisService
from app.services.ingestion import IngestionError, fetch_from_file, fetch_from_url, refine_context

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Ingestion failed", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Analyze LLM Output",
    description="""
    Analyze an LLM output for potential failure modes using the full
    FARIS pipeline with optional Truth Engine ingestion.

    Optionally supply a **source URL** or upload a **PDF file** as
    ground-truth reference.  FARIS will:

    1. **Ingest** — scrape the URL or extract text from the PDF.
    2. **Refine** — rank text chunks by semantic similarity to the question.
    3. **Analyze** — run the full LangGraph failure-detection pipeline.
    4. **Remediate** — if risk score exceeds threshold, auto-correct the answer.

    Use `multipart/form-data`.
    """,
)
async def analyze_llm_output(
    question: str = Form(..., min_length=1, max_length=10000, description="The question posed to the LLM"),
    llm_answer: str = Form(..., min_length=1, max_length=50000, description="The LLM's response to analyze"),
    domain: Domain = Form(default=Domain.GENERAL, description="Domain for context-aware analysis"),
    source_url: Optional[str] = Form(default=None, max_length=2048, description="URL to scrape as ground truth"),
    file: Optional[UploadFile] = File(default=None, description="PDF file to use as ground truth"),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """
    Unified analysis endpoint — ingests context from URL/PDF (if provided),
    refines it, runs the full detection pipeline, and remediates if needed.
    """
    # --- Validate: at most one external source ---
    if source_url and file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either source_url or file, not both.",
        )

    verified_context: Optional[str] = None
    context_source: Optional[str] = None
    raw_text: Optional[str] = None

    # --- Ingest ---
    try:
        if source_url:
            raw_text = await fetch_from_url(source_url)
            context_source = "url"
        elif file:
            file_bytes = await file.read()
            raw_text = await fetch_from_file(file_bytes, file.filename or "upload.pdf")
            context_source = "pdf"
    except IngestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # --- Refine ---
    if raw_text:
        try:
            verified_context = await refine_context(question, raw_text)
        except Exception:
            # If refinement fails, use raw text truncated
            verified_context = raw_text[:4000]

    # --- Build analysis request ---
    analysis_request = AnalysisRequest(
        question=question,
        llm_answer=llm_answer,
        context=verified_context,
        domain=domain,
    )

    # --- Run analysis pipeline ---
    try:
        service = AnalysisService(db=db)
        response = await service.analyze(
            request=analysis_request,
            persist=True,
            verified_context=verified_context,
            context_source=context_source,
        )
        return response
    except RuntimeError as exc:
        err_msg = str(exc).lower()
        if "rate limit" in err_msg or "quota" in err_msg:
            raise HTTPException(
                status_code=429,
                detail=(
                    "The Gemini API rate limit has been reached. "
                    "Please wait 1-2 minutes and try again. "
                    "Tip: The free tier allows ~10 requests per minute."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        )


# Backward-compatible alias
@router.post("/analyze/deep-scan", response_model=AnalysisResponse, include_in_schema=False)
async def deep_scan_alias(
    question: str = Form(..., min_length=1, max_length=10000),
    llm_answer: str = Form(..., min_length=1, max_length=50000),
    domain: Domain = Form(default=Domain.GENERAL),
    source_url: Optional[str] = Form(default=None, max_length=2048),
    file: Optional[UploadFile] = File(default=None),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    return await analyze_llm_output(
        question=question, llm_answer=llm_answer, domain=domain,
        source_url=source_url, file=file, db=db,
    )


@router.post(
    "/analyze/quick",
    response_model=AnalysisResponse,
    summary="Quick Analysis (JSON, No Persistence)",
    description="Perform analysis without file upload or persistence. Accepts JSON body.",
)
async def analyze_llm_output_quick(
    request: AnalysisRequest,
) -> AnalysisResponse:
    """Quick analysis without database persistence. Accepts JSON."""
    try:
        service = AnalysisService(db=None)
        response = await service.analyze(request, persist=False)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )
