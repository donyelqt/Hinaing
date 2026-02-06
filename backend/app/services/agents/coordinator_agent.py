"""Coordinator Agent for final narrative generation and response assembly.

This agent is responsible for Node 7 of the 7-Node Self-Learning Pipeline:
- Receives theme insights from the 6 Theme Agents
- Generates a comprehensive narrative summary using Groq LLMs
- Assembles the final SnapshotResponse
"""
from __future__ import annotations

import logging
from typing import Any

from ..nlp.gemini import LLMNarrativeClient, llm_narrative_client

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """Agent that coordinates final response generation.
    
    Wraps LLMNarrativeClient to provide a consistent agent interface for Node 7.
    Uses Groq's llama-4-scout-17b for comprehensive narrative generation.
    """
    
    def __init__(self, client: LLMNarrativeClient | None = None):
        """Initialize the coordinator agent.
        
        Args:
            client: Optional LLMNarrativeClient instance. Uses global singleton if not provided.
        """
        self._client = client or llm_narrative_client
        logger.info("CoordinatorAgent initialized")
    
    @property
    def is_available(self) -> bool:
        """Check if the underlying LLM is available."""
        return self._client.is_available
    
    async def run(
        self,
        window: str,
        focus_areas: list[str] | None,
        documents: list[dict[str, Any]],
        theme_insights: list[dict[str, Any]] | None = None,
    ) -> tuple[str | None, list[dict[str, str]]]:
        """Generate narrative summary and insights.
        
        Args:
            window: Time window for the analysis (e.g., "24h", "7d")
            focus_areas: List of focus areas being analyzed
            documents: List of enriched documents with sentiment/credibility
            theme_insights: Optional pre-generated theme insights
            
        Returns:
            Tuple of (narrative_summary, insights_list)
        """
        logger.info(
            "[CoordinatorAgent] Generating narrative",
            extra={
                "window": window,
                "focus_areas": focus_areas,
                "doc_count": len(documents),
                "theme_insights_count": len(theme_insights) if theme_insights else 0,
            }
        )
        
        if not self.is_available:
            logger.warning("[CoordinatorAgent] LLM not available, returning None")
            return None, []
        
        try:
            summary, insights = await self._client.analyze_snapshot(
                window=window,
                focus_areas=focus_areas,
                documents=documents,
                theme_insights=theme_insights, # Pass summarized insights
            )
            logger.info("[CoordinatorAgent] Narrative generation complete")
            return summary, insights
        except Exception as exc:
            logger.exception("[CoordinatorAgent] Failed to generate narrative: %s", exc)
            return None, []


# Global singleton instance
_coordinator_agent: CoordinatorAgent | None = None


def get_coordinator_agent() -> CoordinatorAgent:
    """Get singleton CoordinatorAgent instance."""
    global _coordinator_agent
    if _coordinator_agent is None:
        _coordinator_agent = CoordinatorAgent()
    return _coordinator_agent
