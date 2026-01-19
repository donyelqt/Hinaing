"""Qdrant vector store for RAG document retrieval.

Supports both:
- Qdrant Cloud (recommended): Set QDRANT_URL and QDRANT_API_KEY in .env
- Local disk storage (fallback): Uses ./qdrant_data folder
"""
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
    MIN_SCORE_THRESHOLD = 0.50  # Higher threshold for better precision
    
    def __init__(self):
        """Initialize Qdrant client (Cloud or local)."""
        settings = get_settings()
        
        # Use Qdrant Cloud if URL is configured, otherwise fall back to local
        qdrant_url = (settings.qdrant_url or "").strip()
        
        if qdrant_url:
            # Validate URL format
            if not qdrant_url.startswith(("http://", "https://")):
                logger.error(f"[VectorStore] Invalid QDRANT_URL format: {qdrant_url[:50]}...")
                raise ValueError(f"QDRANT_URL must start with http:// or https://")
            
            logger.info(f"[VectorStore] Connecting to Qdrant Cloud: {qdrant_url[:60]}...")
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=settings.qdrant_api_key,
            )
            self._is_cloud = True
        else:
            logger.info("[VectorStore] Using local Qdrant storage (qdrant_data/)")
            self.client = QdrantClient(path="qdrant_data")
            self._is_cloud = False
        
        self.embedding_service = get_embedding_service()
        self._ensure_collection()
        logger.info(f"[VectorStore] Initialized (cloud={self._is_cloud})")
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist, ensure indexes."""
        try:
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
                logger.info(f"[VectorStore] Created collection: {self.COLLECTION_NAME}")
            
            # Ensure payload indexes exist for filtering
            self._ensure_payload_indexes()
            
        except Exception as e:
            logger.error(f"[VectorStore] Failed to ensure collection: {e}")
            raise
    
    def _ensure_payload_indexes(self):
        """Create payload indexes for filterable fields."""
        from qdrant_client.models import PayloadSchemaType
        
        index_fields = ["focus_area", "topic"]
        
        for field in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                logger.info(f"[VectorStore] Created index for '{field}'")
            except Exception as e:
                # Index might already exist, that's fine
                if "already exists" in str(e).lower():
                    logger.debug(f"[VectorStore] Index '{field}' already exists")
                else:
                    logger.warning(f"[VectorStore] Failed to create index for '{field}': {e}")
    
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
                        "topic": chunk.metadata.get("topic") if chunk.metadata else None,
                        "focus_area": chunk.metadata.get("focus_area") if chunk.metadata else None,
                        "metadata": chunk.metadata
                    }
                )
            )
        
        # Upsert points to Qdrant
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )
        
        # Log topic and focus_area distribution for debugging
        topics = [p.payload.get("topic", "unknown") for p in points if p.payload]
        focus_areas = [p.payload.get("focus_area", "unknown") for p in points if p.payload]
        topic_counts = {}
        focus_counts = {}
        for t in topics:
            topic_counts[t] = topic_counts.get(t, 0) + 1
        for f in focus_areas:
            focus_counts[f] = focus_counts.get(f, 0) + 1
        logger.info(f"Successfully added {len(points)} chunks (focus_areas: {focus_counts}, topics: {topic_counts})")
        return len(points)
    
    async def search(
        self, 
        query: str, 
        k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
        topic_filter: str | None = None,
        focus_area_filter: str | None = None
    ) -> list[RetrievalResult]:
        """Semantic similarity search for relevant chunks.
        
        Args:
            query: Search query
            k: Number of top results to return
            filter_metadata: Optional metadata filters
            topic_filter: Optional granular topic to filter by (e.g., "crime incident")
            focus_area_filter: Optional focus area to filter by (e.g., "safety", "health")
            
        Returns:
            List of retrieval results with chunks and scores
        """
        logger.info(f"Searching for top {k} chunks matching query: '{query[:100]}...'")
        
        # Embed query
        query_embedding = self.embedding_service.embed_query(query)
        
        # Build filter conditions
        conditions = []
        if filter_metadata:
            for key, value in filter_metadata.items():
                conditions.append(
                    FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value))
                )
        
        # Add topic filter if specified
        if topic_filter:
            conditions.append(
                FieldCondition(key="topic", match=MatchValue(value=topic_filter))
            )
            logger.info(f"Applying topic filter: {topic_filter}")
        
        # Add focus area filter if specified (preferred for category-level filtering)
        if focus_area_filter:
            conditions.append(
                FieldCondition(key="focus_area", match=MatchValue(value=focus_area_filter))
            )
            logger.info(f"Applying focus_area filter: {focus_area_filter}")

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
        
        # Filter out low-relevance results
        filtered_results = [r for r in results if r.score >= self.MIN_SCORE_THRESHOLD]
        
        if len(filtered_results) < len(results):
            logger.info(
                f"Found {len(results)} chunks, filtered to {len(filtered_results)} "
                f"(threshold={self.MIN_SCORE_THRESHOLD}, scores: {[round(r.score, 3) for r in results[:5]]})"
            )
        else:
            logger.info(f"Found {len(filtered_results)} relevant chunks (scores: {[round(r.score, 3) for r in filtered_results[:3]]})")
        
        return filtered_results
    
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
                "status": collection_info.status,
                "is_cloud": self._is_cloud
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"is_cloud": self._is_cloud}


# Global instance
_instance: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get singleton VectorStore instance."""
    global _instance
    if _instance is None:
        _instance = VectorStore()
    return _instance
