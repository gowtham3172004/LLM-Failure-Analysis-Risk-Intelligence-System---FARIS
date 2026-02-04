"""
FARIS Embedding Encoder

Local embedding generation using SentenceTransformers.
Used for semantic similarity in failure pattern matching.
"""

from functools import lru_cache
from typing import Optional, Union

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings

settings = get_settings()


class EmbeddingEncoder:
    """
    Embedding encoder using SentenceTransformers.
    
    Provides:
    - Text to embedding conversion
    - Batch encoding for efficiency
    - Similarity calculations
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        """
        Initialize the embedding encoder.
        
        Args:
            model_name: SentenceTransformer model name (defaults to settings)
            device: Device to run on (cpu/cuda, defaults to settings)
        """
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        
        self._model = SentenceTransformer(
            self.model_name,
            device=self.device,
        )
        
        # Cache dimension info
        self._dimension = self._model.get_sentence_embedding_dimension()
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return self._dimension
    
    def encode(
        self,
        text: Union[str, list[str]],
        normalize: bool = True,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode text to embeddings.
        
        Args:
            text: Single string or list of strings to encode
            normalize: Whether to L2 normalize embeddings
            show_progress: Show progress bar for batch encoding
        
        Returns:
            Numpy array of shape (n, dimension) or (dimension,)
        """
        embeddings = self._model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )
        
        return embeddings
    
    def encode_single(self, text: str, normalize: bool = True) -> list[float]:
        """
        Encode a single text to embedding list.
        
        Convenience method that returns a Python list instead of numpy array.
        
        Args:
            text: Text to encode
            normalize: Whether to normalize
        
        Returns:
            Embedding as list of floats
        """
        embedding = self.encode(text, normalize=normalize)
        return embedding.tolist()
    
    def encode_batch(
        self,
        texts: list[str],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress: bool = True,
    ) -> list[list[float]]:
        """
        Encode multiple texts efficiently.
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            normalize: Whether to normalize
            show_progress: Show progress bar
        
        Returns:
            List of embeddings as lists of floats
        """
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )
        
        return embeddings.tolist()
    
    def similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Similarity score (0-1 for normalized embeddings)
        """
        emb1 = self.encode(text1, normalize=True)
        emb2 = self.encode(text2, normalize=True)
        
        # Cosine similarity (dot product for normalized vectors)
        similarity = np.dot(emb1, emb2)
        
        return float(similarity)
    
    def batch_similarity(
        self,
        query: str,
        candidates: list[str],
    ) -> list[tuple[int, float]]:
        """
        Calculate similarity of query against multiple candidates.
        
        Args:
            query: Query text
            candidates: List of candidate texts
        
        Returns:
            List of (index, similarity) tuples sorted by similarity descending
        """
        query_emb = self.encode(query, normalize=True)
        candidate_embs = self.encode(candidates, normalize=True)
        
        # Calculate all similarities
        similarities = np.dot(candidate_embs, query_emb)
        
        # Create sorted results
        results = [(i, float(sim)) for i, sim in enumerate(similarities)]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def find_most_similar(
        self,
        query: str,
        candidates: list[str],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[dict]:
        """
        Find the most similar candidates to a query.
        
        Args:
            query: Query text
            candidates: List of candidate texts
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
        
        Returns:
            List of dicts with index, text, and similarity
        """
        results = self.batch_similarity(query, candidates)
        
        # Filter by threshold and limit
        filtered = [
            {
                "index": idx,
                "text": candidates[idx],
                "similarity": sim,
            }
            for idx, sim in results
            if sim >= threshold
        ][:top_k]
        
        return filtered


# Singleton instance
_encoder: Optional[EmbeddingEncoder] = None


def get_embedding_encoder() -> EmbeddingEncoder:
    """
    Get the embedding encoder singleton.
    
    Returns:
        EmbeddingEncoder instance
    """
    global _encoder
    if _encoder is None:
        _encoder = EmbeddingEncoder()
    return _encoder


def reset_embedding_encoder() -> None:
    """Reset the encoder singleton (for testing)."""
    global _encoder
    _encoder = None
