"""Gemini-powered LangChain agent for sentiment reasoning."""
from __future__ import annotations

import logging
import re
from typing import Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ...core.config import get_settings

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


def _mock_weather(city: str) -> str:
    return f"It's always sunny in {city}!"


def _summarize_context(documents: Any = None) -> str:
    if not documents:
        return "No documents available."

    if isinstance(documents, str):
        text = documents.strip()
        return f"Context summary: {text[:200]}"

    if isinstance(documents, dict):
        docs_value = documents.get("documents")
        if isinstance(docs_value, list):
            documents = docs_value
        else:
            items = list(documents.items())[:3]
            summary = "; ".join(f"{k}: {v}" for k, v in items)
            return f"Context summary: {summary}"

    if isinstance(documents, list):
        if not documents:
            return "No documents available."
        titles: list[str] = []
        for doc in documents[:3]:
            if isinstance(doc, dict):
                title = doc.get("title") or "Untitled"
            else:
                title = str(doc)
            titles.append(title)
        reason = "; ".join(titles)
        return f"Key civic chatter: {reason}"

    return "No documents available."


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


def _build_prompt() -> PromptTemplate:
    """Build the ReAct prompt used by create_react_agent.

    This follows the reference template from LangChain's ReAct agent, adapted for
    the Baguio City civic operations use case and JSON-only final answers.
    """

    template = """You are a civic operations analyst for Baguio City.
You have access to the following tools: {tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: {{JSON}} containing 'summary' (<=2 sentences) and 'insights' (array of up to 3 objects with category/title/detail/evidence array).

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

    return PromptTemplate.from_template(template)


def _build_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Unable to initialize Gemini agent.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        google_api_key=settings.gemini_api_key,
    )


def get_gemini_agent() -> AgentExecutor:
    llm = _build_llm()
    tools = _build_tools()
    prompt = _build_prompt()
    agent_runnable = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent_runnable,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=5,  # Prevent runaway iterations
        max_execution_time=20,  # 20 second timeout per agent
    )


def run_gemini_agent(
    message: str,
    *,
    documents: list[dict[str, Any]] | None = None,
    system_instruction: str | None = None,
) -> str:
    executor = get_gemini_agent()
    if documents:
        doc_lines = []
        for doc in documents[:5]:
            title = sanitize_text(doc.get('title', 'Untitled'))
            snippet = sanitize_text(doc.get('snippet', ''))[:180]
            doc_lines.append(f"- {title} :: {snippet}")
        context_block = "\n".join(doc_lines)
        instructions = system_instruction or (
            "You are a civic operations analyst for Baguio City."
            " Return ONLY valid JSON with keys 'summary' (<=2 sentences) and"
            " 'insights' (array of up to 3 objects with category/title/detail/evidence array)."
            " Use tools if needed before answering."
        )
        # Sanitize the message and context
        safe_message = sanitize_text(message)
        safe_context = sanitize_text(context_block)
        input_payload = (
            f"{instructions}\n\nQuestion:\n{safe_message}\n\nContext documents:\n{safe_context}\n"
        )
    else:
        instructions = system_instruction or (
            "You are a civic operations analyst for Baguio City."
            " Respond with JSON containing summary + insights as described."
        )
        safe_message = sanitize_text(message)
        input_payload = f"{instructions}\n\nQuestion:\n{safe_message}"

    result = executor.invoke({"input": input_payload})
    output = result.get("output")
    if not isinstance(output, str):
        logger.warning("Gemini agent returned non-string output: %s", output)
        return str(output)
    return output
