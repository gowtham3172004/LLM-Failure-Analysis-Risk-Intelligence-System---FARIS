"""
FARIS Failure Repository

Data access layer for failure patterns and analytics.
"""

from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DetectedFailure, FailurePattern


class FailureRepository:
    """
    Repository for managing failure data and patterns.
    
    Provides operations for failure analytics and pattern recognition.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def get_failure_distribution(self) -> dict[str, int]:
        """
        Get distribution of failure types across all cases.
        
        Returns:
            Dictionary mapping failure types to counts
        """
        stmt = select(
            DetectedFailure.failure_type,
            func.count(DetectedFailure.id),
        ).group_by(DetectedFailure.failure_type)
        
        result = await self.session.execute(stmt)
        return dict(result.all())
    
    async def get_severity_distribution(self) -> dict[str, int]:
        """
        Get distribution of failure severities.
        
        Returns:
            Dictionary mapping severity levels to counts
        """
        stmt = select(
            DetectedFailure.severity,
            func.count(DetectedFailure.id),
        ).group_by(DetectedFailure.severity)
        
        result = await self.session.execute(stmt)
        return dict(result.all())
    
    async def get_most_common_failures(self, limit: int = 5) -> list[dict]:
        """
        Get the most common failure types.
        
        Args:
            limit: Maximum number of results
        
        Returns:
            List of failure type info with counts
        """
        stmt = (
            select(
                DetectedFailure.failure_type,
                func.count(DetectedFailure.id).label("count"),
                func.avg(DetectedFailure.confidence).label("avg_confidence"),
            )
            .group_by(DetectedFailure.failure_type)
            .order_by(desc("count"))
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        return [
            {
                "failure_type": row.failure_type,
                "count": row.count,
                "avg_confidence": round(row.avg_confidence or 0, 3),
            }
            for row in rows
        ]
    
    async def record_pattern(
        self,
        pattern_type: str,
        pattern_signature: str,
        case_id: str,
        risk_score: float,
    ) -> FailurePattern:
        """
        Record or update a failure pattern.
        
        Args:
            pattern_type: Type of pattern
            pattern_signature: Unique pattern signature
            case_id: ID of the case exhibiting this pattern
            risk_score: Risk score of this occurrence
        
        Returns:
            FailurePattern instance
        """
        # Check if pattern exists
        stmt = select(FailurePattern).where(
            FailurePattern.pattern_signature == pattern_signature
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing pattern
            existing.occurrence_count += 1
            existing.avg_risk_score = (
                (existing.avg_risk_score * (existing.occurrence_count - 1) + risk_score)
                / existing.occurrence_count
            )
            if case_id not in existing.example_case_ids:
                existing.example_case_ids = existing.example_case_ids + [case_id]
            await self.session.flush()
            return existing
        else:
            # Create new pattern
            pattern = FailurePattern(
                pattern_type=pattern_type,
                pattern_signature=pattern_signature,
                occurrence_count=1,
                avg_risk_score=risk_score,
                example_case_ids=[case_id],
            )
            self.session.add(pattern)
            await self.session.flush()
            return pattern
    
    async def find_similar_patterns(
        self,
        pattern_type: str,
        limit: int = 5,
    ) -> list[FailurePattern]:
        """
        Find similar failure patterns.
        
        Args:
            pattern_type: Type of pattern to search for
            limit: Maximum number of results
        
        Returns:
            List of similar FailurePattern instances
        """
        stmt = (
            select(FailurePattern)
            .where(FailurePattern.pattern_type == pattern_type)
            .order_by(desc(FailurePattern.occurrence_count))
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_high_risk_patterns(
        self,
        min_risk_score: float = 0.7,
        min_occurrences: int = 2,
    ) -> list[FailurePattern]:
        """
        Get patterns with high average risk scores.
        
        Args:
            min_risk_score: Minimum average risk score
            min_occurrences: Minimum number of occurrences
        
        Returns:
            List of high-risk FailurePattern instances
        """
        stmt = (
            select(FailurePattern)
            .where(
                FailurePattern.avg_risk_score >= min_risk_score,
                FailurePattern.occurrence_count >= min_occurrences,
            )
            .order_by(desc(FailurePattern.avg_risk_score))
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
