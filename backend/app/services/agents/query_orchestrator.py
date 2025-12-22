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
       
        ["Baguio mallification protest", "SM Baguio expansion", "Baguio student protest market"],
       
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
    for cluster in clusters[:15]:  # Max 6 queries for full topic coverage
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


def expand_contextual_queries(input_str: str) -> str:
    """Generate contextual/seasonal queries based on current date and focus areas.
    
    This tool adds INTELLIGENCE to the agent by generating queries that static
    keyword clusters would miss - seasonal events, holidays, weather patterns, etc.
    
    Args:
        input_str: JSON with 'focus_areas', 'current_date', and optionally 'time_window'
    
    Returns:
        Contextual queries relevant to the current time period
    """
    try:
        data = json.loads(input_str)
        focus_areas = data.get("focus_areas", [])
        current_date = data.get("current_date", datetime.now().strftime("%B %Y"))
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"
    
    # Determine current context
    now = datetime.now()
    month = now.month
    
    # Seasonal/contextual mappings for Baguio City
    contextual_keywords = []
    
    # Holiday seasons
    if month == 12:
        contextual_keywords.extend([
            {"query": "Baguio Christmas traffic 2024", "topic": "holiday-traffic", "reason": "December holiday rush"},
            {"query": "Baguio New Year celebration safety", "topic": "holiday-safety", "reason": "New Year events"},
            {"query": "Baguio holiday tourist crowd", "topic": "holiday-tourism", "reason": "Peak tourist season"},
        ])
    elif month == 1:
        contextual_keywords.extend([
            {"query": "Baguio Panagbenga preparation 2025", "topic": "festival-prep", "reason": "Panagbenga planning"},
            {"query": "Baguio post-holiday cleanup", "topic": "post-holiday", "reason": "Post-New Year issues"},
        ])
    elif month == 2:
        contextual_keywords.extend([
            {"query": "Baguio Panagbenga festival 2025", "topic": "panagbenga", "reason": "Panagbenga Festival month"},
            {"query": "Baguio flower festival crowd", "topic": "festival-crowd", "reason": "Festival overcrowding"},
            {"query": "Baguio Valentine tourism", "topic": "valentine-tourism", "reason": "Valentine's Day tourism"},
        ])
    elif month in [3, 4, 5]:
        contextual_keywords.extend([
            {"query": "Baguio summer crowd 2025", "topic": "summer-tourism", "reason": "Summer vacation season"},
            {"query": "Baguio Holy Week traffic", "topic": "holy-week", "reason": "Holy Week travel"},
            {"query": "Baguio water shortage summer", "topic": "summer-water", "reason": "Dry season water issues"},
        ])
    elif month in [6, 7, 8, 9, 10]:
        contextual_keywords.extend([
            {"query": "Baguio typhoon update", "topic": "typhoon", "reason": "Typhoon season"},
            {"query": "Baguio landslide rainy season", "topic": "rainy-landslide", "reason": "Monsoon landslide risk"},
            {"query": "Baguio flooding news", "topic": "rainy-flood", "reason": "Rainy season flooding"},
            {"query": "Baguio school enrollment issue", "topic": "enrollment", "reason": "School opening season"},
        ])
    elif month == 11:
        contextual_keywords.extend([
            {"query": "Baguio All Saints Day crowd", "topic": "undas", "reason": "Undas/All Saints Day"},
            {"query": "Baguio Christmas preparation", "topic": "christmas-prep", "reason": "Early Christmas rush"},
        ])
    
    # Filter by focus areas if specified
    if focus_areas:
        focus_lower = [f.lower() for f in focus_areas]
        filtered = []
        
        # Map topics to focus areas
        topic_focus_map = {
            "holiday-traffic": ["infrastructure", "tourism", "safety"],
            "holiday-safety": ["safety"],
            "holiday-tourism": ["tourism", "economy"],
            "festival-prep": ["tourism", "infrastructure"],
            "panagbenga": ["tourism", "economy", "safety"],
            "festival-crowd": ["tourism", "safety", "infrastructure"],
            "valentine-tourism": ["tourism", "economy"],
            "summer-tourism": ["tourism", "economy", "infrastructure"],
            "holy-week": ["tourism", "infrastructure", "safety"],
            "summer-water": ["infrastructure", "health", "environment"],
            "typhoon": ["safety", "infrastructure", "environment"],
            "rainy-landslide": ["safety", "infrastructure", "environment"],
            "rainy-flood": ["safety", "infrastructure", "environment"],
            "enrollment": ["infrastructure", "economy"],
            "undas": ["tourism", "safety", "infrastructure"],
            "christmas-prep": ["tourism", "economy", "infrastructure"],
            "post-holiday": ["environment", "infrastructure"],
        }
        
        for kw in contextual_keywords:
            topic = kw.get("topic", "")
            relevant_areas = topic_focus_map.get(topic, [])
            if any(area in focus_lower for area in relevant_areas):
                filtered.append(kw)
        
        contextual_keywords = filtered if filtered else contextual_keywords[:2]
    
    return json.dumps({
        "contextual_queries": contextual_keywords[:3],  # Max 3 contextual queries
        "current_context": current_date,
        "reasoning": f"Generated {len(contextual_keywords[:3])} contextual queries based on {current_date} seasonal patterns",
        "instruction": "Add these to your final query list for time-relevant coverage"
    })


