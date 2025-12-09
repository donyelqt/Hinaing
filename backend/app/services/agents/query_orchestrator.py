"""ReAct-based query orchestrator that creates optimized search prompts for retrieval."""
from __future__ import annotations

import json
import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ...core.config import get_settings
from ...schemas.snapshot import SnapshotRequest
from ...schemas.query import QueryPlan, QueryTask
from ...services.insights.agent_tools import FOCUS_CONCERN_KEYWORDS

warnings.filterwarnings("ignore", message="Error in StdOutCallbackHandler")
logging.getLogger("langchain_core.callbacks.manager").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_time_search_suffix(time_window: str | None) -> str:
    """Generate search operator suffix for time-based filtering.
    
    Uses Google-style 'after:' operator to prioritize recent content.
    """
    if not time_window:
        return ""
    
    now = datetime.now(timezone.utc)
    
    if time_window == "6h":
        date_str = now.strftime("%Y-%m-%d")
        return f" after:{date_str}"
    elif time_window == "24h":
        yesterday = now - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
        return f" after:{date_str}"
    elif time_window == "3d":
        cutoff = now - timedelta(days=3)
        date_str = cutoff.strftime("%Y-%m-%d")
        return f" after:{date_str}"
    elif time_window == "7d":
        cutoff = now - timedelta(days=7)
        date_str = cutoff.strftime("%Y-%m-%d")
        return f" after:{date_str}"
    
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Tool Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_concern_keywords(input_str: str) -> str:
    """Get ALL curated concern keywords for the specified focus areas.
    
    Args:
        input_str: JSON with 'focus_areas' list
    
    Returns:
        All concern keywords for query optimization
    """
    try:
        data = json.loads(input_str)
        focus_areas = data.get("focus_areas", [])
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    all_keywords: list[str] = []
    area_info = []
    
    for area in focus_areas:
        area_lower = area.lower()
        keywords = FOCUS_CONCERN_KEYWORDS.get(area_lower, [])
        all_keywords.extend(keywords)
        area_info.append({
            "area": area,
            "keywords": keywords,
            "count": len(keywords)
        })

    unique_keywords = list(dict.fromkeys(all_keywords))

    return json.dumps({
        "total_keywords": len(unique_keywords),
        "areas": area_info,
        "all_keywords": unique_keywords,
        "instruction": "Use these keywords to craft an optimized search query"
    })


def craft_search_query(input_str: str) -> str:
    """Craft an optimized search query from keywords.
    
    Args:
        input_str: JSON with 'keywords' list and optional 'strategy'
    
    Returns:
        Optimized search query string
    """
    try:
        data = json.loads(input_str)
        keywords = data.get("keywords", [])
        strategy = data.get("strategy", "comprehensive")
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    if not keywords:
        return json.dumps({
            "query": "Baguio City civic concerns news",
            "type": "fallback"
        })

    # Build OR query with all keywords
    or_terms = " OR ".join(f'"{kw}"' for kw in keywords)
    query = f"({or_terms})"

    return json.dumps({
        "query": query,
        "keyword_count": len(keywords),
        "strategy": strategy,
        "type": "optimized"
    })


def evaluate_query_coverage(input_str: str) -> str:
    """Evaluate if the query covers all important concerns.
    
    Args:
        input_str: JSON with 'query' and 'focus_areas'
    
    Returns:
        Coverage assessment
    """
    try:
        data = json.loads(input_str)
        query = data.get("query", "").lower()
        focus_areas = data.get("focus_areas", [])
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    coverage = []
    missing = []
    
    for area in focus_areas:
        area_lower = area.lower()
        keywords = FOCUS_CONCERN_KEYWORDS.get(area_lower, [])
        
        found = sum(1 for kw in keywords if kw.lower() in query)
        total = len(keywords)
        pct = (found / total * 100) if total > 0 else 0
        
        coverage.append({
            "area": area,
            "coverage": f"{found}/{total} ({pct:.0f}%)",
            "complete": found == total
        })
        
        if found < total:
            missing.extend([kw for kw in keywords if kw.lower() not in query])

    all_complete = all(c["complete"] for c in coverage)
    
    return json.dumps({
        "coverage": coverage,
        "all_keywords_included": all_complete,
        "missing_keywords": missing[:5] if missing else [],
        "recommendation": "Query is comprehensive" if all_complete else f"Add missing keywords: {', '.join(missing[:3])}"
    })


