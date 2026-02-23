"""
FARIS API Dependencies

Shared dependencies for FastAPI routes.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.analysis_service import AnalysisService


async def get_analysis_service(
    db: AsyncSession = None,
) -> AsyncGenerator[AnalysisService, None]:
    """
    Dependency that provides an analysis service.
    
    Args:
        db: Database session (injected)
    
    Yields:
        AnalysisService instance
    """
    service = AnalysisService(db=db)
    yield service


async def get_analysis_service_with_db() -> AsyncGenerator[AnalysisService, None]:
    """
    Dependency that provides an analysis service with database.
    
    Yields:
        AnalysisService instance with database connection
    """
    async for db in get_db():
        service = AnalysisService(db=db)
        yield service
