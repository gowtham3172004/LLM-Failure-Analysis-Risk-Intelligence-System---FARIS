"""Repository modules for database operations."""

from app.db.repositories.cases import CaseRepository
from app.db.repositories.failures import FailureRepository

__all__ = [
    "CaseRepository",
    "FailureRepository",
]
