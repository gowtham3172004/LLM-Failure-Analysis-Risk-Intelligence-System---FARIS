"""API routes module."""

from app.api.routes.analysis import router as analysis_router
from app.api.routes.cases import router as cases_router
from app.api.routes.taxonomy import router as taxonomy_router

__all__ = [
    "analysis_router",
    "cases_router",
    "taxonomy_router",
]
