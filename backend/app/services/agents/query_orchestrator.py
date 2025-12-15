"""ReAct-based query orchestrator that creates optimized search prompts for retrieval.

Multi-query strategy for result diversity:
- Groups keywords into topic clusters (3-4 keywords each)
- Generates separate queries per cluster
- Results are merged with diversity enforcement in retrieval agent
"""
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
from ...core.telemetry import measure_performance
from ...schemas.snapshot import SnapshotRequest
from ...schemas.query import QueryPlan, QueryTask
from ...services.insights.agent_tools import FOCUS_CONCERN_KEYWORDS

warnings.filterwarnings("ignore", message="Error in StdOutCallbackHandler")
logging.getLogger("langchain_core.callbacks.manager").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
settings = get_settings()

# Keyword clusters for diversity - group related terms together
KEYWORD_CLUSTERS: dict[str, list[list[str]]] = {
    "infrastructure": [
        ["Baguio traffic congestion", "Session Road rehabilitation", "Baguio public transport"],
        ["Baguio road repair", "Kennon Road closure", "Baguio construction delay"],
        ["Baguio water shortage", "Baguio drainage issue", "Baguio power outage"],
        ["Baguio parking problem", "Baguio internet problem", "Baguio jeepney modernization"],
    ],
    "health": [
        ["Baguio hospital issue", "BGH Baguio problem", "Baguio emergency room"],
        ["Baguio dengue outbreak", "Baguio COVID update", "Baguio vaccination"],
        ["Baguio healthcare concern", "Baguio doctor shortage", "Baguio medicine shortage"],
        ["Baguio mental health", "Baguio medical services", "Baguio health center"],
    ],
    "safety": [
        ["Baguio crime incident", "Baguio theft problem", "Baguio police operation"],
        ["Baguio landslide warning", "Baguio earthquake drill", "Baguio disaster preparedness"],
        ["Baguio fire incident", "Baguio accident report", "Baguio road accident"],
        ["Baguio emergency response", "Baguio missing person", "Baguio evacuation"],
        ["Baguio flood control", "Baguio corruption issue", "Baguio flood control corruption"],
        ["Baguio students walkout", "Baguio student protest", "Baguio youth rally"],
    ],
    "tourism": [
        ["Baguio tourist complaint", "Baguio scam tourist", "Baguio tourist trap"],
        ["Baguio overcrowding", "Session Road crowd", "Baguio weekend traffic"],
        ["Burnham Park problem", "Panagbenga issue", "Baguio travel advisory"],
        ["Baguio hotel issue", "Baguio accommodation problem", "Baguio tour package complaint"],
    ],
    "economy": [
        ["Baguio vendor issue", "Baguio vendor displacement", "Baguio market problem"],
        ["Baguio mallification protest", "SM Baguio expansion", "Baguio student protest market"],
        ["Baguio business closure", "Baguio unemployment", "Baguio job hiring"],
        ["Baguio public market", "Baguio cost of living", "Baguio livelihood program"],
    ],
    "environment": [
        ["Baguio tree cutting", "Baguio pine trees", "Baguio green space"],
        ["Baguio air pollution", "Baguio water pollution", "Baguio environmental concern"],
        ["Baguio flooding", "Baguio waste management", "Baguio garbage problem"],
        ["Baguio urban development", "Baguio climate change", "Baguio illegal dumping"],
    ],
}


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

def analyze_focus_areas(input_str: str) -> str:
    """Analyze focus areas and retrieve keyword clusters for diverse queries.
    
    Args:
        input_str: JSON with 'focus_areas' list
    
    Returns:
        Keyword clusters organized by topic for multi-query generation
    """
    try:
        data = json.loads(input_str)
        focus_areas = data.get("focus_areas", [])
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    all_clusters: list[dict] = []
    
    for area in focus_areas:
        area_lower = area.lower()
        clusters = KEYWORD_CLUSTERS.get(area_lower, [])
        for i, cluster in enumerate(clusters):
            all_clusters.append({
                "area": area,
                "cluster_id": f"{area_lower}_{i+1}",
                "keywords": cluster,
                "topic": cluster[0].replace("Baguio ", "").replace(" issue", "").replace(" problem", ""),
            })

    return json.dumps({
        "total_clusters": len(all_clusters),
        "clusters": all_clusters,
        "instruction": "Generate ONE query per cluster for result diversity. Use looser matching (no quotes) for broader results."
    })


