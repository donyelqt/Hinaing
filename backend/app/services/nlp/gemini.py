"""Gemini helper utilities for narrative generation."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable

import google.generativeai as genai

from ...core.config import get_settings
from ..agents.gemini import run_gemini_agent

logger = logging.getLogger(__name__)


class GeminiClient:
    """Thin wrapper around the Gemini GenerativeModel."""

    def __init__(self, *, model_name: str = "gemini-2.5-flash") -> None:
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
    ) -> tuple[str | None, list[dict[str, Any]]]:
        agent_instruction = self._build_agent_instruction(window=window, focus_areas=focus_areas)

        # Prefer the LangChain agent so reasoning can call tools when necessary.
        try:
            agent_output = await asyncio.to_thread(
                lambda: run_gemini_agent(agent_instruction, documents=documents)
            )
            parsed = self._try_parse_json(agent_output)
            if parsed is not None:
                summary = parsed.get("summary")
                insights = parsed.get("insights") or []
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
        )

    async def _run_direct_generation(
        self,
        *,
        window: str,
        focus_areas: list[str],
        documents: list[dict[str, Any]],
    ) -> tuple[str | None, list[dict[str, Any]]]:
        plan_prompt = self._build_plan_prompt(window=window, focus_areas=focus_areas, documents=documents)

        def _invoke(prompt_builder: Callable[[], str]) -> str:
            response = self._model.generate_content(prompt_builder())
            return response.text or ""

        try:
            plan_text = await asyncio.to_thread(lambda: _invoke(lambda: plan_prompt))
        except Exception:  # pragma: no cover - network/SDK failures
            logger.exception("Gemini generation failed")
            return None, []

        analysis_prompt = self._build_prompt(
            window=window,
            focus_areas=focus_areas,
            documents=documents,
            plan=plan_text,
        )

        try:
            raw_text = await asyncio.to_thread(lambda: _invoke(lambda: analysis_prompt))
        except Exception:  # pragma: no cover - network/SDK failures
            logger.exception("Gemini analysis failed")
            return None, []

        parsed = self._try_parse_json(raw_text)
        if parsed is None:
            return raw_text.strip(), []

        summary = parsed.get("summary")
        insights = parsed.get("insights") or []
        return summary, insights

    def _build_prompt(
        self,
        *,
        window: str,
        focus_areas: list[str],
        documents: list[dict[str, Any]],
        plan: str | None,
    ) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"
        doc_lines = []
        for idx, doc in enumerate(documents[:10], start=1):
            doc_lines.append(
                f"{idx}. Title: {doc.get('title')} | Snippet: {doc.get('snippet')} | Sentiment: {doc.get('sentiment')}"
            )
        context_block = "\n".join(doc_lines) or "No documents available."
        plan_section = plan.strip() if plan else "1. Review documents\n2. Extract key signals\n3. Draft JSON summary"

        return (
            "You are an analyst supporting the Baguio City command center. "
            f"Summarize public chatter over the last {window} with emphasis on {focus}.\n"
            "Start by following this reasoning plan (update it if needed):\n"
            f"{plan_section}\n"
            "Return a JSON object with keys:\n"
            "summary: string narrative (<= 2 sentences)\n"
            "insights: list of up to 3 items, each {category, title, detail, evidence? (array of concise bullets)}.\n"
            "Use the following context entries to ground your analysis:\n"
            f"{context_block}\n"
        )

    def _build_agent_instruction(self, *, window: str, focus_areas: list[str]) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"
        return (
            "Summarize public chatter for the Baguio City command center."
            f" Time window: {window}. Focus areas: {focus}."
            " Produce a JSON object with keys summary (<=2 sentences) and insights (array of up to 3 items)."
            " Each insight needs category, title, detail, and optional evidence array."
            " Cite only from the provided context block and highlight actionable guidance."
        )

    def _build_plan_prompt(self, *, window: str, focus_areas: list[str], documents: list[dict[str, Any]]) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"
        doc_sample = documents[:5]
        doc_summaries = "\n".join(
            f"- {doc.get('title')}: {doc.get('snippet')}" for doc in doc_sample
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
        text = raw_text.strip()
        if text.startswith("```") and text.endswith("```"):
            first_newline = text.find("\n")
            if first_newline != -1 and text[:first_newline].startswith("```"):
                text = text[first_newline + 1 :]
            else:
                text = text[3:]
            text = text[:-3].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.debug("Gemini response not JSON: %s", raw_text)
            return None


gemini_client = GeminiClient()
