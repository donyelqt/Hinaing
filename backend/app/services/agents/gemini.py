"""Gemini-powered LangChain agent for sentiment reasoning."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

from ...core.config import get_settings

logger = logging.getLogger(__name__)


def _mock_weather(city: str) -> str:
    return f"It's always sunny in {city}!"


def _summarize_context(documents: list[dict[str, Any]] | None = None) -> str:
    if not documents:
        return "No documents available."
    reason = "; ".join(doc.get("title") or "Untitled" for doc in documents[:3])
    return f"Key civic chatter: {reason}"


def _build_tools() -> list[Tool]:
    return [
        Tool(
            name="weather",
            func=_mock_weather,
            description="Quick sanity check for weather-related questions.",
        ),
        Tool(
            name="context_summary",
            func=_summarize_context,
            description="Summarize the current set of documents or signals.",
        ),
    ]


def _build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a civic operations analyst for Baguio City."
                "Combine live search documents, citizen reports, and situational awareness"
                "to deliver clear next steps. Use tools if needed, otherwise answer directly.",
            ),
            ("user", "{input}"),
        ]
    )


def _build_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Unable to initialize Gemini agent.")
    return ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)


@lru_cache
def get_gemini_agent() -> AgentExecutor:
    llm = _build_llm()
    tools = _build_tools()
    prompt = _build_prompt()
    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


def run_gemini_agent(message: str, *, documents: list[dict[str, Any]] | None = None) -> str:
    executor = get_gemini_agent()
    if documents:
        doc_lines = [
            f"- {doc.get('title', 'Untitled')} :: {doc.get('snippet', '')[:180]}"
            for doc in documents[:5]
        ]
        context_block = "\n".join(doc_lines)
        input_payload = (
            f"{message}\n\nContext documents:\n{context_block}\n"
        )
    else:
        input_payload = message

    result = executor.invoke({"input": input_payload})
    output = result.get("output")
    if not isinstance(output, str):
        logger.warning("Gemini agent returned non-string output: %s", output)
        return str(output)
    return output
