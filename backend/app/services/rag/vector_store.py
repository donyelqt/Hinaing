"""Qdrant vector store for RAG document retrieval.

HYBRID SEARCH IMPLEMENTATION (Dense + Sparse):
- Dense: BGE-large embeddings (semantic similarity)
- Sparse: BM25 keyword matching (traditional IR)
- Fusion: Reciprocal Rank Fusion (RRF) for combining scores

Supports both:
- Qdrant Cloud (recommended): Set QDRANT_URL and QDRANT_API_KEY in .env
- Local disk storage (fallback): Uses ./qdrant_data folder
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25Okapi = None
    BM25_AVAILABLE = False
    import sys
    print("[VectorStore] rank_bm25 not available, using dense-only search", file=sys.stderr)

from ...core.config import get_settings
from ...schemas.rag import DocumentChunk, RetrievalResult
from .embeddings import get_embedding_service

settings = get_settings()

# Hybrid search configuration
HYBRID_RRF_K = 60  # RRF parameter (standard is 60)
BM25_WEIGHT = 0.3   # Weight for BM25 scores
DENSE_WEIGHT = 0.7  # Weight for dense scores


class VectorStore:
    """Manages document embeddings and similarity search using Qdrant.
    
    Supports HYBRID search (Dense + Sparse):
    - Dense: BGE-large embeddings (1024d)
    - Sparse: BM25 keyword matching
    - Fusion: Reciprocal Rank Fusion (RRF)
    """
    
    COLLECTION_NAME = "baguio_documents"
    MIN_SCORE_THRESHOLD = 0.30  # Lowered for hybrid RRF (fused scores are naturally lower)
    
    def __init__(self):
        """Initialize Qdrant client (Cloud or local) with BM25."""
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
                timeout=30.0,
            )
            self._is_cloud = True
        else:
            logger.info("[VectorStore] Using local Qdrant storage (qdrant_data/)")
            self.client = QdrantClient(
                path="qdrant_data",
                timeout=30.0,
            )
            self._is_cloud = False
        
        self.embedding_service = get_embedding_service()
        
        # BM25 index (built on-demand)
        # Type is Any because BM25Okapi may not be available at runtime
        self._bm25_index: Any = None
        self._bm25_corpus: list[str] = []
        self._bm25_doc_ids: list[int] = []
        
        self._ensure_collection()
        logger.info(f"[VectorStore] Initialized (cloud={self._is_cloud}, hybrid=DENSE+BM25)")
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist, ensure indexes."""
        try:
            collections = self.client.get_collections()
            collection_exists = any(c.name == self.COLLECTION_NAME for c in collections.collections)
            
            if not collection_exists:
                # Create with explicit vector config
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.embedding_service.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"[VectorStore] Created collection: {self.COLLECTION_NAME}")
            else:
                # Check if collection has valid vectors - if not, recreate
                # FIXED: Also check points_count to verify vectors actually exist
                try:
                    collection_info = self.client.get_collection(self.COLLECTION_NAME)
                    vectors_config = getattr(collection_info, 'vectors_config', None)
                    points_count = getattr(collection_info, 'points_count', 0)
                    
                    has_vectors = False
                    if vectors_config:
                        if hasattr(vectors_config, 'size'):  # Single vector config
                            has_vectors = True
                        elif isinstance(vectors_config, dict) and vectors_config:
                            has_vectors = True
                    
                    # CRITICAL FIX: Don't delete if there are points stored!
                    # Even if vectors_config is missing, existing points mean vectors exist
                    if points_count > 0:
                        has_vectors = True
                        logger.info(f"[VectorStore] Collection has {points_count} points - preserving data")
                    
                    if not has_vectors:
                        logger.warning(f"[VectorStore] Collection {self.COLLECTION_NAME} has no vectors config AND no points, recreating...")
                        self.client.delete_collection(self.COLLECTION_NAME)
                        self.client.create_collection(
                            collection_name=self.COLLECTION_NAME,
                            vectors_config=VectorParams(
                                size=self.embedding_service.embedding_dim,
                                distance=Distance.COSINE
                            )
                        )
                        logger.info(f"[VectorStore] Recreated collection: {self.COLLECTION_NAME}")
                except Exception as check_err:
                    logger.warning(f"[VectorStore] Could not check vector config: {check_err}")
            
            # Ensure payload indexes exist for filtering
            self._ensure_payload_indexes()
            
        except Exception as e:
            logger.error(f"[VectorStore] Failed to ensure collection: {e}")
            raise
    
    def _ensure_payload_indexes(self):
        """Create payload indexes for filterable fields."""
        from qdrant_client.models import PayloadSchemaType
        
        index_fields = ["focus_area", "topic", "published_at"]
        
        for field in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD if field != "published_at" else PayloadSchemaType.DATETIME,
                    wait=True,
                )
                logger.info(f"[VectorStore] ✓ Created index for '{field}'")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg or "exist" in error_msg:
                    logger.debug(f"[VectorStore] Index '{field}' already exists (OK)")
                else:
                    logger.warning(f"[VectorStore] Index creation warning for '{field}': {e}")
    
    def _rebuild_bm25_index(self, max_docs: int = 10000):
        """Rebuild BM25 index from Qdrant documents.
        
        Called when:
        - New documents are added
        - Search is performed (lazy rebuild)
        
        Args:
            max_docs: Maximum documents to index (for performance)
        """
        if not BM25_AVAILABLE:
            logger.debug("[VectorStore] BM25 not available, skipping index rebuild")
            return
        
        try:
            # Get all documents from Qdrant
            scroll_result = self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                limit=max_docs,
                with_payload=True,
                with_vectors=False,
            )
            
            points = scroll_result[0] if isinstance(scroll_result, tuple) else scroll_result.points
            
            if not points:
                logger.debug("[VectorStore] No documents to index for BM25")
                return
            
            # Build BM25 corpus
            self._bm25_corpus = []
            self._bm25_doc_ids = []
            
            for point in points:
                if point.payload and point.payload.get("content"):
                    # Tokenize content for BM25
                    content = point.payload["content"].lower()
                    tokens = content.split()  # Simple whitespace tokenization
                    self._bm25_corpus.append(tokens)
                    self._bm25_doc_ids.append(point.id)
            
            if self._bm25_corpus:
                self._bm25_index = BM25Okapi(self._bm25_corpus)
                logger.info(f"[VectorStore] BM25 index built with {len(self._bm25_corpus)} documents")
                
        except Exception as e:
            logger.warning(f"[VectorStore] Failed to rebuild BM25 index: {e}")
            self._bm25_index = None
    
    def _bm25_search(self, query: str, k: int = 20) -> list[tuple[int, float]]:
        """Search using BM25.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of (doc_id, bm25_score) tuples
        """
        if not BM25_AVAILABLE:
            return []
        
        # Rebuild index if needed
        if self._bm25_index is None:
            self._rebuild_bm25_index()
        
        if self._bm25_index is None:
            return []
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self._bm25_index.get_scores(query_tokens)
        
        # Get top-k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self._bm25_doc_ids[idx], scores[idx]))
        
        return results
    
    def _normalize_bm25_scores(self, scores: list[float]) -> list[float]:
        """Normalize BM25 scores to 0-1 range using max scaling."""
        if not scores or max(scores) == 0:
            return scores
        
        max_score = max(scores)
        return [s / max_score for s in scores]
    
    def _reciprocal_rank_fusion(
        self, 
        dense_results: list[tuple[int, float]], 
        sparse_results: list[tuple[int, float]],
        k: int = 60
    ) -> list[tuple[int, float]]:
        """Combine dense and sparse results using RRF.
        
        RRF formula: 1 / (k + rank)
        
        Args:
            dense_results: List of (doc_id, score) from dense search
            sparse_results: List of (doc_id, score) from BM25
            k: RRF parameter (default 60)
            
        Returns:
            Combined list of (doc_id, fused_score) sorted by score
        """
        rrf_scores: dict[int, float] = {}
        
        # Add dense scores with RRF
        for rank, (doc_id, score) in enumerate(dense_results):
            rrf = 1.0 / (k + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + DENSE_WEIGHT * rrf * score
        
        # Add sparse scores with RRF
        for rank, (doc_id, score) in enumerate(sparse_results):
            rrf = 1.0 / (k + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + BM25_WEIGHT * rrf * score
        
        # Sort by combined score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_results
    
    async def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Embed and store document chunks with BM25 indexing.
        
        Args:
            chunks: List of document chunks to store
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        logger.info(f"Adding {len(chunks)} chunks to vector store (hybrid: dense + BM25)")
        
        # Generate dense embeddings
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_batch(chunk_texts)
        
        # Create Qdrant points
        points: list[PointStruct] = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(
                PointStruct(
                    id=hash(chunk.chunk_id) % (10 ** 8),
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
                        "metadata": chunk.metadata,
                        "created_at": datetime.now(timezone.utc).isoformat(),  # For TTL
                    }
                )
            )
        
        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )
        
        # Rebuild BM25 index with new documents
        self._rebuild_bm25_index()
        
        # Log distribution
        topics = [p.payload.get("topic", "unknown") for p in points if p.payload]
        focus_areas = [p.payload.get("focus_area", "unknown") for p in points if p.payload]
        topic_counts = {}
        focus_counts = {}
        for t in topics:
            topic_counts[t] = topic_counts.get(t, 0) + 1
        for f in focus_areas:
            focus_counts[f] = focus_counts.get(f, 0) + 1
        logger.info(f"Successfully added {len(points)} chunks (focus_areas: {focus_counts})")
        return len(points)
    
    async def search(
        self, 
        query: str, 
        k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
        topic_filter: str | None = None,
        focus_area_filter: str | None = None
    ) -> list[RetrievalResult]:
        """Hybrid search combining dense (semantic) + sparse (BM25) results.
        
        Uses Reciprocal Rank Fusion to combine both signals.
        
        Args:
            query: Search query
            k: Number of top results to return
            filter_metadata: Optional metadata filters
            topic_filter: Optional topic to filter by
            focus_area_filter: Optional focus area to filter by
            
        Returns:
            List of retrieval results with chunks and fused scores
        """
        logger.info(f"Hybrid search: '{query[:80]}...' (k={k})")
        
        # Build filter conditions
        conditions = []
        if filter_metadata:
            for key, value in filter_metadata.items():
                conditions.append(
                    FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value))
                )
        
        if topic_filter:
            conditions.append(
                FieldCondition(key="topic", match=MatchValue(value=topic_filter))
            )
        
        if focus_area_filter:
            conditions.append(
                FieldCondition(key="focus_area", match=MatchValue(value=focus_area_filter))
            )

        query_filter = Filter(must=conditions) if conditions else None
        
        # Get dense (semantic) results
        query_embedding = self.embedding_service.embed_query(query)
        
        try:
            dense_response = self.client.query_points(
                collection_name=self.COLLECTION_NAME,
                query=query_embedding,
                limit=k * 3,  # Get more for fusion
                with_payload=True,
                query_filter=query_filter,
            )
            dense_hits = getattr(dense_response, "points", dense_response) or []
            dense_results = [(hit.id, hit.score) for hit in dense_hits]
        except Exception as e:
            logger.warning(f"[VectorStore] Dense search failed: {e}")
            dense_results = []
        
        # Get sparse (BM25) results
        try:
            sparse_results = self._bm25_search(query, k=k * 3)
            
            # Normalize BM25 scores
            if sparse_results:
                bm25_scores = [s for _, s in sparse_results]
                normalized = self._normalize_bm25_scores(bm25_scores)
                sparse_results = [(doc_id, normalized[i]) for i, (doc_id, _) in enumerate(sparse_results)]
                
        except Exception as e:
            logger.warning(f"[VectorStore] BM25 search failed: {e}")
            sparse_results = []
        
        # Fuse results using RRF
        if dense_results and sparse_results:
            fused_results = self._reciprocal_rank_fusion(dense_results, sparse_results, k=HYBRID_RRF_K)
        elif dense_results:
            fused_results = dense_results[:k]
        elif sparse_results:
            fused_results = sparse_results[:k]
        else:
            fused_results = []
        
        # Log fusion details for observability
        if fused_results:
            top_scores = [s for _, s in fused_results[:3]]
            logger.info(f"[VectorStore] RRF fusion: top scores = {top_scores}, min threshold = {self.MIN_SCORE_THRESHOLD}")
        
        # Get full document details for top-k fused results
        if fused_results:
            # Fetch documents by ID
            doc_ids = [doc_id for doc_id, _ in fused_results[:k]]
            
            try:
                points_response = self.client.retrieve(
                    collection_name=self.COLLECTION_NAME,
                    ids=doc_ids,
                    with_payload=True,
                )
                
                # Create ID to payload mapping
                id_to_payload = {p.id: p.payload for p in points_response}
                
                # Build results in fused order
                results: list[RetrievalResult] = []
                for rank, (doc_id, fused_score) in enumerate(fused_results[:k]):
                    payload = id_to_payload.get(doc_id)
                    if not payload:
                        continue
                    
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
                        embedding=None
                    )
                    
                    results.append(
                        RetrievalResult(
                            chunk=chunk,
                            score=fused_score,
                            rank=rank + 1
                        )
                    )
                
                logger.info(f"Hybrid search: {len(results)} results (dense={len(dense_results)}, bm25={len(sparse_results)})")
                
                # Log filtering stats
                if fused_results:
                    passed = len(results)
                    total = len(fused_results)
                    logger.info(f"[VectorStore] Score filtering: {passed}/{total} passed threshold {self.MIN_SCORE_THRESHOLD}")
                
                return results
                
            except Exception as e:
                logger.warning(f"[VectorStore] Failed to retrieve fused results: {e}")
        
        # Fallback to dense-only
        return await self._dense_only_search(query, k, query_filter)
    
    async def _dense_only_search(
        self, 
        query: str, 
        k: int, 
        query_filter: Filter | None
    ) -> list[RetrievalResult]:
        """Fallback: dense-only search when hybrid fails."""
        query_embedding = self.embedding_service.embed_query(query)
        
        try:
            response = self.client.query_points(
                collection_name=self.COLLECTION_NAME,
                query=query_embedding,
                limit=k,
                with_payload=True,
                query_filter=query_filter,
            )
            hits = getattr(response, "points", response) or []
        except Exception as e:
            logger.error(f"[VectorStore] Dense-only search failed: {e}")
            return []
        
        results: list[RetrievalResult] = []
        for rank, hit in enumerate(hits):
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
                embedding=None
            )
            
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=hit.score,
                    rank=rank + 1
                )
            )
        
        return [r for r in results if r.score >= self.MIN_SCORE_THRESHOLD]
    
    async def clear(self):
        """Clear all documents from the collection."""
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
            self._bm25_index = None
            self._bm25_corpus = []
            self._bm25_doc_ids = []
            self._ensure_collection()
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
    
    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        try:
            collection_info = self.client.get_collection(self.COLLECTION_NAME)
            return {
                "name": self.COLLECTION_NAME,
                "vector_count": collection_info.points_count,
                "vector_dim": self.embedding_service.embedding_dim,
                "status": collection_info.status,
                "is_cloud": self._is_cloud,
                "hybrid_search": True,
                "bm25_indexed": self._bm25_index is not None,
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"is_cloud": self._is_cloud}
    
    def recreate_indexes(self):
        """Manually recreate payload indexes."""
        logger.info("[VectorStore] Manually recreating payload indexes...")
        self._ensure_payload_indexes()
        logger.info("[VectorStore] Index recreation complete")


# Global instance
_instance: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get singleton VectorStore instance."""
    global _instance
    if _instance is None:
        _instance = VectorStore()
    return _instance
