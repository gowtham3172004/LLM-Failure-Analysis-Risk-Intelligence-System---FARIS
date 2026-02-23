"""
FARIS Case Repository

Data access layer for analysis cases with async operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AnalysisCase, Claim, DetectedFailure, Recommendation


class CaseRepository:
    """
    Repository for managing analysis case persistence.
    
    Provides CRUD operations and queries for analysis cases
    with proper relationship loading.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def create(
        self,
        question: str,
        llm_answer: str,
        context: Optional[str] = None,
        domain: str = "general",
        model_name: Optional[str] = None,
        model_metadata: Optional[dict] = None,
        failure_detected: bool = False,
        failure_count: int = 0,
        risk_score: float = 0.0,
        risk_level: str = "low",
        explanation: Optional[str] = None,
        processing_time_ms: int = 0,
        analysis_model: str = "llama3.1:8b",
    ) -> AnalysisCase:
        """
        Create a new analysis case.
        
        Args:
            question: Original question
            llm_answer: LLM's answer to analyze
            context: Additional context
            domain: Analysis domain
            model_name: Name of the LLM model
            model_metadata: Additional model metadata
            failure_detected: Whether failures were detected
            failure_count: Number of failures
            risk_score: Calculated risk score
            risk_level: Categorical risk level
            explanation: Analysis explanation
            processing_time_ms: Processing time
            analysis_model: Model used for analysis
        
        Returns:
            Created AnalysisCase instance
        """
        case = AnalysisCase(
            question=question,
            llm_answer=llm_answer,
            context=context,
            domain=domain,
            model_name=model_name,
            model_metadata=model_metadata,
            failure_detected=failure_detected,
            failure_count=failure_count,
            risk_score=risk_score,
            risk_level=risk_level,
            explanation=explanation,
            processing_time_ms=processing_time_ms,
            analysis_model=analysis_model,
        )
        
        self.session.add(case)
        await self.session.flush()
        await self.session.refresh(case)
        
        return case
    
    async def get_by_id(self, case_id: str | UUID) -> Optional[AnalysisCase]:
        """
        Get a case by ID with all relationships loaded.
        
        Args:
            case_id: Case UUID
        
        Returns:
            AnalysisCase if found, None otherwise
        """
        case_id_str = str(case_id)
        
        stmt = (
            select(AnalysisCase)
            .where(AnalysisCase.id == case_id_str)
            .options(
                selectinload(AnalysisCase.failures),
                selectinload(AnalysisCase.claims),
                selectinload(AnalysisCase.recommendations),
            )
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_cases(
        self,
        page: int = 1,
        page_size: int = 20,
        domain: Optional[str] = None,
        risk_level: Optional[str] = None,
        failure_detected: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[AnalysisCase], int]:
        """
        List cases with pagination and filtering.
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            domain: Filter by domain
            risk_level: Filter by risk level
            failure_detected: Filter by failure status
            start_date: Filter by start date
            end_date: Filter by end date
        
        Returns:
            Tuple of (cases list, total count)
        """
        # Build base query
        stmt = select(AnalysisCase)
        count_stmt = select(func.count(AnalysisCase.id))
        
        # Apply filters
        if domain:
            stmt = stmt.where(AnalysisCase.domain == domain)
            count_stmt = count_stmt.where(AnalysisCase.domain == domain)
        
        if risk_level:
            stmt = stmt.where(AnalysisCase.risk_level == risk_level)
            count_stmt = count_stmt.where(AnalysisCase.risk_level == risk_level)
        
        if failure_detected is not None:
            stmt = stmt.where(AnalysisCase.failure_detected == failure_detected)
            count_stmt = count_stmt.where(AnalysisCase.failure_detected == failure_detected)
        
        if start_date:
            stmt = stmt.where(AnalysisCase.created_at >= start_date)
            count_stmt = count_stmt.where(AnalysisCase.created_at >= start_date)
        
        if end_date:
            stmt = stmt.where(AnalysisCase.created_at <= end_date)
            count_stmt = count_stmt.where(AnalysisCase.created_at <= end_date)
        
        # Get total count
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        stmt = (
            stmt
            .order_by(desc(AnalysisCase.created_at))
            .offset(offset)
            .limit(page_size)
        )
        
        # Execute query
        result = await self.session.execute(stmt)
        cases = list(result.scalars().all())
        
        return cases, total
    
    async def add_failure(
        self,
        case_id: str,
        failure_type: str,
        severity: str,
        confidence: float,
        evidence: list[str],
        explanation: str,
        related_claim_ids: list[str] = None,
    ) -> DetectedFailure:
        """
        Add a detected failure to a case.
        
        Args:
            case_id: Parent case ID
            failure_type: Type of failure
            severity: Severity level
            confidence: Detection confidence
            evidence: List of evidence strings
            explanation: Human-readable explanation
            related_claim_ids: IDs of related claims
        
        Returns:
            Created DetectedFailure instance
        """
        failure = DetectedFailure(
            case_id=case_id,
            failure_type=failure_type,
            severity=severity,
            confidence=confidence,
            evidence=evidence or [],
            explanation=explanation,
            related_claim_ids=related_claim_ids or [],
        )
        
        self.session.add(failure)
        await self.session.flush()
        
        return failure
    
    async def add_claim(
        self,
        case_id: str,
        claim_id: str,
        claim_text: str,
        is_verifiable: bool,
        is_supported: bool,
        confidence: float,
        issues: list[str] = None,
    ) -> Claim:
        """
        Add a claim to a case.
        
        Args:
            case_id: Parent case ID
            claim_id: Claim identifier
            claim_text: The claim text
            is_verifiable: Whether claim is verifiable
            is_supported: Whether claim is supported
            confidence: Analysis confidence
            issues: List of identified issues
        
        Returns:
            Created Claim instance
        """
        claim = Claim(
            case_id=case_id,
            claim_id=claim_id,
            claim_text=claim_text,
            is_verifiable=is_verifiable,
            is_supported=is_supported,
            confidence=confidence,
            issues=issues or [],
        )
        
        self.session.add(claim)
        await self.session.flush()
        
        return claim
    
    async def add_recommendation(
        self,
        case_id: str,
        recommendation_id: str,
        priority: int,
        failure_type: str,
        title: str,
        description: str,
        implementation_hint: Optional[str] = None,
    ) -> Recommendation:
        """
        Add a recommendation to a case.
        
        Args:
            case_id: Parent case ID
            recommendation_id: Recommendation identifier
            priority: Priority level (1-5)
            failure_type: Related failure type
            title: Short title
            description: Detailed description
            implementation_hint: Technical implementation hint
        
        Returns:
            Created Recommendation instance
        """
        recommendation = Recommendation(
            case_id=case_id,
            recommendation_id=recommendation_id,
            priority=priority,
            failure_type=failure_type,
            title=title,
            description=description,
            implementation_hint=implementation_hint,
        )
        
        self.session.add(recommendation)
        await self.session.flush()
        
        return recommendation
    
    async def delete(self, case_id: str | UUID) -> bool:
        """
        Delete a case and all related data.
        
        Args:
            case_id: Case UUID
        
        Returns:
            True if deleted, False if not found
        """
        case = await self.get_by_id(case_id)
        if not case:
            return False
        
        await self.session.delete(case)
        await self.session.flush()
        
        return True
    
    async def get_statistics(self) -> dict:
        """
        Get aggregate statistics about analysis cases.
        
        Returns:
            Dictionary with statistics
        """
        # Total cases
        total_stmt = select(func.count(AnalysisCase.id))
        total_result = await self.session.execute(total_stmt)
        total_cases = total_result.scalar() or 0
        
        # Cases with failures
        failure_stmt = select(func.count(AnalysisCase.id)).where(
            AnalysisCase.failure_detected == True  # noqa: E712
        )
        failure_result = await self.session.execute(failure_stmt)
        cases_with_failures = failure_result.scalar() or 0
        
        # Average risk score
        avg_risk_stmt = select(func.avg(AnalysisCase.risk_score))
        avg_risk_result = await self.session.execute(avg_risk_stmt)
        avg_risk_score = avg_risk_result.scalar() or 0.0
        
        # Risk level distribution
        risk_dist_stmt = select(
            AnalysisCase.risk_level,
            func.count(AnalysisCase.id),
        ).group_by(AnalysisCase.risk_level)
        risk_dist_result = await self.session.execute(risk_dist_stmt)
        risk_distribution = dict(risk_dist_result.all())
        
        # Domain distribution
        domain_dist_stmt = select(
            AnalysisCase.domain,
            func.count(AnalysisCase.id),
        ).group_by(AnalysisCase.domain)
        domain_dist_result = await self.session.execute(domain_dist_stmt)
        domain_distribution = dict(domain_dist_result.all())
        
        return {
            "total_cases": total_cases,
            "cases_with_failures": cases_with_failures,
            "failure_rate": cases_with_failures / total_cases if total_cases > 0 else 0,
            "avg_risk_score": round(avg_risk_score, 3),
            "risk_distribution": risk_distribution,
            "domain_distribution": domain_distribution,
        }
