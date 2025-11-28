"""Embedding service for RAG using sentence-transformers."""
from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings for documents and queries."""
    
    # Using all-MiniLM-L6-v2: Fast, good quality, 384 dimensions
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __init__(self, model_name: str | None = None):
        """Initialize embedding model.
        
        Args:
            model_name: Name of sentence-transformer model to use
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        logger.info(f"Loading embedding model: {self.model_name}")
        self._model = SentenceTransformer(self.model_name)
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
            Embedding vector
        """
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings for batch of texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True
        )
        return [emb.tolist() for emb in embeddings]
    
    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for search query.
        
        Args:
            query: Search query
            
        Returns:
            Query embedding vector
        """
        return self.embed_text(query)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance."""
    return EmbeddingService()
