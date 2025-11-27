"""Optimized ReAct agent for theme-specific insights."""
from __future__ import annotations

import logging
from typing import Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ...core.config import get_settings

logger = logging.getLogger(__name__)


def _summarize_theme_context(documents: Any = None) -> str:
    """Summarize document context for theme analysis."""
    if not documents:
        return "No documents available."
    
    if isinstance(documents, list) and documents:
        titles = []
        for doc in documents[:3]:
            if isinstance(doc, dict):
                title = doc.get("title") or "Untitled"
                snippet = doc.get("snippet", "")[:100]
                titles.append(f"{title}: {snippet}")
            else:
                titles.append(str(doc)[:100])
        return f"Key documents: {'; '.join(titles)}"
    
    return "No documents available."


def _build_theme_tools() -> list[Tool]:
    """Build minimal toolset for theme agents."""
    return [
        Tool(
            name="context_summary",
            func=_summarize_theme_context,
            description="Summarize the current set of documents for this theme.",
        ),
    ]


def _build_theme_prompt() -> PromptTemplate:
    """Build optimized ReAct prompt for theme insights.
    
    Key optimizations:
    1. Schema matches expected output (title/detail/evidence)
    2. Simplified instructions to reduce iteration count
    3. Clear termination criteria
    """
    
    template = """You are a civic operations analyst for Baguio City focusing on a specific theme.
You have access to the following tools: {tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: {{JSON}} containing 'title' (concise title), 'detail' (<=240 chars actionable insight), and 'evidence' (array of source URLs).

IMPORTANT INSTRUCTIONS:
1. You already have all the context documents needed in the Question section.
2. DO NOT use tools unless you absolutely need additional context.
3. In most cases, you should answer IMMEDIATELY based on the provided documents.
4. Your response must be valid JSON with keys: title, detail, evidence.

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
    
    return PromptTemplate.from_template(template)


def _build_theme_llm() -> ChatGoogleGenerativeAI:
    """Build LLM instance optimized for theme agents."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Unable to initialize theme agent.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",  # Faster model
        temperature=0.1,  # Lower temperature for more focused output
        google_api_key=settings.gemini_api_key,
    )


def get_theme_agent() -> AgentExecutor:
    """Get optimized ReAct agent for theme insights.
    
    Optimizations:
    - max_iterations=5 (balanced: enough for complex cases, prevents runaway)
    - max_execution_time=30s (hard timeout)
    - minimal toolset (faster execution)
    - focused prompt (clearer task)
    """
    llm = _build_theme_llm()
    tools = _build_theme_tools()
    prompt = _build_theme_prompt()
    agent_runnable = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent_runnable,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=5,  # Increased from 3 to handle complex themes
        max_execution_time=30,  # 30 second hard cap
    )


def run_theme_agent(
    theme_label: str,
    prompt: str,
    documents: list[dict[str, Any]],
) -> str:
    """Run optimized ReAct agent for theme insight synthesis.
    
    Args:
        theme_label: Theme name (e.g., "Health & Safety")
        prompt: Analysis instruction
        documents: Context documents
        
    Returns:
        JSON string with {title, detail, evidence}
    """
    executor = get_theme_agent()
    
    # Build context block
    doc_lines = [
        f"- {doc.get('title', 'Untitled')} :: {doc.get('snippet', '')[:180]}"
        for doc in documents[:5]
    ]
    context_block = "\n".join(doc_lines)
    
    # Define theme-specific focus instructions
    theme_focus = {
        "Health & Wellness": "ONLY analyze health issues (diseases, medical services, public health risks, hospitals, clinics, sanitation, wellness programs). IGNORE safety, infrastructure, economic, environmental, or tourism topics.",
        "Public Safety": "ONLY analyze safety concerns (crime, police, fire, accidents, emergency services, disasters, rescue operations). IGNORE health, infrastructure, economic, environmental, or tourism topics.",
        "Infrastructure": "ONLY analyze infrastructure (roads, traffic, water systems, power, buildings, construction, utilities). IGNORE health, safety, economic, environmental, or tourism topics.",
        "Environment": "ONLY analyze environmental issues (pollution, waste management, flooding, landslides, rain, drainage, environmental programs). IGNORE health, safety, infrastructure, economic, or tourism topics.",
        "Tourism & Events": "ONLY analyze tourism impacts, visitor numbers, events, festivals, hotel/accommodation issues. IGNORE health, safety, infrastructure, environmental, or business/economic topics unless they directly impact tourism.",
        "Business & Economy": "ONLY analyze economic indicators, business conditions, market trends, vendors, revenue, livelihood. IGNORE health, safety, infrastructure, environmental, or tourism topics unless they directly impact economy.",
    }
    
    focus_instruction = theme_focus.get(theme_label, f"Focus strictly on {theme_label}-related aspects only.")
    
    # Build input
    input_payload = (
        f"Theme: {theme_label}\n\n"
        f"CRITICAL: {focus_instruction}\n\n"
        f"{prompt}\n\n"
        f"Context documents:\n{context_block}\n\n"
        "If the documents do not contain relevant information for this specific theme, "
        "return JSON with title indicating no relevant data, detail explaining this, and empty evidence array.\n\n"
        "Return ONLY valid JSON with keys 'title', 'detail', and 'evidence' (array of source URLs)."
    )
    
    result = executor.invoke({"input": input_payload})
    output = result.get("output")
    if not isinstance(output, str):
        logger.warning("Theme agent returned non-string output: %s", output)
        return str(output)
    return output