def generate_query(input_str: str) -> str:
    """Generate diverse queries from keyword clusters.
    
    Args:
        input_str: JSON with 'clusters' list from analyze_focus_areas
    
    Returns:
        Multiple queries for diverse result coverage
    """
    try:
        data = json.loads(input_str)
        clusters = data.get("clusters", [])
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    if not clusters:
        return json.dumps({
            "queries": [{"query": "Baguio City civic concerns news", "topic": "general"}],
            "type": "fallback"
        })

    queries = []
    for cluster in clusters[:6]:  # Max 6 queries for full topic coverage
        keywords = cluster.get("keywords", [])
        topic = cluster.get("topic", "general")
        
        # Use looser matching: mix quoted and unquoted terms
        # First term exact, others loose for broader matching
        if len(keywords) >= 2:
            query = f'"{keywords[0]}" OR {keywords[1]}'
            if len(keywords) >= 3:
                query += f' OR {keywords[2]}'
        elif keywords:
            query = keywords[0]
        else:
            continue
            
        queries.append({
            "query": f"({query})",
            "topic": topic,
            "cluster_id": cluster.get("cluster_id", "unknown"),
        })

    return json.dumps({
        "queries": queries,
        "query_count": len(queries),
        "type": "diverse_multi_query"
    })


def evaluate_query(input_str: str) -> str:
    """Evaluate if queries cover diverse topics.
    
    Args:
        input_str: JSON with 'queries' list and 'focus_areas'
    
    Returns:
        Diversity assessment
    """
    try:
        data = json.loads(input_str)
        queries = data.get("queries", [])
        focus_areas = data.get("focus_areas", [])
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    topics_covered = set()
    for q in queries:
        topic = q.get("topic", "")
        if topic:
            topics_covered.add(topic)
    
    # Check cluster coverage per focus area
    coverage = []
    for area in focus_areas:
        area_lower = area.lower()
        total_clusters = len(KEYWORD_CLUSTERS.get(area_lower, []))
        covered = sum(1 for q in queries if q.get("cluster_id", "").startswith(area_lower))
        coverage.append({
            "area": area,
            "clusters_covered": f"{covered}/{total_clusters}",
            "sufficient": covered >= 2,  # At least 2 clusters per area
        })

    return json.dumps({
        "topics_covered": list(topics_covered),
        "topic_count": len(topics_covered),
        "coverage": coverage,
        "diverse": len(topics_covered) >= len(queries) * 0.75,
        "recommendation": "Good diversity" if len(topics_covered) >= 3 else "Add more topic variety"
    })


# ─────────────────────────────────────────────────────────────────────────────
# ReAct Agent
# ─────────────────────────────────────────────────────────────────────────────

REACT_PROMPT = PromptTemplate.from_template("""You are a search query optimization agent for Baguio City civic monitoring.

Your task: Create MULTIPLE DIVERSE search queries to ensure broad topic coverage.

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
Thought: I have crafted diverse queries.
Final Answer: [JSON with strategy and queries]

WORKFLOW:
1. Use analyze_focus_areas to get keyword CLUSTERS (grouped by topic)
2. Use generate_query with the clusters to create MULTIPLE queries (one per topic cluster)
3. Optionally use evaluate_query to verify topic diversity
4. Output Final Answer with ALL queries

Final Answer JSON format:
{{"strategy": "multi-query for topic diversity", "queries": [{{"query": "...", "topic": "..."}}], "expected_results": ["diverse results across topics"]}}

CRITICAL: Generate ONE query for EACH provided focus area (up to max, default 6). Coverage for ALL requested areas is required. Do NOT combine all keywords into one query.

Begin!

Question: {input}
{agent_scratchpad}""")


