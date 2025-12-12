"""Context augmentation agent using RAG for theme analysis."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from ...schemas.rag import AugmentedContext, DocumentChunk
from ...schemas.snapshot import WebDocument
from ..rag.chunker import SemanticChunker
from ..rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class ContextAugmentationAgent:
    """RAG-based context builder for enriching theme analysis.
    
    Now supports 7-Node Self-Learning Architecture:
    - retrieve_knowledge: Recall internal memory (Node 3)
    - consolidate_memory: Ingest new knowledge (Node 5)
    """
    
    def __init__(self):
        """Initialize agent with RAG components."""
        self.vector_store = get_vector_store()
        self.chunker = SemanticChunker(
            chunk_size=400,
            chunk_overlap=100,
            min_chunk_size=50
        )
        logger.info("ContextAugmentationAgent initialized")

    async def retrieve_knowledge(
        self,
        focus_areas: list[str] | None,
        limit: int = 10
    ) -> list[WebDocument]:
        """Recall internal knowledge from memory (Vector DB).
        
        Performs targeted searches for each focus area to ensure coverage,
        rather than a single smeared query.
        
        Args:
            focus_areas: List of keywords/themes to search for
            limit: Max total number of documents to retrieve
            
        Returns:
            List of WebDocuments reconstructed from memory chunks
        """
        if not focus_areas:
            logger.info("No focus areas provided for memory recall")
            return []

        # Calculate quota per focus area (min 3 to ensure representation)
        per_area_limit = max(3, int(limit / len(focus_areas)) + 1)
        
        all_results = []
        seen_ids = set()
        
        logger.info(f"Recalling memory for {len(focus_areas)} topics (limit/topic={per_area_limit})...")
        
        for area in focus_areas:
            try:
                # OPTIMIZATION: Expand query with specific keywords if available
                # This boosts vector scores by providing dense semantic targets
                # e.g., "Health" -> "Health dengue hospital medicine outbreak"
                from ..insights.agent_tools import FOCUS_CONCERN_KEYWORDS
                
                # Normalize key lookup
                normalized_area = area.lower()
                # Find matching key in keywords dict (handling case variations)
                rich_keywords = []
                for k, v in FOCUS_CONCERN_KEYWORDS.items():
                    if k.lower() == normalized_area or k.lower() in normalized_area:
                        rich_keywords = v
                        break
                
                if rich_keywords:
                    # Construct dense query
                    query_text = f"{area} {' '.join(rich_keywords)}"
                    logger.debug(f"Expanded memory query '{area}' -> '{query_text}'")
                else:
                    query_text = area

                # Search for specific topic with enhanced query
                results = await self.vector_store.search(query=query_text, k=per_area_limit)
                
                # Add unique results
                added_count = 0
                for res in results:
                    if res.chunk.chunk_id not in seen_ids:
                        seen_ids.add(res.chunk.chunk_id)
                        all_results.append(res)
                        added_count += 1
                
                logger.debug(f"Memory recall for '{area}': found {len(results)}, added {added_count} unique")
                
            except Exception as e:
                logger.warning(f"Memory recall failed for topic '{area}': {e}")

        # Reconstruct WebDocuments
        documents = []
        for result in all_results:
            chunk = result.chunk
            
            # Reconstruct metadata
            meta = chunk.metadata.copy()
            meta["_score"] = result.score
            meta["_source_type"] = "memory_recall"
            
            doc = WebDocument(
                title=chunk.source_title or meta.get("title", "Recalled Memory"),
                snippet=chunk.content,
                url=chunk.source_url or meta.get("url"),
                published_at=datetime.fromisoformat(meta["created_at"]) if meta.get("created_at") else None,
                sentiment=meta.get("sentiment"),
                metadata=meta
            )
            documents.append(doc)
            
        # Sort by score descending (if scores comparable) or just shuffle?
        # Since we queried different topics, scores might vary in scale if unnormalized, 
        # but usually cosine is 0-1. Let's sort to keep best quality.
        documents.sort(key=lambda d: d.metadata.get("_score", 0), reverse=True)
        
        # Enforce global limit
        if len(documents) > limit:
            documents = documents[:limit]
            
        logger.info(f"Memory recall complete. Retrieved {len(documents)} unique documents across {len(focus_areas)} topics.")
        return documents

    async def consolidate_memory(self, documents: list[WebDocument]) -> int:
        """Ingest new documents into memory (Vector DB).
        
        Args:
            documents: List of fresh documents to learn
            
        Returns:
            Number of chunks stored
        """
        if not documents:
            return 0
            
        logger.info(f"Consolidating memory with {len(documents)} new documents")
        
        # 1. Chunk
        chunks = self.chunker.chunk_documents(documents)
        if not chunks:
            return 0
            
        # 2. Store
        count = await self.vector_store.add_chunks(chunks)
        logger.info(f"Learned {count} new memory chunks")
        return count
    
    async def augment_context(
        self,
        documents: list[WebDocument],
        theme: str,
        time_window: str = "24h",
        top_k: int = 10
    ) -> AugmentedContext:
        """Legacy method: Build RAG-augmented context for theme analysis.
        
        NOTE: In the new 7-Node architecture, this is split into:
        1. retrieve_knowledge (Node 3)
        2. consolidate_memory (Node 5)
        
        This method is kept for backward compatibility with the old pipeline
        logic where RAG happened AFTER analysis based on themes.
        """
        logger.info(f"Augmenting context for theme '{theme}' with {len(documents)} documents")
        
        # Step 1 & 2: Chunk & Store (Consolidate Memory)
        # We only do this if we are in the old flow where ingestion happened here
        # But to be safe and avoid double ingestion if called linearly, we'll re-implement
        # using the breakdown logic but adhering to the old interface.
        
        # In the old flow, we ingested specific theme docs? No, we ingested ALL docs
        # then retrieved by theme.
        
        chunks = self.chunker.chunk_documents(documents)
        if chunks:
            await self.vector_store.add_chunks(chunks)
        
        # Step 3: Retrieve
        theme_query = self._build_theme_query(theme)
        retrieval_results = await self.vector_store.search(
            query=theme_query,
            k=top_k
        )
        
        if not retrieval_results:
            return self._empty_context(theme)
        
        relevant_chunks = [result.chunk for result in retrieval_results]
        relevance_scores = [result.score for result in retrieval_results]
        
        # Step 4: Build temporal context
        temporal_range = self._get_temporal_range(relevant_chunks, time_window)
        
        # Step 5: Generate context summary
        context_summary = self._generate_summary(relevant_chunks, theme)
        
        return AugmentedContext(
            theme=theme,
            relevant_chunks=relevant_chunks,
            context_summary=context_summary,
            temporal_range=temporal_range,
            spatial_context="Baguio City",
            relevance_scores=relevance_scores,
            total_documents=len(documents)
        )
    
    def _build_theme_query(self, theme: str) -> str:
        """Build search query using FOCUS_CONCERN_KEYWORDS for better semantic matching.
        
        Args:
            theme: Theme label
            
        Returns:
            Optimized search query using actual concern keywords
        """
        from ..insights.agent_tools import FOCUS_CONCERN_KEYWORDS
        
        # Map theme labels to focus area keys
        theme_to_focus = {
            "Health & Wellness": "health",
            "Public Safety": "safety",
            "Infrastructure": "infrastructure",
            "Environment": "environment",
            "Tourism & Events": "tourism",
            "Business & Economy": "economy",
        }
        
        focus_key = theme_to_focus.get(theme)
        
        if focus_key and focus_key in FOCUS_CONCERN_KEYWORDS:
            # Use actual concern keywords for better semantic matching
            keywords = FOCUS_CONCERN_KEYWORDS[focus_key]
            # Join all keywords for comprehensive query
            return " ".join(keywords)
        
        # Fallback for unknown themes
        return f"Baguio City {theme} news updates issues concerns"
    
    def _get_temporal_range(
        self, 
        chunks: list[DocumentChunk],
        time_window: str
    ) -> tuple[datetime, datetime] | None:
        """Extract temporal range from chunks.
        
        Args:
            chunks: Document chunks
            time_window: Time window specification
            
        Returns:
            Tuple of (earliest, latest) datetime, or None if no dates
        """
        dates = [chunk.published_at for chunk in chunks if chunk.published_at]
        
        if not dates:
            return None
        
        return (min(dates), max(dates))
    
    def _generate_summary(self, chunks: list[DocumentChunk], theme: str) -> str:
        """Generate condensed summary of context.
        
        Args:
            chunks: Relevant chunks
            theme: Theme label
            
        Returns:
            Context summary string
        """
        if not chunks:
            return f"No relevant context found for {theme}."
        
        # Get top 3 chunks
        top_chunks = chunks[:3]
        sources = {chunk.source_title for chunk in top_chunks}
        
        summary = (
            f"Context for {theme}: "
            f"{len(chunks)} relevant passages from {len(sources)} sources. "
            f"Key topics: {', '.join(c.content[:50] + '...' for c in top_chunks[:2])}"
        )
        
        return summary[:300]
    
    def _empty_context(self, theme: str) -> AugmentedContext:
        """Create empty context when no data found.
        
        Args:
            theme: Theme label
            
        Returns:
            Empty augmented context
        """
        return AugmentedContext(
            theme=theme,
            relevant_chunks=[],
            context_summary=f"No relevant context found for {theme}.",
            temporal_range=None,
            spatial_context="Baguio City",
            relevance_scores=[],
            total_documents=0
        )
    
    async def clear_cache(self):
        """Clear vector store cache."""
        await self.vector_store.clear()
        logger.info("Context cache cleared")
