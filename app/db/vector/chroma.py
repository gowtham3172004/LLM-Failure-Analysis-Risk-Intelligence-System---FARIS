"""
FARIS ChromaDB Client

Vector database integration for semantic similarity search
on failure patterns and explanations.
"""

import hashlib
from functools import lru_cache
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

settings = get_settings()


class ChromaClient:
    """
    ChromaDB client for vector similarity operations.
    
    Used for:
    - Storing failure explanation embeddings
    - Finding similar past failures
    - Pattern recognition across analyses
    """
    
    def __init__(self):
        """Initialize ChromaDB client with persistence."""
        self._client = chromadb.Client(
            ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=settings.chroma_persist_directory,
                anonymized_telemetry=False,
            )
        )
        
        # Get or create the main collection
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"description": "FARIS failure analysis embeddings"},
        )
    
    @property
    def collection(self):
        """Get the main collection."""
        return self._collection
    
    def _generate_id(self, text: str) -> str:
        """Generate a deterministic ID from text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    async def add_failure_embedding(
        self,
        case_id: str,
        failure_type: str,
        explanation: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Add a failure explanation embedding to the collection.
        
        Args:
            case_id: The analysis case ID
            failure_type: Type of failure
            explanation: The failure explanation text
            embedding: Pre-computed embedding vector
            metadata: Additional metadata
        
        Returns:
            The document ID
        """
        doc_id = f"{case_id}_{failure_type}"
        
        doc_metadata = {
            "case_id": case_id,
            "failure_type": failure_type,
            **(metadata or {}),
        }
        
        self._collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[explanation],
            metadatas=[doc_metadata],
        )
        
        return doc_id
    
    async def find_similar_failures(
        self,
        query_embedding: list[float],
        failure_type: Optional[str] = None,
        n_results: int = 5,
    ) -> list[dict]:
        """
        Find similar failures based on embedding similarity.
        
        Args:
            query_embedding: Query embedding vector
            failure_type: Optional filter by failure type
            n_results: Number of results to return
        
        Returns:
            List of similar failure documents with scores
        """
        where_filter = None
        if failure_type:
            where_filter = {"failure_type": failure_type}
        
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        
        # Format results
        similar_failures = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                similar_failures.append({
                    "id": doc_id,
                    "document": results["documents"][0][i] if results["documents"] else None,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        
        return similar_failures
    
    async def add_claim_embedding(
        self,
        case_id: str,
        claim_id: str,
        claim_text: str,
        embedding: list[float],
        is_problematic: bool = False,
        issues: Optional[list[str]] = None,
    ) -> str:
        """
        Add a claim embedding for pattern matching.
        
        Args:
            case_id: The analysis case ID
            claim_id: The claim identifier
            claim_text: The claim text
            embedding: Pre-computed embedding vector
            is_problematic: Whether the claim has issues
            issues: List of identified issues
        
        Returns:
            The document ID
        """
        doc_id = f"claim_{case_id}_{claim_id}"
        
        metadata = {
            "case_id": case_id,
            "claim_id": claim_id,
            "is_problematic": is_problematic,
            "issues": ",".join(issues) if issues else "",
            "type": "claim",
        }
        
        self._collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[claim_text],
            metadatas=[metadata],
        )
        
        return doc_id
    
    async def find_similar_claims(
        self,
        query_embedding: list[float],
        only_problematic: bool = False,
        n_results: int = 5,
    ) -> list[dict]:
        """
        Find claims similar to a query.
        
        Args:
            query_embedding: Query embedding vector
            only_problematic: Only return problematic claims
            n_results: Number of results to return
        
        Returns:
            List of similar claims with metadata
        """
        where_filter = {"type": "claim"}
        if only_problematic:
            where_filter["is_problematic"] = True
        
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        
        similar_claims = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                similar_claims.append({
                    "id": doc_id,
                    "claim_text": results["documents"][0][i] if results["documents"] else None,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        
        return similar_claims
    
    def get_collection_stats(self) -> dict:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        return {
            "name": self._collection.name,
            "count": self._collection.count(),
            "metadata": self._collection.metadata,
        }
    
    def delete_case_embeddings(self, case_id: str) -> None:
        """
        Delete all embeddings for a case.
        
        Args:
            case_id: The case ID to delete embeddings for
        """
        # Get all IDs for this case
        results = self._collection.get(
            where={"case_id": case_id},
            include=[],
        )
        
        if results["ids"]:
            self._collection.delete(ids=results["ids"])


# Singleton instance
_chroma_client: Optional[ChromaClient] = None


def get_chroma_client() -> ChromaClient:
    """
    Get the ChromaDB client singleton.
    
    Returns:
        ChromaClient instance
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
    return _chroma_client


def reset_chroma_client() -> None:
    """Reset the ChromaDB client (for testing)."""
    global _chroma_client
    _chroma_client = None
