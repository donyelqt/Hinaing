"""ReAct-based adaptive query planning for the insights workflow."""
from __future__ import annotations

import json
import logging
import warnings
from dataclasses import dataclass, field
from typing import Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ...core.config import get_settings
from ...schemas.snapshot import SnapshotRequest
from ...schemas.query import QueryPlan, QueryTask

# Suppress the StdOutCallbackHandler warning
warnings.filterwarnings("ignore", message="Error in StdOutCallbackHandler")
logging.getLogger("langchain_core.callbacks.manager").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
settings = get_settings()


# ─────────────────────────────────────────────────────────────────────────────
# Tool Functions
# ─────────────────────────────────────────────────────────────────────────────

def analyze_focus_areas(input_str: str) -> str:
    """Analyze focus areas to determine optimal search strategy.
    
    Args:
        input_str: JSON string with 'focus_areas' and 'time_window' keys
    
    Returns:
        Analysis with recommended query types and coverage strategy
    """
    try:
        data = json.loads(input_str)
        focus_areas = data.get("focus_areas", [])
        time_window = data.get("time_window", "24h")
    except json.JSONDecodeError:
        return "Error: Invalid JSON input. Expected {'focus_areas': [...], 'time_window': '...'}"

    if not focus_areas:
        return json.dumps({
            "analysis": "No specific focus areas provided",
            "recommendation": "Use broad civic monitoring queries",
            "suggested_types": ["broad", "risk"],
            "coverage": "general"
        })

    # Analyze each focus area for query strategy
    analysis_results = []
    for area in focus_areas:
        area_lower = area.lower()
        
        # Determine query characteristics based on focus area
        if area_lower in ("health", "safety"):
            query_type = "urgent"
            keywords = ["alert", "incident", "update", "report"]
        elif area_lower in ("infrastructure", "environment"):
            query_type = "monitoring"
            keywords = ["status", "project", "development", "issue"]
        elif area_lower in ("tourism", "economy"):
            query_type = "trend"
            keywords = ["trend", "growth", "activity", "business"]
        else:
            query_type = "general"
            keywords = ["news", "update", "latest"]
        
        analysis_results.append({
            "area": area,
            "query_type": query_type,
            "suggested_keywords": keywords,
            "priority": "high" if query_type == "urgent" else "medium"
        })

    return json.dumps({
        "analysis": f"Analyzed {len(focus_areas)} focus areas",
        "time_window": time_window,
        "areas": analysis_results,
        "recommendation": "Generate targeted queries for each area plus one broad query"
    })


def generate_query(input_str: str) -> str:
    """Generate an optimized search query for Baguio City civic monitoring.
    
    Args:
        input_str: JSON with 'focus_area', 'query_type', 'time_window', 'keywords'
    
    Returns:
        Optimized query string
    """
    try:
        data = json.loads(input_str)
        focus_area = data.get("focus_area", "public services")
        query_type = data.get("query_type", "broad")
        time_window = data.get("time_window", "24h")
        keywords = data.get("keywords", [])
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    # Build query based on type
    base = "Baguio City"
    
    if query_type == "urgent":
        query = f"{base} {focus_area} alert incident report {time_window}"
    elif query_type == "monitoring":
        query = f"{base} {focus_area} status update development {time_window}"
    elif query_type == "trend":
        query = f"{base} {focus_area} trend news latest {time_window}"
    elif query_type == "risk":
        query = f"{base} {focus_area} emergency warning crisis {time_window}"
    else:
        # Broad query
        if keywords:
            keyword_str = " ".join(keywords[:3])
            query = f"{base} {focus_area} {keyword_str} {time_window}"
        else:
            query = f"{base} {focus_area} civic updates {time_window}"

    return json.dumps({
        "query": query,
        "type": query_type,
        "focus_area": focus_area,
        "estimated_relevance": 0.8 if query_type in ("urgent", "targeted") else 0.6
    })


