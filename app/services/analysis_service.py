"""
FARIS Analysis Service

Main service layer that orchestrates the analysis workflow
and handles persistence.
"""

import time
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.requests import AnalysisRequest
from app.api.schemas.responses import (
    AnalysisResponse,
    ClaimAnalysis,
    ExecutionMetadata,
    FailureDetail,
    FailureType,
    Recommendation,
    RiskAssessment,
    RiskLevel,
    Severity,
)
from app.config import get_settings
from app.core.graph import run_analysis
from app.db.repositories.cases import CaseRepository

settings = get_settings()


class AnalysisService:
    """
    Main service for LLM failure analysis.
    
    This service:
    1. Orchestrates the LangGraph analysis pipeline
    2. Converts internal state to API response format
    3. Persists results to database
    4. Handles errors gracefully
    """
    
    def __init__(self, db: Optional[AsyncSession] = None):
        """
        Initialize the analysis service.
        
        Args:
            db: Optional database session for persistence
        """
        self.db = db
        self._case_repo = CaseRepository(db) if db else None
    
    async def analyze(
        self,
        request: AnalysisRequest,
        persist: bool = True,
    ) -> AnalysisResponse:
        """
        Perform complete failure analysis on an LLM output.
        
        Args:
            request: The analysis request
            persist: Whether to persist results to database
        
        Returns:
            Complete AnalysisResponse
        """
        start_time = time.time()
        analysis_id = uuid4()
        
        # Prepare model metadata
        model_metadata = {}
        if request.model_metadata:
            model_metadata = {
                "model_name": request.model_metadata.model_name,
                "temperature": request.model_metadata.temperature,
                "source": request.model_metadata.source,
                "additional_params": request.model_metadata.additional_params,
            }
        
        # Run the analysis pipeline
        result = await run_analysis(
            question=request.question,
            answer=request.llm_answer,
            context=request.context,
            domain=request.domain.value,
            model_metadata=model_metadata,
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert to response format
        response = self._build_response(
            result=result,
            analysis_id=analysis_id,
            processing_time_ms=processing_time_ms,
        )
        
        # Persist to database
        if persist and self._case_repo:
            await self._persist_analysis(
                request=request,
                response=response,
                result=result,
            )
        
        return response
    
    def _build_response(
        self,
        result: dict,
        analysis_id: UUID,
        processing_time_ms: int,
    ) -> AnalysisResponse:
        """
        Convert LangGraph state to API response format.
        
        Args:
            result: Final LangGraph state
            analysis_id: Unique analysis ID
            processing_time_ms: Processing time
        
        Returns:
            Formatted AnalysisResponse
        """
        # Build failure details
        failures = []
        for f in result.get("detected_failures", []):
            failure_type_str = f.get("failure_type", "hallucination")
            try:
                failure_type = FailureType(failure_type_str)
            except ValueError:
                failure_type = FailureType.HALLUCINATION
            
            severity_str = f.get("severity", "medium")
            try:
                severity = Severity(severity_str)
            except ValueError:
                severity = Severity.MEDIUM
            
            failures.append(FailureDetail(
                failure_type=failure_type,
                detected=f.get("detected", False),
                confidence=f.get("confidence", 0.0),
                severity=severity,
                evidence=f.get("evidence", []),
                related_claim_ids=f.get("related_claim_ids", []),
                explanation=f.get("explanation", ""),
            ))
        
        # Build claim analysis
        claims = []
        for c in result.get("claims", []):
            claims.append(ClaimAnalysis(
                claim_id=c.get("claim_id", ""),
                claim_text=c.get("claim_text", ""),
                is_verifiable=True,  # Simplified
                is_supported=True,  # Will be updated based on failures
                confidence=0.8,  # Default
                issues=[],
            ))
        
        # Mark claims with issues
        for f in failures:
            for claim_id in f.related_claim_ids:
                for claim in claims:
                    if claim.claim_id == claim_id:
                        claim.is_supported = False
                        claim.issues.append(f.failure_type.value)
        
        # Build risk assessment
        risk_level_str = result.get("risk_level", "low")
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            risk_level = RiskLevel.LOW
        
        risk_assessment = RiskAssessment(
            risk_score=result.get("risk_score", 0.0),
            risk_level=risk_level,
            domain=result.get("domain", "general"),
            domain_multiplier=result.get("domain_multiplier", 1.0),
            contributing_factors=result.get("contributing_factors", []),
            explanation=result.get("risk_explanation", ""),
        )
        
        # Build recommendations
        recommendations = []
        for r in result.get("recommendations", []):
            failure_type_str = r.get("failure_type", "hallucination")
            try:
                failure_type = FailureType(failure_type_str)
            except ValueError:
                failure_type = FailureType.HALLUCINATION
            
            recommendations.append(Recommendation(
                recommendation_id=r.get("recommendation_id", "r1"),
                priority=r.get("priority", 3),
                failure_type=failure_type,
                title=r.get("title", ""),
                description=r.get("description", ""),
                implementation_hint=r.get("implementation_hint"),
            ))
        
        # Build metadata
        metadata = ExecutionMetadata(
            analysis_id=analysis_id,
            timestamp=datetime.utcnow(),
            processing_time_ms=processing_time_ms,
            model_used=settings.ollama_model,
            version=settings.app_version,
        )
        
        # Build failure types list
        failure_types = [FailureType(ft) for ft in result.get("failure_types", [])]
        
        return AnalysisResponse(
            failure_detected=result.get("failure_detected", False),
            failure_types=failure_types,
            failures=failures,
            claims=claims,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            explanation=result.get("explanation", "Analysis complete."),
            metadata=metadata,
        )
    
    async def _persist_analysis(
        self,
        request: AnalysisRequest,
        response: AnalysisResponse,
        result: dict,
    ) -> None:
        """
        Persist analysis results to database.
        
        Args:
            request: Original request
            response: Formatted response
            result: Raw LangGraph state
        """
        if not self._case_repo:
            return
        
        try:
            # Create the case
            case = await self._case_repo.create(
                question=request.question,
                llm_answer=request.llm_answer,
                context=request.context,
                domain=request.domain.value,
                model_name=request.model_metadata.model_name if request.model_metadata else None,
                model_metadata=request.model_metadata.model_dump() if request.model_metadata else None,
                failure_detected=response.failure_detected,
                failure_count=len(response.failures),
                risk_score=response.risk_assessment.risk_score,
                risk_level=response.risk_assessment.risk_level.value,
                explanation=response.explanation,
                processing_time_ms=response.metadata.processing_time_ms,
                analysis_model=settings.ollama_model,
            )
            
            # Add failures
            for failure in response.failures:
                await self._case_repo.add_failure(
                    case_id=case.id,
                    failure_type=failure.failure_type.value,
                    severity=failure.severity.value,
                    confidence=failure.confidence,
                    evidence=failure.evidence,
                    explanation=failure.explanation,
                    related_claim_ids=failure.related_claim_ids,
                )
            
            # Add claims
            for claim in response.claims:
                await self._case_repo.add_claim(
                    case_id=case.id,
                    claim_id=claim.claim_id,
                    claim_text=claim.claim_text,
                    is_verifiable=claim.is_verifiable,
                    is_supported=claim.is_supported,
                    confidence=claim.confidence,
                    issues=claim.issues,
                )
            
            # Add recommendations
            for rec in response.recommendations:
                await self._case_repo.add_recommendation(
                    case_id=case.id,
                    recommendation_id=rec.recommendation_id,
                    priority=rec.priority,
                    failure_type=rec.failure_type.value,
                    title=rec.title,
                    description=rec.description,
                    implementation_hint=rec.implementation_hint,
                )
            
        except Exception as e:
            # Log but don't fail the analysis
            import structlog
            logger = structlog.get_logger()
            logger.error("Failed to persist analysis", error=str(e))