@dataclass
class QueryOrchestratorAgent:
    """ReAct agent that creates diverse search queries for broad topic coverage."""

    max_queries: int = 6  # Up to 6 diverse queries
    max_iterations: int = 5
    fallback_focus: str = "public services"
    _llm: ChatGoogleGenerativeAI | None = field(default=None, init=False)
    _executor: AgentExecutor | None = field(default=None, init=False)

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """Get Gemini LLM for query generation."""
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.gemini_api_key,
                temperature=0.2,
            )
        return self._llm

    def _get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="analyze_focus_areas",
                func=analyze_focus_areas,
                description=(
                    "Analyze focus areas and retrieve ALL curated concern keywords. "
                    "Input: JSON with 'focus_areas' list. "
                    "Returns all keywords to include in the search query."
                ),
            ),
            Tool(
                name="generate_query",
                func=generate_query,
                description=(
                    "Generate diverse search queries from keyword clusters. "
                    "Input: JSON with 'clusters' list from analyze_focus_areas. "
                    "Returns multiple queries for topic diversity."
                ),
            ),
            Tool(
                name="evaluate_query",
                func=evaluate_query,
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

    @measure_performance(component="QueryOrchestratorAgent", operation="run_planning")
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
        """Parse ReAct output into QueryPlan with multiple diverse queries."""
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
                if isinstance(q, str):
                    query_text = q
                    topic_name = f"topic_{idx+1}"
                else:
                    query_text = q.get("query", "")
                    topic_name = q.get("topic", f"topic_{idx+1}")
                
                if query_text:
                    query_with_time = f"{query_text}{time_suffix}"
                    queries.append(QueryTask(
                        query=query_with_time, 
                        intent="targeted",
                        topic=topic_name,
                        priority=idx + 1
                    ))

            if not queries:
                if steps:
                    return self._extract_from_steps(steps, focus_values, time_window)
                return self._fallback_plan(focus_values, time_window)

            logger.info("[query_orchestrator] Generated %d diverse queries with time suffix: %s", 
                       len(queries), time_suffix or "(none)")
            
            return QueryPlan(
                strategy=data.get("strategy", f"Multi-query diversity for {', '.join(focus_values)}"),
                queries=queries[:self.max_queries],
                expected_results=data.get("expected_results", [])[:3],
            )

        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("[query_orchestrator] Parse failed: %s", exc)
            if steps:
                return self._extract_from_steps(steps, focus_values, time_window)
            return self._fallback_plan(focus_values, time_window)

    def _extract_from_steps(self, steps: list, focus_values: list[str], time_window: str | None = None) -> QueryPlan:
        """Extract queries from intermediate steps, accumulating from ALL tool calls."""
        time_suffix = _get_time_search_suffix(time_window)
        all_queries = []
        
        for step in steps:
            if len(step) >= 2:
                action, observation = step[0], step[1]
                if hasattr(action, 'tool') and action.tool == "generate_query":
                    try:
                        result = json.loads(observation) if isinstance(observation, str) else observation
                        if isinstance(result, dict) and result.get("queries"):
                            for idx, q in enumerate(result["queries"]):
                                query_text = q.get("query", "") if isinstance(q, dict) else q
                                topic_name = q.get("topic", f"topic_{len(all_queries)+1}") if isinstance(q, dict) else f"topic_{len(all_queries)+1}"
                                if query_text:
                                    all_queries.append(QueryTask(
                                        query=f"{query_text}{time_suffix}",
                                        intent="targeted",
                                        topic=topic_name,
                                        priority=len(all_queries) + 1
                                    ))
                    except (json.JSONDecodeError, TypeError):
                        continue
        
        if all_queries:
            # If we have more queries than max, simplistic slice might drop entire categories if mostly from step 1.
            # But usually max_queries is 6. If we generated 18, we have a problem.
            # Let's trust the agent to manage count or just return them all (retrieval agent handles batches).
            # The retrieval agent handles parallel batching, so 12-18 queries is fine, just more time.
            # We will NOT slice here to ensure coverage, but let RetrievalAgent verify.
            # Actually, RetrievalAgent respects the list length. Let's allow up to 12.
            
            logger.info("[query_orchestrator] Extracted %d queries from steps", len(all_queries))
            return QueryPlan(
                strategy=f"Multi-query with {len(all_queries)} topic clusters",
                queries=all_queries, 
                expected_results=[f"Diverse results for {', '.join(focus_values)}"],
            )
            
        return self._fallback_plan(focus_values, time_window)

    def _fallback_plan(self, focus_values: list[str], time_window: str | None = None) -> QueryPlan:
        """Direct fallback using keyword clusters for diversity."""
        time_suffix = _get_time_search_suffix(time_window)
        
        queries = []
        for area in focus_values:
            area_lower = area.lower()
            clusters = KEYWORD_CLUSTERS.get(area_lower, [])
            
            # Take first 2 clusters per area for diversity
            for i, cluster in enumerate(clusters[:2]):
                if len(cluster) >= 2:
                    # Mix exact and loose matching
                    query = f'("{cluster[0]}" OR {cluster[1]})'
                elif cluster:
                    query = cluster[0]
                else:
                    continue
                
                queries.append(QueryTask(
                    query=f"{query}{time_suffix}",
                    intent="targeted",
                    topic=cluster[0].replace("Baguio ", ""),
                    priority=len(queries) + 1
                ))
                
                if len(queries) >= self.max_queries:
                    break
            
            if len(queries) >= self.max_queries:
                break
        
        if not queries:
            # Ultimate fallback
            query = f"Baguio City {' '.join(focus_values)} problem OR concern{time_suffix}"
            queries = [QueryTask(query=query, intent="broad", topic="general", priority=1)]
        
        logger.info("[query_orchestrator] Fallback: %d diverse queries", len(queries))
        
        return QueryPlan(
            strategy=f"Fallback multi-query for {', '.join(focus_values)}",
            queries=queries,
            expected_results=[f"Diverse results for {', '.join(focus_values)} concerns"],
        )