def evaluate_query(input_str: str) -> str:
    """Evaluate if a query will yield good results for civic monitoring.
    
    Args:
        input_str: JSON with 'query' and 'intent'
    
    Returns:
        Quality assessment with score and suggestions
    """
    try:
        data = json.loads(input_str)
        query = data.get("query", "")
        intent = data.get("intent", "broad")
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    if not query:
        return json.dumps({"score": 0, "feedback": "Empty query", "pass": False})

    # Scoring criteria
    score = 0.5  # Base score
    feedback = []

    # Check for location specificity
    if "baguio" in query.lower():
        score += 0.2
        feedback.append("Good: Location-specific")
    else:
        feedback.append("Warning: Missing location context")

    # Check for temporal markers
    temporal_markers = ["24h", "1w", "1d", "week", "today", "latest", "recent"]
    if any(marker in query.lower() for marker in temporal_markers):
        score += 0.1
        feedback.append("Good: Has temporal context")

    # Check query length (not too short, not too long)
    word_count = len(query.split())
    if 4 <= word_count <= 12:
        score += 0.1
        feedback.append("Good: Appropriate query length")
    elif word_count < 4:
        feedback.append("Warning: Query too short, may be too broad")
    else:
        feedback.append("Warning: Query too long, may be too specific")

    # Check for actionable keywords based on intent
    if intent == "risk":
        risk_keywords = ["alert", "emergency", "incident", "warning", "crisis"]
        if any(kw in query.lower() for kw in risk_keywords):
            score += 0.1
            feedback.append("Good: Contains risk-relevant keywords")

    return json.dumps({
        "score": round(score, 2),
        "feedback": "; ".join(feedback),
        "pass": score >= 0.6,
        "suggestion": "Query looks good" if score >= 0.6 else "Consider adding location or temporal context"
    })


# ─────────────────────────────────────────────────────────────────────────────
# ReAct Agent
# ─────────────────────────────────────────────────────────────────────────────

REACT_PROMPT = PromptTemplate.from_template("""You are a query planning agent for a civic monitoring system in Baguio City, Philippines.

Your goal is to generate an optimal set of search queries that will retrieve relevant documents about the specified focus areas.

You have access to the following tools:
{tools}

Tool names: {tool_names}

STRICT FORMAT - Follow this EXACTLY:

Question: the input question you must answer
Thought: think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (must be valid JSON)
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation 2-3 times)
Thought: I have generated enough queries. I will now provide the final answer.
Final Answer: {{"strategy": "...", "queries": [...], "expected_results": [...]}}

RULES:
1. You MUST say "Final Answer:" before outputting JSON
2. Do NOT output JSON without "Final Answer:" prefix
3. After 3 tool calls, you MUST output Final Answer
4. Generate 3-6 queries covering: broad, targeted, and risk

Begin!

Question: {input}
{agent_scratchpad}""")


