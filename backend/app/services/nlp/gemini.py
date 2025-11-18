"""Gemini helper utilities for narrative generation."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import google.generativeai as genai

from ...core.config import get_settings

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
        if not self._model:
            return None, []

        prompt = self._build_prompt(window=window, focus_areas=focus_areas, documents=documents)

        def _invoke() -> str:
            response = self._model.generate_content(prompt)
            return response.text or ""

        try:
            raw_text = await asyncio.to_thread(_invoke)
        except Exception:  # pragma: no cover - network/SDK failures
            logger.exception("Gemini generation failed")
            return None, []

        try:
            text = raw_text.strip()
            if text.startswith("```") and text.endswith("```"):
                # Remove opening fence (``` or ```json)
                first_newline = text.find("\n")
                if first_newline != -1 and text[:first_newline].startswith("```"):
                    text = text[first_newline + 1 :]
                else:
                    text = text[3:]
                text = text[:-3].strip()

            parsed = json.loads(text)
        except json.JSONDecodeError:
            logger.debug("Gemini response not JSON: %s", raw_text)
            return raw_text.strip(), []

        summary = parsed.get("summary")
        insights = parsed.get("insights") or []
        return summary, insights

    def _build_prompt(self, *, window: str, focus_areas: list[str], documents: list[dict[str, Any]]) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"
        doc_lines = []
        for idx, doc in enumerate(documents[:10], start=1):
            doc_lines.append(
                f"{idx}. Title: {doc.get('title')} | Snippet: {doc.get('snippet')} | Sentiment: {doc.get('sentiment')}"
            )
        context_block = "\n".join(doc_lines) or "No documents available."

        return (
            "You are an analyst supporting the Baguio City command center. "
            f"Summarize public chatter over the last {window} with emphasis on {focus}.\n"
            "Return a JSON object with keys:\n"
            "summary: string narrative (<= 2 sentences)\n"
            "insights: list of up to 3 items, each {category, title, detail, evidence? (array of concise bullets)}.\n"
            "Use the following context entries to ground your analysis:\n"
            f"{context_block}\n"
        )


gemini_client = GeminiClient()
