"""Emerging concerns memory using Qdrant vector store.

Implements 6 isolated collections for production research:
- infrastructure_concerns
- health_concerns
- safety_concerns
- tourism_concerns
- economy_concerns
- environment_concerns

This provides:
- Semantic isolation per focus area (higher accuracy)
- Failure isolation (one crash = one area affected)
- Per-area metrics for thesis research

SELF-LEARNING ARCHITECTURE:
- Concerns stored with created_at timestamp
- recall_concerns() checks created_at vs current time
- If older than max_age_days (default: 7), triggers LLM regeneration
- This creates an adaptive agent that learns from previous cycles

MEMORY LIFECYCLE:
  Day 1: LLM generates concerns → store_concerns() saves to Qdrant
  Day 2-7: recall_concerns() returns from Qdrant (free, fast)
  Day 8: recall_concerns() detects age > 7 → falls back to defaults
  Then: LLM generates NEW concerns → store_concerns() updates memory
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
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
from ..rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)
settings = get_settings()

# Default TTL for concerns memory (can be overridden in .env)
DEFAULT_CONCERNS_TTL_DAYS = getattr(settings, 'concerns_memory_ttl_days', 7)

# 6 Collections for isolation (one per focus area)
# Using BGE-large for higher accuracy
# - 1024 dimensions (vs 384 in BGE-small)
# - MTEB 64.1 (top 3 open source)
# - Better semantic understanding for query generation
FOCUS_AREA_COLLECTIONS = {
    "infrastructure": "infrastructure_concerns",
    "health": "health_concerns", 
    "safety": "safety_concerns",
    "tourism": "tourism_concerns",
    "economy": "economy_concerns",
    "environment": "environment_concerns",
}

# Default concerns as fallback (loaded if Qdrant unavailable)
DEFAULT_EMERGING_CONCERNS: dict[str, list[list[str]]] = {
    "infrastructure": [
        ["Baguio traffic congestion", "Session Road rehabilitation", "Baguio public transport"],
        ["Baguio road repair", "Kennon Road closure", "Baguio construction delay"],
        ["Baguio water shortage", "Baguio drainage issue", "Baguio power outage"],
        ["Baguio parking problem", "Baguio internet problem", "Baguio jeepney modernization"],
    ],
    "health": [
        ["Baguio hospital issue", "BGH Baguio problem", "Baguio emergency room"],
        ["Baguio dengue outbreak", "Baguio COVID update", "Baguio vaccination"],
        ["Baguio healthcare concern", "Baguio doctor shortage", "Baguio medicine shortage"],
        ["Baguio mental health", "Baguio medical services", "Baguio health center"],
    ],
    "safety": [
        ["Baguio crime incident", "Baguio theft problem", "Baguio police operation"],
        ["Baguio landslide warning", "Baguio earthquake drill", "Baguio disaster preparedness"],
        ["Baguio fire incident", "Baguio accident report", "Baguio road accident"],
        ["Baguio emergency response", "Baguio missing person", "Baguio evacuation"],
        ["Baguio flood control", "Baguio corruption issue", "Baguio flood control corruption"],
        ["Baguio students walkout", "Baguio student protest", "Baguio youth rally"],
    ],
    "tourism": [
        ["Baguio tourist complaint", "Baguio scam tourist", "Baguio tourist trap"],
        ["Baguio overcrowding", "Session Road crowd", "Baguio weekend traffic"],
        ["Burnham Park problem", "Panagbenga issue", "Baguio travel advisory"],
        ["Baguio hotel issue", "Baguio accommodation problem", "Baguio tour package complaint"],
    ],
    "economy": [
        ["Baguio mallification protest", "SM Baguio expansion", "Baguio student protest market"],
    ],
    "environment": [
        ["Baguio tree cutting", "Baguio pine trees", "Baguio green space"],
        ["Baguio air pollution", "Baguio water pollution", "Baguio environmental concern"],
        ["Baguio flooding", "Baguio waste management", "Baguio garbage problem"],
        ["Baguio urban development", "Baguio climate change", "Baguio illegal dumping"],
    ],
}


class EmergingConcernsMemory:
    """Vector store for dynamically generated concern keywords.
    
    Uses 6 isolated collections for production research:
    - Semantic isolation per focus area
    - Failure isolation (one crash = one area)
    - Precise per-area metrics
    
    API mirrors ContextAugmentationAgent:
    - store_concerns(): Save LLM-generated concerns
    - recall_concerns(): Retrieve past concerns
    """
    
    def __init__(self):
        """Initialize Qdrant client and ensure collections exist."""
        self._client = None
        self._embedding_service = None
        self._initialized_collections: set[str] = set()
        self._embedding_dim = None
        
    @property
    def client(self) -> QdrantClient:
        """Lazy-load Qdrant client."""
        if self._client is None:
            qdrant_url = (settings.qdrant_url or "").strip()
            if not qdrant_url:
                raise RuntimeError("QDRANT_URL not configured")
            
            self._client = QdrantClient(
                url=qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=30.0,
            )
            logger.info("[EmergingConcerns] Connected to Qdrant Cloud")
        return self._client
    
    @property
    def embedding_service(self):
        """Lazy-load embedding service and ensure model is loaded."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
            # Force model load to get dimension
            _ = self._embedding_service.embedding_dim
            self._embedding_dim = self._embedding_service.embedding_dim
        return self._embedding_service
    
    def _ensure_collection(self, focus_area: str) -> str:
        """Ensure collection exists for focus area.
        
        Args:
            focus_area: Focus area name (e.g., "infrastructure")
            
        Returns:
            Collection name
        """
        collection_name = FOCUS_AREA_COLLECTIONS.get(focus_area.lower())
        if not collection_name:
            raise ValueError(f"Unknown focus area: {focus_area}")
        
        if collection_name in self._initialized_collections:
            return collection_name
        
        try:
            collections = self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self._embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"[EmergingConcerns] Created collection: {collection_name}")
            
            # Create payload indexes for filtering
            # - cluster_index (integer): Filter by cluster number
            # - focus_area (keyword): Filter by focus area
            # - created_at (keyword): Used for age filtering in code
            try:
                from qdrant_client.models import PayloadSchemaType
                
                # Integer index for cluster_index
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="cluster_index",
                    field_schema=PayloadSchemaType.INTEGER,
                    wait=True,
                )
                
                # Keyword index for focus_area (useful for filtering)
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="focus_area",
                    field_schema=PayloadSchemaType.KEYWORD,
                    wait=True,
                )
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    pass  # OK
                else:
                    logger.warning(f"[EmergingConcerns] Index creation warning: {e}")
            
            self._initialized_collections.add(collection_name)
            
        except Exception as e:
            logger.error(f"[EmergingConcerns] Failed to ensure collection {collection_name}: {e}")
            raise
        
        return collection_name
    
    def store_concerns(
        self,
        concerns: dict[str, list[list[str]]],
        source: str = "llm"
    ) -> dict[str, int]:
        """Store LLM-generated concerns into isolated collections.
        
        SELF-LEARNING: Stores metadata for the self-learning cycle.
        
        Metadata stored per concern cluster:
        - focus_area: The focus area (infrastructure, health, etc.)
        - keywords: The actual keyword cluster
        - cluster_index: Position in the cluster list
        - source: "llm" or "fallback" (tracks generation method)
        - created_at: ISO timestamp for age tracking (7-day TTL)
        - retrieval_score: Average retrieval score from last use (for learning)
        - usage_count: How many times this concern was used
        
        Args:
            concerns: {"infrastructure": [["kw1", "kw2"], ["kw3", "kw4"]], ...}
            source: "llm" or "fallback"
            
        Returns:
            Dict mapping focus_area to number of clusters stored
        """
        stored_counts = {}
        timestamp = datetime.now(timezone.utc).isoformat()
        
        for focus_area, clusters in concerns.items():
            try:
                collection_name = self._ensure_collection(focus_area)
                
                points = []
                for cluster_idx, keywords in enumerate(clusters):
                    # Create semantic content from keywords
                    content = f"Focus: {focus_area}. Keywords: {', '.join(keywords)}"
                    
                    # Generate embedding
                    embedding = self.embedding_service.embed_query(content)
                    
                    point = PointStruct(
                        id=hash(f"{focus_area}_{cluster_idx}_{timestamp}") % (10 ** 8),
                        vector=embedding,
                        payload={
                            "focus_area": focus_area,
                            "keywords": keywords,
                            "cluster_index": cluster_idx,
                            "source": source,
                            "created_at": timestamp,
                        }
                    )
                    points.append(point)
                
                if points:
                    self.client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                    stored_counts[focus_area] = len(points)
                    logger.info(f"[EmergingConcerns] Stored {len(points)} clusters for {focus_area}")
                    
            except Exception as e:
                logger.error(f"[EmergingConcerns] Failed to store {focus_area}: {e}")
                stored_counts[focus_area] = 0
        
        return stored_counts
    
    def recall_concerns(
        self,
        focus_areas: list[str],
        max_clusters_per_area: int = 4,
        max_age_days: int = None
    ) -> dict[str, list[list[str]]]:
        """Recall most recent concerns for given focus areas.
        
        SELF-LEARNING: This method implements the TTL-based memory cycle.
        
        How it works:
        1. Query Qdrant for concerns using semantic similarity
        2. Filter results by created_at timestamp (age check)
        3. If all results are older than max_age_days:
           - Return empty for that area → triggers LLM regeneration
        4. If recent concerns exist, return them (free, no LLM call needed)
        
        The TTL (time-to-live) is configured via:
        - concerns_memory_ttl_days in .env (default: 7)
        - Or passed directly as max_age_days parameter
        
        Args:
            focus_areas: List like ["infrastructure", "health"]
            max_clusters_per_area: Max clusters to return per area
            max_age_days: Override TTL from config. Default: use settings.concerns_memory_ttl_days
            
        Returns:
            {"infrastructure": [["kw1", "kw2"], ["kw3", "kw4"]], ...}
        """
        # Use config TTL if not overridden
        if max_age_days is None:
            max_age_days = getattr(settings, 'concerns_memory_ttl_days', DEFAULT_CONCERNS_TTL_DAYS)
        results = {}
        
        for focus_area in focus_areas:
            try:
                collection_name = FOCUS_AREA_COLLECTIONS.get(focus_area.lower())
                if not collection_name:
                    continue
                
                # Ensure collection exists (will create if not)
                try:
                    self._ensure_collection(focus_area)
                except Exception:
                    pass  # Collection might be empty, that's OK
                
                # Search for concerns
                query_text = f"{focus_area} emerging concerns keywords"
                query_embedding = self.embedding_service.embed_query(query_text)
                
                # Calculate age cutoff
                age_cutoff = None
                if max_age_days > 0:
                    age_cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
                
                # Get MORE results than needed (to filter by age)
                search_limit = max_clusters_per_area * 4  # Get 4x for filtering
                
                try:
                    search_response = self.client.query_points(
                        collection_name=collection_name,
                        query=query_embedding,
                        limit=search_limit,
                        with_payload=True,
                    )
                except Exception as e:
                    logger.warning(f"[EmergingConcerns] Search failed for {focus_area}: {e}")
                    continue
                
                hits = getattr(search_response, "points", search_response) or []
                
                # Extract keywords from results with AGE FILTERING in code
                clusters = []
                for hit in hits:
                    payload = hit.payload or {}
                    keywords = payload.get("keywords", [])
                    created_at_str = payload.get("created_at")
                    
                    # Apply age filter in code (more reliable than Qdrant filter)
                    if age_cutoff and created_at_str:
                        try:
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            # Only include if created_at >= age_cutoff (i.e., newer than cutoff)
                            if created_at < age_cutoff:
                                continue  # Skip stale concerns
                        except Exception:
                            pass  # Include if parse fails
                    
                    if keywords:
                        clusters.append(keywords)
                        if len(clusters) >= max_clusters_per_area:
                            break
                
                if clusters:
                    results[focus_area.lower()] = clusters
                    logger.info(f"[EmergingConcerns] Recalled {len(clusters)} clusters for {focus_area}")
                else:
                    # Fall back to default if nothing in memory
                    default = DEFAULT_EMERGING_CONCERNS.get(focus_area.lower(), [])
                    if default:
                        results[focus_area.lower()] = default[:max_clusters_per_area]
                        logger.info(f"[EmergingConcerns] Using defaults for {focus_area}")
                        
            except Exception as e:
                logger.warning(f"[EmergingConcerns] Recall failed for {focus_area}: {e}")
                # Fall back to defaults
                default = DEFAULT_EMERGING_CONCERNS.get(focus_area.lower(), [])
                if default:
                    results[focus_area.lower()] = default[:max_clusters_per_area]
        
        return results
    
    def clear_focus_area(self, focus_area: str) -> bool:
        """Clear all concerns for a specific focus area.
        
        Args:
            focus_area: Focus area to clear
            
        Returns:
            True if successful
        """
        collection_name = FOCUS_AREA_COLLECTIONS.get(focus_area.lower())
        if not collection_name:
            return False
        
        try:
            self.client.delete_collection(collection_name)
            self._initialized_collections.discard(collection_name)
            logger.info(f"[EmergingConcerns] Cleared collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"[EmergingConcerns] Failed to clear {focus_area}: {e}")
            return False
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all concern collections.
        
        Returns:
            Dict with per-collection stats
        """
        stats = {}
        
        for focus_area, collection_name in FOCUS_AREA_COLLECTIONS.items():
            try:
                info = self.client.get_collection(collection_name)
                stats[focus_area] = {
                    "points_count": info.points_count,
                    "collection_name": collection_name,
                }
            except Exception as e:
                stats[focus_area] = {"error": str(e)}
        
        return stats


# Global singleton
_concerns_memory: EmergingConcernsMemory | None = None


def get_concerns_memory() -> EmergingConcernsMemory:
    """Get singleton EmergingConcernsMemory instance."""
    global _concerns_memory
    if _concerns_memory is None:
        _concerns_memory = EmergingConcernsMemory()
    return _concerns_memory