# ─────────────────────────────────────────────────────────────────────────────
# ReAct Agent
# ─────────────────────────────────────────────────────────────────────────────

REACT_PROMPT = PromptTemplate.from_template("""You are a search query optimization agent for Baguio City civic monitoring.

Your task: Create an OPTIMIZED search query that the retrieval agent will use to find relevant documents.

Tools available:
{tools}

Tool names: {tool_names}

Format:
Question: [input]
Thought: [your reasoning]
Action: [tool name]
Action Input: [JSON input]
Observation: [tool result]
... (repeat as needed)
Thought: I have crafted an optimized query.
Final Answer: [JSON with strategy and query]

WORKFLOW:
1. Use get_concern_keywords to retrieve ALL keywords for the focus areas
2. Use craft_search_query to build an optimized OR query with ALL keywords
3. Optionally use evaluate_query_coverage to verify completeness
4. Output Final Answer with the optimized query

Final Answer JSON format:
{{"strategy": "description of your optimization approach", "queries": ["the optimized search query"], "expected_results": ["what results to expect"]}}

IMPORTANT: Include ALL concern keywords in the query - do not filter or reduce them.

Begin!

Question: {input}
{agent_scratchpad}""")


@dataclass
class QueryOrchestratorAgent:
    """ReAct agent that creates optimized search prompts for retrieval."""

    max_queries: int = 1
    max_iterations: int = 5
    fallback_focus: str = "public services"
    _llm: ChatGoogleGenerativeAI | None = field(default=None, init=False)
    _executor: AgentExecutor | None = field(default=None, init=False)

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=settings.gemini_api_key,
                temperature=0.2,
            )
        return self._llm

    def _get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="get_concern_keywords",
                func=get_concern_keywords,
                description=(
                    "Get ALL curated concern keywords for focus areas. "
                    "Input: JSON with 'focus_areas' list. "
                    "Returns all keywords to include in the search query."
                ),
            ),
            Tool(
                name="craft_search_query",
                func=craft_search_query,
                description=(
                    "Craft an optimized search query from keywords. "
                    "Input: JSON with 'keywords' list. "
                    "Returns an OR-combined query string."
                ),
            ),
            Tool(
                name="evaluate_query_coverage",
                func=evaluate_query_coverage,
                description=(
                    "Evaluate if query covers all concerns. "
                    "Input: JSON with 'query' and 'focus_areas'. "
                    "Returns coverage assessment."
                ),
            ),
        ]

    def _build_executor(self) -> AgentExecutor:
        if self._executor is None:
            llm = self._get_llm()
            tools = self._get_tools()
            agent = create_react_agent(llm, tools, REACT_PROMPT)
            self._executor = AgentExecutor(
                agent=agent,
                tools=tools,
                max_iterations=self.max_iterations,
                verbose=True,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
            )
        return self._executor

    def run(self, request: SnapshotRequest) -> QueryPlan:
        """Generate an optimized query plan using ReAct reasoning."""
        focus_values = request.focus_areas or [self.fallback_focus]
        time_window = request.time_window or "24h"

        logger.info(
            "[query_orchestrator] Starting ReAct optimization",
            extra={"focus": focus_values, "window": time_window},
        )

        input_text = (
            f"Create an optimized search query for Baguio City civic monitoring. "
            f"Focus areas: {', '.join(focus_values)}. "
            f"Time window: {time_window}. "
            f"The query should include ALL relevant concern keywords for comprehensive retrieval."
        )

        try:
            executor = self._build_executor()
            result = executor.invoke({"input": input_text})
            
            final_output = result.get("output", "")
            steps = result.get("intermediate_steps", [])
            logger.info(f"[query_orchestrator] ReAct completed in {len(steps)} steps")
            
            plan = self._parse_output(final_output, focus_values, steps, time_window)
            
        except Exception as exc:
            logger.warning("[query_orchestrator] ReAct failed, using fallback: %s", exc)
            plan = self._fallback_plan(focus_values, time_window)

        logger.info(
            "[query_orchestrator] Optimized query ready",
            extra={"strategy": plan.strategy[:80]},
        )
        return plan

    def _parse_output(self, output: str, focus_values: list[str], steps: list | None = None, time_window: str | None = None) -> QueryPlan:
        """Parse ReAct output into QueryPlan."""
        time_suffix = _get_time_search_suffix(time_window)
        
        try:
            # Extract JSON from output
            if "```json" in output:
                json_str = output.split("```json")[1].split("```")[0].strip()
            elif "```" in output:
                json_str = output.split("```")[1].split("```")[0].strip()
            else:
                start = output.find("{")
                end = output.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = output[start:end]
                else:
                    if steps:
                        return self._extract_from_steps(steps, focus_values, time_window)
                    raise ValueError("No JSON found")

            data = json.loads(json_str)
            
            queries = []
            for idx, q in enumerate(data.get("queries", [])):
                query_text = q if isinstance(q, str) else q.get("query", "")
                if query_text:
                    # Append time suffix to each query
                    query_with_time = f"{query_text}{time_suffix}"
                    queries.append(QueryTask(query=query_with_time, intent="targeted", priority=idx + 1))

            if not queries:
                if steps:
                    return self._extract_from_steps(steps, focus_values, time_window)
                return self._fallback_plan(focus_values, time_window)

            logger.info("[query_orchestrator] Added time suffix to queries: %s", time_suffix or "(none)")
            
            return QueryPlan(
                strategy=data.get("strategy", f"Optimized query for {', '.join(focus_values)}"),
                queries=queries[:self.max_queries],
                expected_results=data.get("expected_results", [])[:3],
            )

        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("[query_orchestrator] Parse failed: %s", exc)
            if steps:
                return self._extract_from_steps(steps, focus_values, time_window)
            return self._fallback_plan(focus_values, time_window)

    def _extract_from_steps(self, steps: list, focus_values: list[str], time_window: str | None = None) -> QueryPlan:
        """Extract query from intermediate steps."""
        time_suffix = _get_time_search_suffix(time_window)
        
        for step in reversed(steps):
            if len(step) >= 2:
                action, observation = step[0], step[1]
                if hasattr(action, 'tool') and action.tool == "craft_search_query":
                    try:
                        result = json.loads(observation) if isinstance(observation, str) else observation
                        if isinstance(result, dict) and result.get("query"):
                            query_with_time = f"{result['query']}{time_suffix}"
                            logger.info("[query_orchestrator] Added time suffix: %s", time_suffix or "(none)")
                            return QueryPlan(
                                strategy=f"Optimized query with {result.get('keyword_count', 0)} keywords",
                                queries=[QueryTask(query=query_with_time, intent="targeted", priority=1)],
                                expected_results=[f"Results for {', '.join(focus_values)} concerns"],
                            )
                    except (json.JSONDecodeError, TypeError):
                        continue
        return self._fallback_plan(focus_values, time_window)

    def _fallback_plan(self, focus_values: list[str], time_window: str | None = None) -> QueryPlan:
        """Direct fallback using ALL concern keywords."""
        time_suffix = _get_time_search_suffix(time_window)
        
        all_keywords: list[str] = []
        for area in focus_values:
            keywords = FOCUS_CONCERN_KEYWORDS.get(area.lower(), [])
            all_keywords.extend(keywords)
        
        unique = list(dict.fromkeys(all_keywords))
        
        if unique:
            or_terms = " OR ".join(f'"{kw}"' for kw in unique)
            query = f"({or_terms}){time_suffix}"
            strategy = f"Fallback: {len(unique)} keywords for {', '.join(focus_values)}"
        else:
            query = f"Baguio City {' '.join(focus_values)} problem OR concern{time_suffix}"
            strategy = f"Fallback: Generic query for {', '.join(focus_values)}"
        
        logger.info("[query_orchestrator] Fallback with time suffix: %s", time_suffix or "(none)")
        
        return QueryPlan(
            strategy=strategy,
            queries=[QueryTask(query=query, intent="targeted", priority=1)],
            expected_results=[f"Results for {', '.join(focus_values)} concerns in Baguio City"],
        )