# ─────────────────────────────────────────────────────────────────────────────
# ReAct Agent
# ─────────────────────────────────────────────────────────────────────────────

REACT_PROMPT = PromptTemplate.from_template("""You are a search query optimization agent for Baguio City civic monitoring.

Your task: Create MULTIPLE DIVERSE search queries combining STATIC clusters AND CONTEXTUAL/SEASONAL queries.

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
1. Use analyze_focus_areas to get keyword CLUSTERS (static coverage)
2. Use generate_query with ALL clusters at once
3. Use expand_contextual_queries to get SEASONAL/TIME-RELEVANT queries (this is CRITICAL for intelligent search)
4. COMBINE both static and contextual queries in Final Answer

IMPORTANT: The expand_contextual_queries tool adds INTELLIGENCE by generating queries based on:
- Current month/season (typhoon season, summer, Christmas, Panagbenga)
- Holidays and events
- Weather patterns
This is what makes the agent SMART - static clusters alone are not enough!

Final Answer JSON format:
{{"strategy": "hybrid: static clusters + contextual expansion", "queries": [{{"query": "...", "topic": "...", "type": "static|contextual"}}], "expected_results": ["diverse results across topics and time-relevant events"]}}

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
                model="gemini-2.5-flash-lite",
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
                name="expand_contextual_queries",
                func=expand_contextual_queries,
                description=(
                    "Generate CONTEXTUAL/SEASONAL queries based on current date. "
                    "Input: JSON with 'focus_areas' list and 'current_date' string. "
                    "Returns time-relevant queries (holidays, weather, events) that static clusters miss. "
                    "CRITICAL: Always use this tool to add intelligent, time-aware queries!"
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
        """Generate query plan using TRUE ReAct agentic reasoning.
        
        AGENTIC STRATEGY (ReAct Pattern):
        1. Agent analyzes focus areas using tools
        2. Agent generates diverse queries through reasoning loop
        3. Agent evaluates query coverage before finalizing
        
        The agent autonomously decides:
        - How many queries to generate
        - Which keyword clusters to prioritize
        - Whether to add seasonal/contextual queries
        """
        focus_values = request.focus_areas or [self.fallback_focus]
        time_window = request.time_window or "24h"
        time_suffix = _get_time_search_suffix(time_window)
        current_date = datetime.now().strftime("%B %Y")

        logger.info(
            "[query_orchestrator] Starting ReAct Agentic Planning",
            extra={"focus": focus_values, "calendar": current_date},
        )

        # Build the ReAct agent executor
        try:
            executor = self._build_executor()
            
            # Invoke ReAct reasoning loop
            agent_input = (
                f"Create diverse search queries for Baguio City civic monitoring.\n"
                f"Focus areas: {', '.join(focus_values)}\n"
                f"Time window: {time_window}\n"
                f"Current date: {current_date}\n"
                f"IMPORTANT: Use analyze_focus_areas first, then generate_query for EACH cluster, "
                f"then evaluate_query to verify coverage."
            )
            
            result = executor.invoke({"input": agent_input})
            
            # Extract queries from agent output or intermediate steps
            output = result.get("output", "")
            steps = result.get("intermediate_steps", [])
            
            # Try to parse Final Answer JSON
            parsed_plan = self._parse_react_output(output, focus_values, time_suffix)
            if parsed_plan and parsed_plan.queries:
                logger.info(f"[query_orchestrator] ReAct produced {len(parsed_plan.queries)} queries")
                return parsed_plan
            
            # Fallback: extract from intermediate steps
            step_plan = self._extract_from_steps(steps, focus_values, time_window)
            if step_plan and step_plan.queries:
                logger.info(f"[query_orchestrator] Extracted {len(step_plan.queries)} queries from steps")
                return step_plan
                
        except Exception as e:
            logger.warning(f"[query_orchestrator] ReAct agent failed: {e}")
        
        # Ultimate fallback: deterministic query generation
        logger.info("[query_orchestrator] Using fallback query generation")
        return self._fallback_plan(focus_values, time_window)
    
    def _parse_react_output(self, output: str, focus_values: list[str], time_suffix: str) -> QueryPlan | None:
        """Parse the Final Answer from ReAct agent."""
        try:
            # Try to find JSON in output
            if "```json" in output:
                json_str = output.split("```json")[1].split("```")[0].strip()
            elif "{" in output and "}" in output:
                start = output.find("{")
                end = output.rfind("}") + 1
                json_str = output[start:end]
            else:
                return None
            
            data = json.loads(json_str)
            queries = []
            
            for q in data.get("queries", []):
                query_text = q.get("query", "")
                if query_text:
                    queries.append(QueryTask(
                        query=f"({query_text}){time_suffix}" if time_suffix not in query_text else query_text,
                        intent=q.get("intent", "targeted"),
                        topic=q.get("topic", "general"),
                        priority=len(queries) + 1
                    ))
            
            if queries:
                return QueryPlan(
                    strategy=data.get("strategy", f"ReAct-planned for {', '.join(focus_values)}"),
                    queries=queries,
                    expected_results=data.get("expected_results", [f"Diverse coverage for {', '.join(focus_values)}"])
                )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"[query_orchestrator] Failed to parse ReAct output: {e}")
        
        return None

    def _parse_output(self, output: str, focus_values: list[str], steps: list | None = None, time_window: str | None = None) -> QueryPlan:
        """(Deprecated) Parse ReAct output."""
        return self.run(SnapshotRequest(focus_areas=focus_values, time_window=time_window))

    def _extract_from_steps(self, steps: list, focus_values: list[str], time_window: str | None = None) -> QueryPlan:
        """Extract queries from intermediate steps, accumulating from ALL tool calls."""
        time_suffix = _get_time_search_suffix(time_window)
        all_queries = []
        static_count = 0
        contextual_count = 0
        
        for step in steps:
            if len(step) >= 2:
                action, observation = step[0], step[1]
                
                # Extract from generate_query (static clusters)
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
                                    static_count += 1
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                # Extract from expand_contextual_queries (seasonal/contextual)
                elif hasattr(action, 'tool') and action.tool == "expand_contextual_queries":
                    try:
                        result = json.loads(observation) if isinstance(observation, str) else observation
                        if isinstance(result, dict) and result.get("contextual_queries"):
                            for q in result["contextual_queries"]:
                                query_text = q.get("query", "") if isinstance(q, dict) else q
                                topic_name = q.get("topic", "contextual") if isinstance(q, dict) else "contextual"
                                if query_text:
                                    all_queries.append(QueryTask(
                                        query=f"({query_text}){time_suffix}",
                                        intent="trend",  # Contextual queries are trend-focused
                                        topic=f"ctx-{topic_name}",
                                        priority=len(all_queries) + 1
                                    ))
                                    contextual_count += 1
                    except (json.JSONDecodeError, TypeError):
                        continue
        
        if all_queries:
            logger.info(
                "[query_orchestrator] Extracted %d queries from steps (static=%d, contextual=%d)", 
                len(all_queries), static_count, contextual_count
            )
            return QueryPlan(
                strategy=f"Hybrid: {static_count} static + {contextual_count} contextual queries",
                queries=all_queries, 
                expected_results=[f"Diverse results for {', '.join(focus_values)} with seasonal awareness"],
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
