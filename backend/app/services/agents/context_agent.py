"""Context augmentation agent using RAG for theme analysis."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from ...schemas.rag import AugmentedContext, DocumentChunk
from ...schemas.snapshot import WebDocument
from ..rag.chunker import SemanticChunker
from ..rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class ContextAugmentationAgent:
    """RAG-based context builder for enriching theme analysis."""
    
    def __init__(self):
        """Initialize agent with RAG components."""
        self.vector_store = VectorStore()
        self.chunker = SemanticChunker(
            chunk_size=400,
            chunk_overlap=100,
            min_chunk_size=50
        )
        logger.info("ContextAugmentationAgent initialized")
    
    async def augment_context(
        self,
        documents: list[WebDocument],
        theme: str,
        time_window: str = "24h",
        top_k: int = 10
    ) -> AugmentedContext:
        """Build RAG-augmented context for theme analysis.
        
        Process:
        1. Chunk documents semantically
        2. Embed and store chunks in Qdrant
        3. Retrieve top-k most relevant chunks for theme
        4. Build temporal/spatial context window
        5. Generate context summary
        
        Args:
            documents: Source documents to process
            theme: Theme to focus on (e.g., "Health & Wellness")
            time_window: Time window filter (e.g., "24h", "7d")
            top_k: Number of top chunks to retrieve
            
        Returns:
            Augmented context with relevant chunks and metadata
        """
        logger.info(f"Augmenting context for theme '{theme}' with {len(documents)} documents")
        
        # Step 1: Chunk documents
        chunks = self.chunker.chunk_documents(documents)
        if not chunks:
            logger.warning(f"No chunks created for theme '{theme}'")
            return self._empty_context(theme)
        
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        
        # Step 2: Add chunks to vector store
        await self.vector_store.add_chunks(chunks)
        
        # Step 3: Retrieve relevant chunks using theme-specific query
        theme_query = self._build_theme_query(theme)
        retrieval_results = await self.vector_store.search(
            query=theme_query,
            k=top_k
        )
        
        if not retrieval_results:
            logger.warning(f"No relevant chunks found for theme '{theme}'")
            return self._empty_context(theme)
        
        relevant_chunks = [result.chunk for result in retrieval_results]
        relevance_scores = [result.score for result in retrieval_results]
        
        logger.info(
            f"Retrieved {len(relevant_chunks)} chunks for '{theme}' "
            f"(avg score: {sum(relevance_scores)/len(relevance_scores):.3f})"
        )
        
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
        """Build search query optimized for theme with Baguio-specific keywords.
        
        Args:
            theme: Theme label
            
        Returns:
            Optimized search query with local context
        """
        # Theme-specific query templates with Baguio-specific terms
        theme_queries = {
            "Health & Wellness": (
                "Baguio hospital health disease clinic medical sanitation "
                "Baguio General Hospital BGH wellness hygiene outbreak "
                "BGH substandard construction building defect hospital facility"
            ),
            "Public Safety": (
                "Baguio crime police fire accident emergency landslide flood "
                "Kennon Road accident safety disaster rescue security "
                "student walkout protest rally school incident demonstration"
            ),
            "Infrastructure": (
                "Baguio road traffic water power pothole Session Road "
                "Kennon Road Marcos Highway jeepney garbage infrastructure "
                "construction utility building BENECO water district"
            ),
            "Environment": (
                "Baguio pollution air quality waste flooding landslide "
                "environmental drainage climate pine trees deforestation"
            ),
            "Tourism & Events": (
                "Baguio tourist Panagbenga Burnham Park Camp John Hay "
                "Mines View Wright Park overcrowding hotel festival "
                "Summer Capital City of Pines tourism visitor"
            ),
            "Business & Economy": (
                "Baguio vendor market business livelihood employment "
                "public market mallification SM Prime redevelopment PPP "
                "vendor displacement economy trade commerce "
                "student walkout protest mallification anti-mall"
            ),
        }
        
        return theme_queries.get(theme, f"Baguio City {theme} news updates issues concerns")
    
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
