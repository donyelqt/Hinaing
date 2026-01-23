"""Gemini helper utilities for narrative generation."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Callable

import google.generativeai as genai

from ...core.config import get_settings
from ..agents.gemini import run_gemini_agent

logger = logging.getLogger(__name__)


def sanitize_text(text: str | None) -> str:
    """Remove invalid Unicode characters (surrogates) that break Gemini API."""
    if not text:
        return ""
    # Remove surrogate characters (U+D800 to U+DFFF)
    cleaned = re.sub(r'[\ud800-\udfff]', '', str(text))
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
    cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', cleaned)
    return cleaned.strip()


class GeminiClient:
    """Thin wrapper around the Gemini GenerativeModel."""

    def __init__(self, *, model_name: str = "gemini-2.5-flash-lite") -> None:
        """Initialize Gemini client.
        
        Uses Gemini 2.5 Flash for narrative generation. Since theme_insights
        are already summarized by Theme Agents (using Pro), Flash is sufficient
        for final synthesis and much faster (~10s vs ~40s).
        """
        settings = get_settings()
        self._api_key = settings.gemini_api_key
        self._model_name = model_name
        self._model = None

        if self._api_key:
            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(self._model_name)

    @property
    def is_available(self) -> bool:
        return self._model is not None

    async def analyze_snapshot(
        self,
        *,
        window: str,
        focus_areas: list[str],
        documents: list[dict[str, Any]],
        theme_insights: list[dict[str, Any]] | None = None,
    ) -> tuple[str | None, list[dict[str, Any]]]:
        # OPTIMIZATION: If theme_insights exist, skip the slow agent path
        # Theme insights are already summarized by Theme Agents (Node 6)
        # This reduces latency from ~40s to ~10s
        if theme_insights and len(theme_insights) > 0:
            logger.info(
                "[GeminiClient] Using theme_insights for narrative (skipping agent path)",
                extra={"theme_count": len(theme_insights), "doc_count": len(documents)}
            )
            return await self._run_direct_generation(
                window=window,
                focus_areas=focus_areas,
                documents=documents,  # Still passed for fallback context
                theme_insights=theme_insights,
            )
        
        # Fallback: Use agent path only when no theme_insights available
        agent_instruction = self._build_agent_instruction(window=window, focus_areas=focus_areas)

        try:
            agent_output = await asyncio.to_thread(
                lambda: run_gemini_agent(agent_instruction, documents=documents)
            )
            parsed = self._try_parse_json(agent_output)
            if parsed is not None:
                summary = sanitize_text(parsed.get("summary"))
                insights = self._sanitize_insights(parsed.get("insights") or [])
                return summary, insights
        except Exception:
            logger.exception("Gemini agent execution failed")

        # Fallback to direct model invocation if the agent path fails or returns invalid JSON.
        if not self._model:
            return None, []

        return await self._run_direct_generation(
            window=window,
            focus_areas=focus_areas,
            documents=documents,
            theme_insights=theme_insights,
        )

    def _sanitize_insights(self, insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sanitize all text fields in insights to remove surrogates."""
        sanitized = []
        for item in insights:
            if not isinstance(item, dict):
                continue
            clean_item = {
                "category": sanitize_text(item.get("category")),
                "title": sanitize_text(item.get("title")),
                "detail": sanitize_text(item.get("detail")),
            }
            evidence = item.get("evidence")
            if isinstance(evidence, list):
                clean_item["evidence"] = [sanitize_text(str(e)) for e in evidence]
            elif isinstance(evidence, str):
                clean_item["evidence"] = [sanitize_text(evidence)]
            sanitized.append(clean_item)
        return sanitized

    async def _run_direct_generation(
        self,
        *,
        window: str,
        focus_areas: list[str],
        documents: list[dict[str, Any]],
        theme_insights: list[dict[str, Any]] | None = None,
    ) -> tuple[str | None, list[dict[str, Any]]]:
        # Single-shot analysis without separate planning step for speed
        analysis_prompt = self._build_prompt(
            window=window,
            focus_areas=focus_areas,
            documents=documents,
            theme_insights=theme_insights,
        )

        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        def _invoke(prompt_builder: Callable[[], str]) -> str:
            response = self._model.generate_content(
                prompt_builder(),
                safety_settings=safety_settings,
            )
            return response.text or ""

        try:
            import time
            start = time.perf_counter()
            raw_text = await asyncio.wait_for(
                asyncio.to_thread(lambda: _invoke(lambda: analysis_prompt)),
                timeout=60.0  # 60s max for narrative generation
            )
            elapsed = time.perf_counter() - start
            logger.info(f"[GeminiClient] Narrative generated in {elapsed:.1f}s")
        except asyncio.TimeoutError:
            logger.error("[GeminiClient] Narrative generation timed out after 60s")
            return None, []
        except Exception:  # pragma: no cover - network/SDK failures
            logger.exception("Gemini analysis failed")
            return None, []

        parsed = self._try_parse_json(raw_text)
        if parsed is None:
            return sanitize_text(raw_text.strip()), []

        summary = sanitize_text(parsed.get("summary"))
        insights = self._sanitize_insights(parsed.get("insights") or [])
        return summary, insights

    def _build_prompt(
        self,
        *,
        window: str,
        focus_areas: list[str],
        documents: list[dict[str, Any]],
        theme_insights: list[dict[str, Any]] | None = None,
    ) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"
        
        # Build theme insights section if available
        insights_block = ""
        if theme_insights:
            insight_lines = []
            for item in theme_insights:
                cat = sanitize_text(item.get('category', 'General'))
                title = sanitize_text(item.get('title'))
                detail = sanitize_text(item.get('detail'))
                insight_lines.append(f"THEME [{cat}]: {title}\nDETAILS: {detail}")
            insights_block = "\n\n=== PRE-ANALYZED THEME INSIGHTS ===\n" + "\n\n".join(insight_lines)
        
        # Build documents section - use all docs, truncate snippets for speed
        doc_lines = []
        for idx, doc in enumerate(documents, start=1):
            title = sanitize_text(doc.get('title', ''))
            snippet = sanitize_text(doc.get('snippet', ''))[:300]  # Truncate long snippets
            sentiment = doc.get('sentiment', 'neutral')
            credibility = doc.get('metadata', {}).get('credibility_score', doc.get('credibility_score', 0.0))
            doc_lines.append(f"{idx}. [{sentiment.upper()} | Cred:{credibility:.2f}] {title}: {snippet}")
        docs_block = "\n".join(doc_lines) or "No documents available."

        return (
            "You are a senior analyst supporting the Baguio City command center. "
            f"Summarize public chatter over the last {window} with emphasis on {focus}.\n\n"
            f"=== SUPPORTING CONVERSATIONS ({len(documents)} documents) ===\n"
            f"{docs_block}\n"
            f"{insights_block}\n\n"
            "TASK:\n"
            "1. Analyze ALL supporting conversations above.\n"
            "2. Reference the theme insights for structured context.\n"
            "3. Generate a comprehensive, engaging narrative summary.\n\n"
            "FORMATTING REQUIREMENTS:\n"
            "- Structure the summary into 4-5 well-developed paragraphs (3-4 sentences each)\n"
            "- Each paragraph should focus on ONE major theme/topic with depth and context\n"
            "- Start each paragraph with a BOLD topic indicator like: **Public Safety:** or **Infrastructure:**\n"
            "- Use vivid, descriptive language that brings the situation to life\n"
            "- Highlight key tensions, risks, and positive developments with specific details\n"
            "- Include contextual information about what this means for Baguio City\n"
            "- Add a concluding paragraph that synthesizes the overall sentiment and key takeaways\n\n"
            "Return a JSON object with keys:\n"
            "- summary: string narrative (structured paragraphs as described above, separated by double newlines)\n"
            "- insights: list of up to 5 items, each {category, title, detail, evidence (array of source URLs)}\n"
        )

    def _build_agent_instruction(self, *, window: str, focus_areas: list[str]) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"
        num_focus_areas = len(focus_areas) if focus_areas else 1
        return (
            "Summarize public chatter for the Baguio City command center."
            f" Time window: {window}. Focus areas: {focus}."
            " Produce a JSON object with keys summary (3-5 sentences covering all major themes) and insights (array of up to 5 items)."
            " Each insight needs category, title, detail (comprehensive explanation), and optional evidence array with source URLs."
            f" IMPORTANT: Generate at least one insight for EACH focus area ({focus})."
            " Ensure balanced coverage - do not focus only on the most common topic."
            " Analyze ALL provided documents thoroughly and cite from the context block."
        )

    def _build_plan_prompt(self, *, window: str, focus_areas: list[str], documents: list[dict[str, Any]]) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"
        doc_sample = documents[:5]
        doc_summaries = "\n".join(
            f"- {sanitize_text(doc.get('title'))}: {sanitize_text(doc.get('snippet'))}" for doc in doc_sample
        ) or "- No documents available"

        return (
            "You are a senior analyst agent tasked with planning how to summarize civic chatter.\n"
            f"Time window: {window}. Focus areas: {focus}.\n"
            "Draft a numbered plan (3-5 steps) describing how you will interpret the documents, prioritize risks, and validate sources.\n"
            "End with 'Plan ready.'\n"
            "Recent documents:\n"
            f"{doc_summaries}\n"
        )

    @staticmethod
    def _try_parse_json(raw_text: str) -> dict[str, Any] | None:
        """Extract and parse JSON from Gemini's response with robust recovery."""
        if not raw_text:
            return None
            
        text = sanitize_text(raw_text).strip()
        
        # Strategy 1: Markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if json_match:
            candidate = json_match.group(1).strip()
            result = GeminiClient._safe_json_parse(candidate)
            if result:
                return result
            text = candidate
        
        # Strategy 2: Outermost braces
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx : end_idx + 1]

        # Strategy 3: Direct parse with cleaning
        result = GeminiClient._safe_json_parse(text)
        if result:
            return result
        
        # Strategy 4: Extract summary and insights separately using regex
        # This handles cases where JSON is malformed but content is extractable
        logger.info("[GeminiClient] Attempting regex extraction fallback...")
        
        summary_match = re.search(r'"summary"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', text, re.DOTALL)
        summary = summary_match.group(1) if summary_match else None
        
        if summary:
            # Unescape the summary
            summary = summary.replace('\\"', '"').replace('\\n', '\n')
            logger.info(f"[GeminiClient] Extracted summary via regex ({len(summary)} chars)")
            return {"summary": summary, "insights": []}
        
        logger.warning(f"[GeminiClient] JSON parse failed. Text: {text[:200]}...")
        return None
    
    @staticmethod
    def _safe_json_parse(text: str) -> dict[str, Any] | None:
        """Try multiple JSON parsing strategies."""
        # Attempt 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Attempt 2: Remove trailing commas
        try:
            cleaned = re.sub(r',\s*([}\]])', r'\1', text)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Attempt 3: Fix common issues
        try:
            # Replace single quotes with double quotes (common Gemini issue)
            fixed = text.replace("'", '"')
            # Remove any control characters
            fixed = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', fixed)
            # Fix unescaped newlines in strings
            fixed = re.sub(r'(?<!\\)\n', '\\n', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
        
        # Attempt 4: Truncate at last valid closing brace
        try:
            # Find balanced braces
            depth = 0
            last_valid_end = -1
            for i, char in enumerate(text):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        last_valid_end = i
                        break
            
            if last_valid_end > 0:
                truncated = text[:last_valid_end + 1]
                return json.loads(truncated)
        except json.JSONDecodeError:
            pass
        
        return None


gemini_client = GeminiClient()
