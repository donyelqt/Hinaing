"""Theme-specific sub-agents for civic insight generation.

This module implements TRUE SUB-AGENTS using the Worker Pattern (dataclass with run() method).
Each domain has its own specialized agent with autonomous reasoning capabilities.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

import google.generativeai as genai

from ...core.config import get_settings
from ...schemas.snapshot import WebDocument

logger = logging.getLogger(__name__)


def sanitize_text(text: Any) -> str:
    """Remove invalid Unicode characters that break Gemini API."""
    if not text:
        return ""
    text_str = str(text)
    cleaned = re.sub(r'[\ud800-\udfff]', '', text_str)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
    cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', cleaned)
    return cleaned.strip()


# ============================================================================
# BASE THEME AGENT (Abstract Sub-Agent)
# ============================================================================

@dataclass
class BaseThemeAgent:
    """Base class for all theme-specific sub-agents.
    
    AOSE Pattern: Expert Pattern with Worker Pattern implementation.
    Each agent is autonomous and specializes in a specific civic domain.
    """
    
    theme_label: str
    theme_focus: str
    
    def _build_context(self, documents: list[dict[str, Any]]) -> str:
        """Build context string from documents."""
        doc_lines = []
        for doc in documents[:10]:
            title = sanitize_text(doc.get('title', 'Untitled'))
            snippet = sanitize_text(doc.get('snippet', ''))[:200]
            url = sanitize_text(doc.get('url', ''))
            if url:
                doc_lines.append(f"- [{title}]({url}): {snippet}")
            else:
                doc_lines.append(f"- {title}: {snippet}")
        return "\n".join(doc_lines)
    
    def _build_prompt(self, theme_label: str, focus: str, context: str, doc_count: int) -> str:
        """Build the Gemini prompt for insight generation."""
        return f"""You are a civic analyst for Baguio City.

Theme: {theme_label}
{focus}

Task: Analyze the documents below and generate EXACTLY 3 DISTINCT insights.

Documents ({doc_count} shown):
{context}

CRITICAL REQUIREMENTS:
1. Generate EXACTLY 3 insights (no more, no less)
2. Each insight must address a DIFFERENT issue or sub-topic
3. DO NOT merge unrelated problems into one insight
4. Each insight should be actionable and specific
5. Prioritize the most important/urgent issues first

Examples of DISTINCT insights for Infrastructure:
✅ GOOD:
  - Insight 1: "Traffic congestion on Kennon Road"
  - Insight 2: "Water supply interruptions in District 3"
  - Insight 3: "Parking shortage in CBD area"

❌ BAD:
  - Insight 1: "Infrastructure challenges including traffic, water, and parking" (too broad, merged)

Return ONLY valid JSON with this exact structure:
{{
  "insights": [
    {{
      "title": "First specific issue title",
      "detail": "Actionable detail under 240 characters",
      "evidence": ["actual_url_from_documents_above"]
    }},
    {{
      "title": "Second distinct issue title",
      "detail": "Actionable detail under 240 characters",
      "evidence": ["actual_url_from_documents_above"]
    }},
    {{
      "title": "Third different issue title",
      "detail": "Actionable detail under 240 characters",
      "evidence": ["actual_url_from_documents_above"]
    }}
  ]
}}

IMPORTANT:
- The "evidence" array MUST contain actual URLs from the documents above
- If documents truly lack {theme_label} content, return: {{"insights": []}}
- Generate EXACTLY 3 insights if you have sufficient content

