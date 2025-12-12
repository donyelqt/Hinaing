"""Qdrant vector store for RAG document retrieval."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from ...core.config import get_settings
from ...schemas.rag import DocumentChunk, RetrievalResult
from .embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages document embeddings and similarity search using Qdrant."""
    
    COLLECTION_NAME = "baguio_documents"
    
    def __init__(self):
        """Initialize Qdrant client and collection."""
        settings = get_settings()
        
        # Use persistent storage on disk
        self.client = QdrantClient(path="qdrant_data")  # Persists data to ./qdrant_data
        self.embedding_service = get_embedding_service()
        
        # Create collection if it doesn't exist
        self._ensure_collection()
        logger.info("VectorStore initialized")
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_exists = any(c.name == self.COLLECTION_NAME for c in collections)
        
        if not collection_exists:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.embedding_service.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.COLLECTION_NAME}")
    
    async def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Embed and store document chunks.
        
        Args:
            chunks: List of document chunks to store
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        logger.info(f"Adding {len(chunks)} chunks to vector store")
        
        # Generate embeddings for all chunks
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_batch(chunk_texts)
        
        # Create Qdrant points
        points: list[PointStruct] = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(
                PointStruct(
                    id=hash(chunk.chunk_id) % (10 ** 8),  # Convert to int ID
                    vector=embedding,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "source_url": chunk.source_url,
                        "source_title": chunk.source_title,
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "total_chunks": chunk.total_chunks,
                        "published_at": chunk.published_at.isoformat() if chunk.published_at else None,
                        "metadata": chunk.metadata
                    }
                )
            )
        
        # Upsert points to Qdrant
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )
        
        logger.info(f"Successfully added {len(points)} chunks to vector store")
        return len(points)
    
    async def search(
        self, 
        query: str, 
        k: int = 10,
        filter_metadata: dict[str, Any] | None = None
    ) -> list[RetrievalResult]:
        """Semantic similarity search for relevant chunks.
        
        Args:
            query: Search query
            k: Number of top results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of retrieval results with chunks and scores
        """
        logger.info(f"Searching for top {k} chunks matching query: '{query[:100]}...'")
        
        # Embed query
        query_embedding = self.embedding_service.embed_query(query)
        
        # Search Qdrant
        conditions = []
        if filter_metadata:
            for key, value in filter_metadata.items():
                conditions.append(
                    FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value))
                )

        query_filter = Filter(must=conditions) if conditions else None

        search_response = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_embedding,
            limit=k,
            with_payload=True,
            query_filter=query_filter,
        )
        hits = getattr(search_response, "points", search_response) or []
        
        # Build RetrievalResult objects
        results: list[RetrievalResult] = []
        for rank, hit in enumerate(hits):
            # Some driver versions may return tuples instead of objects
            if isinstance(hit, tuple):
                hit = hit[0]
            payload = hit.payload or {}
            published_at = payload.get("published_at")
            if isinstance(published_at, str):
                try:
                    published_at_dt = datetime.fromisoformat(published_at)
                except ValueError:
                    published_at_dt = None
            else:
                published_at_dt = published_at
            chunk = DocumentChunk(
                chunk_id=payload.get("chunk_id", ""),
                source_url=payload.get("source_url", ""),
                source_title=payload.get("source_title", "Untitled"),
                content=payload.get("content", ""),
                chunk_index=payload.get("chunk_index", 0),
                total_chunks=payload.get("total_chunks", 0),
                published_at=published_at_dt,
                metadata=payload.get("metadata", {}),
                embedding=None  # Don't return embedding in result
            )
            
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=hit.score,
                    rank=rank + 1
                )
            )
        
        logger.info(f"Found {len(results)} relevant chunks (scores: {[r.score for r in results[:3]]})")
        return results
    
    async def clear(self):
        """Clear all documents from the collection."""
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
            self._ensure_collection()
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
    
    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Dictionary with collection stats
        """
        try:
            collection_info = self.client.get_collection(self.COLLECTION_NAME)
            return {
                "name": self.COLLECTION_NAME,
                "vector_count": collection_info.points_count,
                "vector_dim": self.embedding_service.embedding_dim,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Global instance
_instance: VectorStore | None = None

def get_vector_store() -> VectorStore:
    """Get singleton VectorStore instance."""
    global _instance
    if _instance is None:
        _instance = VectorStore()
    return _instance