@dataclass
class QueryOrchestratorAgent:
    """ReAct-based adaptive query planner."""

    max_queries: int = 6
    max_iterations: int = 5
    fallback_focus: str = "public services"
    _llm: ChatGoogleGenerativeAI | None = field(default=None, init=False)
    _executor: AgentExecutor | None = field(default=None, init=False)

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """Lazy-load LLM instance."""
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=settings.gemini_api_key,
                temperature=0.3,
            )
        return self._llm

    def _get_tools(self) -> list[Tool]:
        """Build tool list for the ReAct agent."""
        return [
            Tool(
                name="analyze_focus_areas",
                func=analyze_focus_areas,
                description=(
                    "Analyze user's focus areas to determine search strategy. "
                    "Input: JSON with 'focus_areas' (list) and 'time_window' (string). "
                    "Returns analysis with recommended query types."
                ),
            ),
            Tool(
                name="generate_query",
                func=generate_query,
                description=(
                    "Generate an optimized search query. "
                    "Input: JSON with 'focus_area', 'query_type', 'time_window', 'keywords'. "
                    "Returns the generated query with metadata."
                ),
            ),
            Tool(
                name="evaluate_query",
                func=evaluate_query,
                description=(
                    "Evaluate if a query will yield good results. "
                    "Input: JSON with 'query' and 'intent'. "
                    "Returns quality score and feedback."
                ),
            ),
        ]

    def _build_executor(self) -> AgentExecutor:
        """Build the ReAct agent executor."""
        if self._executor is None:
            llm = self._get_llm()
            tools = self._get_tools()
            agent = create_react_agent(llm, tools, REACT_PROMPT)
            self._executor = AgentExecutor(
                agent=agent,
                tools=tools,
                max_iterations=self.max_iterations,
                verbose=True,  # Show full ReAct reasoning in console
                handle_parsing_errors=True,
                return_intermediate_steps=True,
            )
        return self._executor

    def run(self, request: SnapshotRequest) -> QueryPlan:
        """Generate a query plan using ReAct reasoning."""
        focus_values = request.focus_areas or [self.fallback_focus]
        time_window = request.time_window or "24h"

        logger.info(
            "[query_orchestrator] Starting ReAct planning",
            extra={"focus": focus_values, "window": time_window},
        )

        # Build input for the agent
        input_text = (
            f"Create a search query plan for Baguio City civic monitoring. "
            f"Focus areas: {', '.join(focus_values)}. "
            f"Time window: {time_window}. "
            f"Generate 3-6 optimized queries covering these areas."
        )

        try:
            executor = self._build_executor()
            result = executor.invoke({"input": input_text})
            
            # Parse the final answer
            final_output = result.get("output", "")
            steps = result.get("intermediate_steps", [])
            logger.info(f"[query_orchestrator] ReAct completed in {len(steps)} steps")
            
            plan = self._parse_output(final_output, focus_values, time_window)
            
        except Exception as exc:
            logger.warning(
                "[query_orchestrator] ReAct failed, using fallback: %s", exc
            )
            plan = self._fallback_plan(focus_values, time_window)

        logger.info(
            "[query_orchestrator] Plan ready",
            extra={"query_count": len(plan.queries), "strategy": plan.strategy[:100]},
        )
        return plan

    def _parse_output(
        self, output: str, focus_values: list[str], time_window: str
    ) -> QueryPlan:
        """Parse ReAct agent output into QueryPlan."""
        # Try to extract JSON from the output
        try:
            # Handle case where output is wrapped in markdown
            if "```json" in output:
                json_str = output.split("```json")[1].split("```")[0].strip()
            elif "```" in output:
                json_str = output.split("```")[1].split("```")[0].strip()
            else:
                # Try to find JSON object directly
                start = output.find("{")
                end = output.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = output[start:end]
                else:
                    raise ValueError("No JSON found in output")

            data = json.loads(json_str)
            
            queries = []
            for q in data.get("queries", []):
                queries.append(
                    QueryTask(
                        query=q.get("query", ""),
                        intent=q.get("intent", "broad"),
                        priority=q.get("priority", 1),
                    )
                )

            # Ensure we have at least some queries
            if not queries:
                return self._fallback_plan(focus_values, time_window)

            return QueryPlan(
                strategy=data.get("strategy", f"ReAct-planned queries for {', '.join(focus_values)}"),
                queries=queries[: self.max_queries],
                expected_results=data.get("expected_results", [])[:3],
            )

        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("[query_orchestrator] Failed to parse output: %s", exc)
            return self._fallback_plan(focus_values, time_window)

    def _fallback_plan(self, focus_values: list[str], time_window: str) -> QueryPlan:
        """Generate fallback plan when ReAct fails."""
        tasks: list[QueryTask] = []

        # Broad query
        tasks.append(
            QueryTask(
                query=f"Baguio City {', '.join(focus_values)} civic updates {time_window}",
                intent="broad",
                priority=1,
            )
        )

        # Targeted queries per focus area
        for idx, area in enumerate(focus_values, start=2):
            tasks.append(
                QueryTask(
                    query=f"{area} situation in Baguio City latest {time_window}",
                    intent="targeted",
                    priority=idx,
                )
            )

        # Risk query
        tasks.append(
            QueryTask(
                query=f"Baguio City civic risk alerts emergency {time_window}",
                intent="risk",
                priority=5,
            )
        )

        return QueryPlan(
            strategy=f"Fallback plan: {len(tasks)} queries for {', '.join(focus_values)}",
            queries=tasks[: self.max_queries],
            expected_results=[
                f"Validate latest developments for {area.lower()} in Baguio City"
                for area in focus_values
            ][:3],
        )
