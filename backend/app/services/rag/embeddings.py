"""Embedding service for RAG using sentence-transformers.

Optimized for CPU-only environments (Railway, etc.)
"""
from __future__ import annotations

import logging
import os
import re
from functools import lru_cache

import torch


def sanitize_text(text: str | None) -> str:
    """Remove invalid Unicode characters (surrogates) that break tokenizers."""
    if not text:
        return ""
    # Remove surrogate characters (U+D800 to U+DFFF)
    cleaned = re.sub(r'[\ud800-\udfff]', '', text)
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
    cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', cleaned)
    return cleaned.strip() or "empty"

# Optimize CPU threading for Railway containers (typically 1-2 vCPUs)
CPU_THREADS = int(os.getenv("EMBEDDING_CPU_THREADS", "2"))
torch.set_num_threads(CPU_THREADS)
torch.set_num_interop_threads(1)

# Disable gradient computation globally for inference
torch.set_grad_enabled(False)

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings for documents and queries.
    
    Optimized for CPU inference with:
    - Controlled thread count for container environments
    - Disabled gradients for faster inference
    - Normalized embeddings for cosine similarity
    - LRU cache for repeated queries
    """
    
    # Using all-MiniLM-L6-v2: Fast, good quality, 384 dimensions
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __init__(self, model_name: str | None = None):
        """Initialize embedding model.
        
        Args:
            model_name: Name of sentence-transformer model to use
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        logger.info(f"Loading embedding model: {self.model_name}")
        logger.info(f"CPU threads: {CPU_THREADS}")
        
        self._model = SentenceTransformer(
            self.model_name,
            device="cpu",
        )
        # Put model in eval mode for inference optimization
        self._model.eval()
        
        # Cache for repeated query embeddings
        self._query_cache: dict[str, list[float]] = {}
        self._cache_max_size = 100
        
        logger.info(f"Embedding model loaded. Dimension: {self.embedding_dim}")
    
    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self._model.get_sentence_embedding_dimension()
    
    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (normalized for cosine similarity)
        """
        with torch.inference_mode():
            embedding = self._model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,  # Pre-normalize for faster cosine similarity
            )
        return embedding.tolist()
    
    def embed_batch(self, texts: list[str], batch_size: int = 16) -> list[list[float]]:
        """Generate embeddings for batch of texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing (smaller = less memory on CPU)
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Sanitize all texts to remove invalid Unicode
        sanitized_texts = [sanitize_text(t) for t in texts]
            
        logger.info(f"Embedding {len(sanitized_texts)} texts in batches of {batch_size}")
        
        with torch.inference_mode():
            embeddings = self._model.encode(
                sanitized_texts,
                batch_size=batch_size,
                show_progress_bar=len(sanitized_texts) > 100,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        return [emb.tolist() for emb in embeddings]
    
    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for search query with caching.
        
        Args:
            query: Search query
            
        Returns:
            Query embedding vector
        """
        # Check cache first
        query_key = query.strip().lower()
        if query_key in self._query_cache:
            return self._query_cache[query_key]
        
        embedding = self.embed_text(query)
        
        # Add to cache with size limit
        if len(self._query_cache) >= self._cache_max_size:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]
        
        self._query_cache[query_key] = embedding
        return embedding
    
    def clear_cache(self) -> None:
        """Clear the query embedding cache."""
        self._query_cache.clear()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance."""
    return EmbeddingService()