JSON:"""
    
    def _parse_response(self, output: str, theme_label: str) -> list[dict]:
        """Parse and sanitize Gemini response."""
        # Remove markdown code blocks
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
        
        try:
            parsed = json.loads(output)
            insights = parsed.get("insights", [])
            
            sanitized = []
            for item in insights:
                if isinstance(item, dict):
                    sanitized.append({
                        "title": sanitize_text(item.get("title", f"Update in {theme_label}")),
                        "detail": sanitize_text(item.get("detail", "Context unavailable")),
                        "evidence": [sanitize_text(str(e)) for e in item.get("evidence", []) if e],
                    })
            return sanitized
        except json.JSONDecodeError:
            logger.warning(f"[{theme_label}] JSON parse failed: {output[:100]}")
            return []
    
    async def run(self, documents: list[dict[str, Any]]) -> list[dict]:
        """Execute the sub-agent's autonomous reasoning.
        
        Args:
            documents: List of documents to analyze for this theme
            
        Returns:
            List of insight dictionaries with title, detail, and evidence
        """
        if not documents:
            logger.info(f"[{self.theme_label}] No documents, skipping")
            return []
        
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing")
        
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        context = self._build_context(documents)
        prompt = self._build_prompt(self.theme_label, self.theme_focus, context, len(documents))
        
        logger.info(f"[{self.theme_label}] Starting analysis with {len(documents)} documents")
        
        # Disable safety filters for civic news analysis
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(temperature=0.1, max_output_tokens=8000),
                safety_settings=safety_settings,
            )
            
            if not response.candidates:
                return [{"title": f"No Data for {self.theme_label}", "detail": "AI model returned no response.", "evidence": []}]
            
            output = sanitize_text(response.text)
            insights = self._parse_response(output, self.theme_label)
            
            logger.info(f"[{self.theme_label}] Generated {len(insights)} insights")
            return insights
            
        except Exception as e:
            logger.exception(f"[{self.theme_label}] Error: {e}")
            return [{"title": f"Error in {self.theme_label}", "detail": "Failed to generate insight.", "evidence": []}]


# ============================================================================
# DOMAIN-SPECIFIC SUB-AGENTS (6 Expert Sub-Agents)
# ============================================================================

@dataclass
class InfrastructureAgent(BaseThemeAgent):
    """Sub-agent for Infrastructure domain insights.
    
    Specialized in: roads, traffic, water, power, bridges, construction
    """
    
    theme_label: str = "Infrastructure"
    theme_focus: str = "Focus ONLY on infrastructure topics (roads, traffic, water, power, bridges, construction, Kennon Road, Session Road). Ignore other topics."


@dataclass
class HealthAgent(BaseThemeAgent):
    """Sub-agent for Health & Wellness domain insights.
    
    Specialized in: hospitals, clinics, diseases, vaccines, medical services
    """
    
    theme_label: str = "Health & Wellness"
    theme_focus: str = "Focus ONLY on health topics (diseases, hospitals, clinics, medical services, sanitation, dengue, covid, vaccine, medicine, BGH). Ignore other topics."


@dataclass
class SafetyAgent(BaseThemeAgent):
    """Sub-agent for Public Safety domain insights.
    
    Specialized in: crime, police, fire, emergencies, accidents, disasters
    """
    
    theme_label: str = "Public Safety"
    theme_focus: str = "Focus ONLY on safety topics (crime, police, fire, emergencies, accidents, landslides, floods, walkouts, protests). Ignore other topics."


@dataclass
class TourismAgent(BaseThemeAgent):
    """Sub-agent for Tourism & Events domain insights.
    
    Specialized in: tourists, hotels, festivals, events, visitors
    """
    
    theme_label: str = "Tourism & Events"
    theme_focus: str = "Focus ONLY on tourism/events topics (tourists, hotels, festivals, Panagbenga, visitors, Burnham, overcrowding). Ignore other topics."


@dataclass
class EconomyAgent(BaseThemeAgent):
    """Sub-agent for Business & Economy domain insights.
    
    Specialized in: markets, vendors, businesses, employment, prices
    """
    
    theme_label: str = "Business & Economy"
    theme_focus: str = "Focus ONLY on economy topics (business, markets, vendors, livelihood, mallification, SM Prime, price, displacement, employment). Ignore other topics."


@dataclass
class EnvironmentAgent(BaseThemeAgent):
    """Sub-agent for Environment domain insights.
    
    Specialized in: pollution, waste, climate, flooding, air quality
    """
    
    theme_label: str = "Environment"
    theme_focus: str = "Focus ONLY on environment topics (pollution, waste, garbage, climate, flooding, air quality, trees, deforestation). Ignore other topics."


# ============================================================================
# THEME AGENT FACTORY
# ============================================================================

def get_theme_agent(theme_key: str) -> BaseThemeAgent:
    """Factory function to create the appropriate sub-agent based on theme key.
    
    This enables CONDITIONAL SUB-AGENT SPAWNING based on theme.
    """
    agents = {
        "infrastructure": InfrastructureAgent,
        "health": HealthAgent,
        "safety": SafetyAgent,
        "tourism": TourismAgent,
        "economy": EconomyAgent,
        "environment": EnvironmentAgent,
    }
    
    agent_class = agents.get(theme_key.lower())
    if agent_class:
        return agent_class()
    
    # Generic fallback agent
    class GenericAgent(BaseThemeAgent):
        theme_label = theme_key.title()
        theme_focus = f"Focus on {theme_key} aspects only."
    
    return GenericAgent()


# ============================================================================
# LEGACY FUNCTION INTERFACE (Backward Compatibility)
# ============================================================================

async def run_theme_agent(
    theme_label: str,
    prompt: str,
    documents: list[dict[str, Any]],
) -> str:
    """Legacy function interface - kept for backward compatibility.
    
    Note: For new code, use the sub-agent classes directly.
    """
    agent = get_theme_agent(theme_label)
    insights = await agent.run(documents)
    return json.dumps({"insights": insights})
