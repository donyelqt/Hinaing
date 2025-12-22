"""Semantic Theme Router Agent - Routes documents to themes using embeddings + keywords."""
from __future__ import annotations

import logging
from typing import Any

from ...schemas.snapshot import SnapshotRequest, WebDocument
from ..rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class SemanticThemeRouterAgent:
    """Agent that routes documents to themes using semantic similarity + keyword fallback.
    
    Strategy:
    1. Compute embeddings for each theme (from keywords + description)
    2. Compute embeddings for each document (title + snippet)
    3. Route document to theme with highest cosine similarity (if > threshold)
    4. Fall back to keyword matching for edge cases
    """
    
    def __init__(self, theme_groups: dict[str, dict[str, Any]]):
        """Initialize with theme configuration.
        
        Args:
            theme_groups: Dict mapping theme keys to metadata (keywords, label, focus_values)
        """
        self.theme_groups = theme_groups
        self.embedding_service = get_embedding_service()
        self._theme_embeddings: dict[str, list[float]] | None = None
        self._similarity_threshold = 0.35  # Tune based on testing
        
    def _compute_theme_embeddings(self) -> dict[str, list[float]]:
        """Compute embeddings for each theme based on keywords and description."""
        if self._theme_embeddings is not None:
            return self._theme_embeddings
            
        theme_texts = {}
        for key, meta in self.theme_groups.items():
            # Combine keywords and label into representative text
            keywords = meta.get("keywords", [])
            label = meta.get("label", key)
            
            # Convert to list if it's a set (sets aren't subscriptable)
            if isinstance(keywords, set):
                keywords = list(keywords)
            
            # Create rich theme description
            theme_text = f"{label}. Topics: {', '.join(keywords[:10])}"
            theme_texts[key] = theme_text
        
        # Batch embed all themes
        texts = list(theme_texts.values())
        embeddings = self.embedding_service.embed_batch(texts)
        
        self._theme_embeddings = {
            key: embeddings[i] 
            for i, key in enumerate(theme_texts.keys())
        }
        
        logger.info(f"[SemanticThemeRouter] Computed embeddings for {len(self._theme_embeddings)} themes")
        return self._theme_embeddings
    
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _keyword_match(self, doc: WebDocument, theme_key: str) -> bool:
        """Fallback keyword matching for edge cases."""
        meta = self.theme_groups.get(theme_key, {})
        keywords = meta.get("keywords", [])
        
        # Convert set to list if needed
        if isinstance(keywords, set):
            keywords = list(keywords)
        
        content = f"{doc.title} {doc.snippet} {str(doc.url)}".lower()
        
        for kw in keywords:
            if kw.lower() in content:
                return True
        
        return False
    
    def run(
        self, 
        documents: list[WebDocument], 
        request: SnapshotRequest
    ) -> dict[str, list[WebDocument]]:
        """Route documents to themes using semantic similarity.
        
        Args:
            documents: List of documents to route
            request: Request containing focus_areas to filter active themes
            
        Returns:
            Dict mapping theme keys to lists of documents
        """
        logger.info(
            f"[SemanticThemeRouter] Routing {len(documents)} documents for focus areas {request.focus_areas}"
        )
        
        # Initialize result dict
        theme_docs: dict[str, list[WebDocument]] = {
            key: [] for key in self.theme_groups.keys()
        }
        
        # Determine active themes based on focus_areas
        focus_values = {f.lower() for f in (request.focus_areas or [])}
        active_themes = set()
        
        for key, meta in self.theme_groups.items():
            theme_focus = set(meta.get("focus_values", set()))
            if focus_values & theme_focus:
                active_themes.add(key)
        
        if not active_themes:
            logger.warning("[SemanticThemeRouter] No active themes, returning empty routing")
            return theme_docs
        
        # Compute theme embeddings (cached after first call)
        theme_embeddings = self._compute_theme_embeddings()
        
        # Batch embed all documents
        doc_texts = [
            f"{doc.title}. {doc.snippet[:200]}" 
            for doc in documents
        ]
        doc_embeddings = self.embedding_service.embed_batch(doc_texts)
        
        # Route each document
        semantic_routed = 0
        keyword_routed = 0
        
        for doc, doc_embedding in zip(documents, doc_embeddings):
            # Compute similarity to each active theme
            best_theme = None
            best_score = self._similarity_threshold
            
            for theme_key in active_themes:
                theme_embedding = theme_embeddings[theme_key]
                similarity = self._cosine_similarity(doc_embedding, theme_embedding)
                
                if similarity > best_score:
                    best_score = similarity
                    best_theme = theme_key
            
            # Route to best matching theme
            if best_theme:
                theme_docs[best_theme].append(doc)
                semantic_routed += 1
            else:
                # Fallback: Try keyword matching for any active theme
                for theme_key in active_themes:
                    if self._keyword_match(doc, theme_key):
                        theme_docs[theme_key].append(doc)
                        keyword_routed += 1
                        break
        
        # Log routing stats
        stats = {k: len(v) for k, v in theme_docs.items() if v}
        logger.info(
            f"[SemanticThemeRouter] Routed {semantic_routed} docs via semantic, "
            f"{keyword_routed} via keywords. Distribution: {stats}"
        )
        
        return theme_docs


def get_theme_router_agent(theme_groups: dict[str, dict[str, Any]]) -> SemanticThemeRouterAgent:
    """Factory function to create theme router agent."""
    return SemanticThemeRouterAgent(theme_groups)
