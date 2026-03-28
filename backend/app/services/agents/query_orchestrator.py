"""Query Orchestrator Agent with true AI-powered query synthesis.

Agentic query generation strategy:
- ReAct agent retrieves domain knowledge and temporal context via tools
- Agent REASONS about what search queries would uncover real civic concerns
- Agent GENERATES diverse, targeted queries autonomously (not copy-paste)
- Memory integration provides past discoveries to avoid redundant searches
- Fallback to deterministic generation if agent fails

Key difference from previous static approach:
- OLD: Tools mechanically formatted keywords into "kw1 OR kw2" templates
- NEW: Tools provide context; the AGENT generates queries through reasoning
"""
from __future__ import annotations

import asyncio
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
from .concerns_memory import get_concerns_memory, DEFAULT_EMERGING_CONCERNS

warnings.filterwarnings("ignore", message="Error in StdOutCallbackHandler")
logging.getLogger("langchain_core.callbacks.manager").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
settings = get_settings()

# Self-Learning Configuration (loaded from settings)
CONCERNS_TTL_DAYS = getattr(settings, 'concerns_memory_ttl_days', 7)

# Module-level concerns (backward-compat for tests/external config)
EMERGING_CONCERNS: dict[str, list[list[str]]] = {}
_emerging_concerns: dict[str, list[list[str]]] = {}
_fallback_used = False


def set_emerging_concerns(concerns: dict[str, list[list[str]]]) -> None:
    """Set dynamic emerging concerns (for testing or external configuration)."""
    global EMERGING_CONCERNS, _emerging_concerns
    _emerging_concerns = concerns
    EMERGING_CONCERNS = concerns
    logger.info(f"[QueryOrchestrator] Loaded {sum(len(v) for v in concerns.values())} concern areas")


def get_fallback_status() -> bool:
    """Check if fallback was used (for testing/metrics)."""
    return _fallback_used


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
# Tool Functions (Information Providers — NOT query generators)
#
# These tools provide RAW CONTEXT for the ReAct agent to reason over.
# The AGENT decides what queries to generate based on this context.
# ─────────────────────────────────────────────────────────────────────────────

def get_domain_context(input_str: str) -> str:
    """Provide domain knowledge and past discoveries for the agent to reason over.

    Returns:
    1. Domain knowledge from FOCUS_CONCERN_KEYWORDS (linearized knowledge graph)
    2. Past discoveries from Qdrant memory (to avoid redundancy)

    The AGENT decides what queries to generate based on this context.
    """
    try:
        data = json.loads(input_str)
        focus_areas = data.get("focus_areas", [])
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    # 1. Domain knowledge from FOCUS_CONCERN_KEYWORDS (inductive bias)
    domain_knowledge = {}
    for area in focus_areas:
        area_lower = area.lower()
        keywords = FOCUS_CONCERN_KEYWORDS.get(area_lower, [])
        domain_knowledge[area] = {
            "known_concern_topics": keywords,
            "total_topics": len(keywords),
        }

    # 2. Past discoveries from memory (avoid redundancy)
    past_discoveries = {}
    try:
        memory = get_concerns_memory()
        cached = memory.recall_concerns(
            focus_areas=focus_areas,
            max_clusters_per_area=4,
            max_age_days=CONCERNS_TTL_DAYS
        )
        if cached:
            past_discoveries = cached
            logger.info(
                "[get_domain_context] Recalled %d past discovery clusters",
                sum(len(v) for v in cached.values())
            )
    except Exception as e:
        logger.warning(f"[get_domain_context] Memory recall failed: {e}")

    return json.dumps({
        "domain_knowledge": domain_knowledge,
        "past_discoveries": past_discoveries,
        "focus_areas": focus_areas,
        "instruction": (
            "Use this domain knowledge as INSPIRATION, not as copy-paste source. "
            "Generate NOVEL search queries that target specific angles and sub-topics. "
            "Your queries should discover what people are ACTUALLY complaining about."
        )
    })


def get_temporal_context(input_str: str) -> str:
    """Provide temporal awareness for seasonally-relevant query generation.

    Returns current date, season, and relevant Baguio City events/patterns
    so the agent can generate time-aware queries autonomously.
    """
    try:
        data = json.loads(input_str)
        focus_areas = data.get("focus_areas", [])
        time_window = data.get("time_window", "24h")
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    now = datetime.now()
    month = now.month
    year = now.year
    time_suffix = _get_time_search_suffix(time_window)

    seasonal_info = {
        "current_date": now.strftime("%B %d, %Y"),
        "month": month,
        "year": year,
        "day_of_week": now.strftime("%A"),
        "time_suffix": time_suffix,
        "time_window": time_window,
    }

    # Baguio City calendar facts (factual data for the agent to reason about)
    calendar_facts = []

    if month == 12:
        calendar_facts = [
            "Peak Christmas tourism season in Baguio",
            "Christmas Village at Burnham Park draws massive crowds",
            "Heavy traffic on Marcos Highway and Kennon Road",
            "Night Market and Session Road pedestrianized for holidays",
            "Cold weather attracts domestic tourists",
            "New Year celebration preparations",
        ]
    elif month == 1:
        calendar_facts = [
            "Post-holiday period, Panagbenga Festival preparation begins",
            "Coldest month in Baguio (temperatures can drop to 6°C)",
            "Strawberry picking season at La Trinidad",
            "Fire safety month awareness",
            "Dry season begins",
        ]
    elif month == 2:
        calendar_facts = [
            f"Panagbenga Flower Festival month ({year})",
            "Grand Float Parade and Street Dancing events",
            "Session Road closed for festival events",
            "Valentine's Day tourism surge",
            "Peak strawberry season at La Trinidad",
            "Massive crowd management needed citywide",
        ]
    elif month in [3, 4, 5]:
        month_name = {3: "March", 4: "April", 5: "May"}[month]
        calendar_facts = [
            f"{month_name}: Summer/dry season in Baguio",
            "Peak domestic tourism, school vacation travel",
            "Water shortage concerns during dry season",
            "Fire hazard risks increase",
            "Holy Week travel surge (March/April)",
        ]
        if month == 4:
            calendar_facts.append("April 24: Cordillera Day celebration")
    elif month in [6, 7, 8, 9, 10]:
        calendar_facts = [
            "Monsoon/rainy season active",
            "Typhoon season — landslide and flooding risks elevated",
            "School opening season (June)",
            "Rainy season infrastructure challenges",
            "Reduced tourism but ongoing local concerns",
        ]
        if month == 9:
            calendar_facts.append("September 1: Baguio City Charter Day")
    elif month == 11:
        calendar_facts = [
            "All Saints' Day (Undas) travel and cemetery crowds",
            "Early Christmas preparations and shopping",
            "Holiday traffic increases begin",
        ]

    seasonal_info["calendar_facts"] = calendar_facts
    seasonal_info["instruction"] = (
        "Use these temporal facts to generate TIME-RELEVANT queries. "
        "IMPORTANT: Append the time_suffix to EVERY query you generate."
    )

    return json.dumps(seasonal_info)


def validate_query_diversity(input_str: str) -> str:
    """Evaluate if generated queries cover diverse topics and focus areas."""
    try:
        data = json.loads(input_str)
        queries = data.get("queries", [])
        focus_areas = data.get("focus_areas", [])
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"

    topics_covered = set()
    focus_coverage = {area.lower(): 0 for area in focus_areas}

    for q in queries:
        topic = q.get("topic", "")
        if topic:
            topics_covered.add(topic)
        fa = q.get("focus_area", "").lower()
        if fa in focus_coverage:
            focus_coverage[fa] += 1

    uncovered = [area for area, count in focus_coverage.items() if count == 0]

    return json.dumps({
        "total_queries": len(queries),
        "unique_topics": len(topics_covered),
        "focus_area_coverage": focus_coverage,
        "uncovered_areas": uncovered,
        "is_diverse": len(uncovered) == 0 and len(topics_covered) >= len(queries) * 0.7,
        "recommendation": (
            f"Missing coverage for: {', '.join(uncovered)}. Add queries for these areas."
            if uncovered else
            "Good diversity! All focus areas covered with unique topics."
        )
    })


# ─────────────────────────────────────────────────────────────────────────────
# ReAct Agent Prompt — Agent generates queries through REASONING
# ─────────────────────────────────────────────────────────────────────────────

REACT_PROMPT = PromptTemplate.from_template(
    """You are a civic intelligence analyst specializing in Baguio City, Philippines.

Your task: Generate diverse web search queries to discover real-time public concerns.

CRITICAL RULES:
1. You must GENERATE your own search queries — do NOT copy keywords from tools verbatim
2. Queries must be natural-language phrases people would actually use when discussing issues
3. Each query must target a SPECIFIC angle (not generic like "Baguio traffic")
4. Include the time filter suffix (after:YYYY-MM-DD) in EVERY query
5. Mix: complaint-focused, news-focused, and discussion-focused queries
6. Cover DIFFERENT sub-topics within each focus area
7. At least 1 query per area should target emerging or unexpected issues

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
Thought: I have the context I need. Now I will GENERATE diverse queries using my analysis.
Final Answer: [JSON with queries]

WORKFLOW:
1. Use get_domain_context ONCE to understand what topics matter for each focus area
2. Use get_temporal_context ONCE to understand current season/events
3. REASON deeply: What specific searches would uncover real civic complaints and news?
4. Generate 8-12 diverse queries covering ALL requested focus areas
5. Output Final Answer with your AI-generated queries

EXAMPLES of GOOD vs BAD queries:
✅ "Session Road rehabilitation delay commuter complaint" (specific angle)
✅ "BGH emergency room overcrowding patient wait time" (targeted concern)
✅ "Kennon Road landslide warning today update" (timely + specific)
✅ "Baguio public market vendor displacement SM expansion" (concrete issue)
❌ "Baguio traffic congestion" (too generic, just a keyword)
❌ "Baguio problem issue concern" (not how people search)

Final Answer MUST be valid JSON:
{{"strategy": "AI-synthesized agentic queries with domain + temporal analysis", "queries": [{{"query": "your generated query after:YYYY-MM-DD", "topic": "specific-sub-topic", "focus_area": "parent-area", "intent": "targeted"}}], "expected_results": ["description of what these queries should find"]}}

Begin!

Question: {input}
{agent_scratchpad}"""
)


# ─────────────────────────────────────────────────────────────────────────────
# QueryOrchestratorAgent Class
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QueryOrchestratorAgent:
    """ReAct agent that creates diverse search queries through AI reasoning.

    Truly agentic approach:
    - Tools provide domain knowledge and temporal context (information)
    - Agent REASONS about what queries would uncover civic concerns
    - Agent GENERATES novel queries (not copy-paste from keyword lists)
    """

    max_queries: int = 12
    max_iterations: int = 6
    fallback_focus: str = "public services"
    _llm: ChatGoogleGenerativeAI | None = field(default=None, init=False)
    _executor: AgentExecutor | None = field(default=None, init=False)

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """Get Gemini 2.5 Flash Lite for ultra-fast agentic query synthesis.

        Using Gemini 2.5 Flash Lite:
        - 2x FASTER than Groq Compound (200-400ms vs 500-800ms per inference)
        - Lower latency from Asia-Pacific
        - Optimized for ReAct patterns with tool calls
        - Cost: $0.075/1M tokens (very low usage)
        """
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                google_api_key=settings.gemini_api_key,
                temperature=0.4,  # Balanced: creative enough for novel queries
            )
            logger.info("[QueryOrchestrator] Using Gemini 2.5 Flash Lite for agentic query synthesis")
        return self._llm

    def _get_tools(self) -> list[Tool]:
        """Information-provider tools (NOT query generators).

        The agent calls these to gather context, then generates queries itself.
        """
        return [
            Tool(
                name="get_domain_context",
                func=get_domain_context,
                description=(
                    "Retrieve domain knowledge for focus areas including known concern "
                    "topics and past discoveries from memory. "
                    "Input: JSON with 'focus_areas' list. "
                    "Use this as INSPIRATION for generating your own queries."
                ),
            ),
            Tool(
                name="get_temporal_context",
                func=get_temporal_context,
                description=(
                    "Get current date, season, and Baguio City events/calendar facts. "
                    "Input: JSON with 'focus_areas' and 'time_window'. "
                    "Use this to make your queries time-relevant and seasonal."
                ),
            ),
            Tool(
                name="validate_query_diversity",
                func=validate_query_diversity,
                description=(
                    "Check if your generated queries cover all focus areas diversely. "
                    "Input: JSON with 'queries' list and 'focus_areas'. "
                    "Use this ONLY if you want to verify quality before Final Answer."
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
    async def run(self, request: SnapshotRequest) -> QueryPlan:
        """Generate query plan using AI-powered agentic reasoning.

        AGENTIC STRATEGY:
        1. Agent retrieves domain knowledge and temporal context via tools
        2. Agent REASONS about what queries would discover civic concerns
        3. Agent GENERATES diverse queries autonomously
        4. Fallback to deterministic generation if agent fails

        The agent autonomously decides:
        - What specific search queries to create
        - How to phrase queries for maximum discovery
        - Which angles and sub-topics to target
        - How to integrate temporal/seasonal awareness
        """
        focus_values = request.focus_areas or [self.fallback_focus]
        time_window = request.time_window or "24h"
        time_suffix = _get_time_search_suffix(time_window)
        current_date = datetime.now().strftime("%B %d, %Y")

        logger.info(
            "[query_orchestrator] Starting AI-Powered Agentic Query Synthesis",
            extra={"focus": focus_values, "calendar": current_date},
        )

        # Background: populate memory for future context enrichment
        await self._populate_memory_if_needed(focus_values)

        # Run the ReAct agent
        try:
            executor = self._build_executor()

            target_count = min(len(focus_values) * 3, self.max_queries)
            agent_input = (
                f"Generate diverse search queries for Baguio City civic monitoring.\n"
                f"Focus areas: {', '.join(focus_values)}\n"
                f"Time window: {time_window}\n"
                f"Time suffix to append to ALL queries: {time_suffix}\n"
                f"Current date: {current_date}\n\n"
                f"WORKFLOW: Call get_domain_context ONCE, then get_temporal_context ONCE, "
                f"then GENERATE {target_count} diverse queries in your Final Answer."
            )

            result = await executor.ainvoke({"input": agent_input})

            output = result.get("output", "")
            steps = result.get("intermediate_steps", [])

            # Parse the agent's Final Answer
            parsed_plan = self._parse_synthesis_output(output, focus_values, time_suffix)
            if parsed_plan and parsed_plan.queries:
                logger.info(
                    "[query_orchestrator] AI agent synthesized %d queries",
                    len(parsed_plan.queries)
                )
                # Store generated queries as concerns for future memory
                self._store_queries_as_concerns(parsed_plan.queries, focus_values)
                return parsed_plan

            # Attempt extraction from raw output text
            extracted = self._extract_queries_from_text(output, focus_values, time_suffix)
            if extracted and extracted.queries:
                logger.info(
                    "[query_orchestrator] Extracted %d queries from agent text",
                    len(extracted.queries)
                )
                return extracted

        except Exception as e:
            logger.warning(f"[query_orchestrator] AI agent failed: {e}")

        # Ultimate fallback: deterministic query generation
        logger.info("[query_orchestrator] Using fallback query generation")
        return self._fallback_plan(focus_values, time_window)

    async def _populate_memory_if_needed(self, focus_values: list[str]) -> None:
        """Populate concerns memory if stale (for future context enrichment)."""
        try:
            memory = get_concerns_memory()
            cached = memory.recall_concerns(
                focus_areas=focus_values, max_age_days=CONCERNS_TTL_DAYS
            )
            if cached:
                return  # Memory is fresh, no action needed

            # Generate and store new concern keywords via lightweight LLM call
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                google_api_key=settings.gemini_api_key,
                temperature=0.7,
            )

            prompt = (
                f"Generate 4 diverse emerging concern keyword clusters for each "
                f"focus area: {', '.join(focus_values)}.\n"
                f"Each cluster: 2-3 related keywords specific to Baguio City.\n"
                f'Return JSON: {{"focus_area": [["kw1", "kw2", "kw3"], ...], ...}}'
            )

            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            if "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                concerns = json.loads(content[start:end])

                if isinstance(concerns, dict):
                    memory.store_concerns(concerns, source="llm")
                    logger.info(
                        "[query_orchestrator] Stored %d concern clusters to memory",
                        sum(len(v) for v in concerns.values())
                    )
        except Exception as e:
            logger.debug(f"[query_orchestrator] Memory population skipped: {e}")

    def _store_queries_as_concerns(
        self, queries: list[QueryTask], focus_values: list[str]
    ) -> None:
        """Store AI-generated query topics back to memory for self-learning."""
        try:
            memory = get_concerns_memory()
            concerns_by_area: dict[str, list[list[str]]] = {}

            for q in queries:
                # Extract meaningful terms from the query
                clean = q.query.split(" after:")[0].strip("()")
                # Use focus_area from QueryTask if available, otherwise fall back to topic parsing
                area = q.focus_area.lower() if q.focus_area else (
                    q.topic.split("-")[0].lower() if "-" in q.topic else
                    (focus_values[0].lower() if focus_values else "general")
                )
                concerns_by_area.setdefault(area, []).append(
                    [term.strip('" ') for term in clean.split(" OR ")[:3] if term.strip('" ')]
                )

            if concerns_by_area:
                memory.store_concerns(concerns_by_area, source="agent_synthesis")
                logger.info(
                    "[query_orchestrator] Stored %d synthesized concern clusters",
                    sum(len(v) for v in concerns_by_area.values())
                )
        except Exception:
            pass  # Non-critical; don't block the pipeline

    def _parse_synthesis_output(
        self, output: str, focus_values: list[str], time_suffix: str
    ) -> QueryPlan | None:
        """Parse the AI agent's Final Answer into a QueryPlan."""
        try:
            # Extract JSON from output
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
                if not query_text:
                    continue

                # Ensure time suffix is present
                if time_suffix and time_suffix.strip() not in query_text:
                    query_text = f"({query_text}){time_suffix}"

                # Validate intent against allowed values
                raw_intent = q.get("intent", "targeted")
                valid_intents = {"broad", "targeted", "trend", "risk"}
                intent = raw_intent if raw_intent in valid_intents else "targeted"

                queries.append(QueryTask(
                    query=query_text,
                    intent=intent,
                    topic=q.get("topic", "general"),
                    priority=len(queries) + 1,
                ))

            if queries:
                return QueryPlan(
                    strategy=data.get(
                        "strategy",
                        f"AI-synthesized agentic queries for {', '.join(focus_values)}"
                    ),
                    queries=queries[:self.max_queries],
                    expected_results=data.get(
                        "expected_results",
                        [f"Diverse civic concerns for {', '.join(focus_values)}"]
                    ),
                )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"[query_orchestrator] Failed to parse synthesis output: {e}")

        return None

    def _extract_queries_from_text(
        self, output: str, focus_values: list[str], time_suffix: str
    ) -> QueryPlan | None:
        """Last-resort: extract any query-like JSON objects from raw agent text."""
        import re

        json_blocks = re.findall(r'\{[^{}]*"query"[^{}]*\}', output)
        queries = []

        for block in json_blocks:
            try:
                q = json.loads(block)
                query_text = q.get("query", "")
                if query_text and "baguio" in query_text.lower():
                    if time_suffix and time_suffix.strip() not in query_text:
                        query_text = f"({query_text}){time_suffix}"

                    raw_intent = q.get("intent", "targeted")
                    valid_intents = {"broad", "targeted", "trend", "risk"}
                    intent = raw_intent if raw_intent in valid_intents else "targeted"

                    queries.append(QueryTask(
                        query=query_text,
                        intent=intent,
                        topic=q.get("topic", "general"),
                        priority=len(queries) + 1,
                    ))
            except json.JSONDecodeError:
                continue

        if queries:
            return QueryPlan(
                strategy=f"AI-extracted queries for {', '.join(focus_values)}",
                queries=queries[:self.max_queries],
                expected_results=[f"Diverse coverage for {', '.join(focus_values)}"],
            )

        return None

    def _fallback_plan(
        self, focus_values: list[str], time_window: str | None = None
    ) -> QueryPlan:
        """Deterministic fallback using FOCUS_CONCERN_KEYWORDS with balanced distribution.
        
        FIXED: Now ensures equal queries per focus area to prevent theme dominance.
        """
        global _fallback_used
        _fallback_used = True

        time_suffix = _get_time_search_suffix(time_window)

        # BALANCED QUERY GENERATION: Ensure equal distribution across focus areas
        queries_per_area = max(1, self.max_queries // len(focus_values))  # ~2 queries per area for 6 areas
        
        queries = []
        for area in focus_values:
            area_lower = area.lower()
            keywords = FOCUS_CONCERN_KEYWORDS.get(area_lower, [])

            if keywords:
                # Pick pairs of keywords for diverse coverage (up to queries_per_area)
                for i in range(0, min(len(keywords), queries_per_area * 2), 2):
                    kw1 = keywords[i]
                    kw2 = keywords[i + 1] if i + 1 < len(keywords) else ""

                    if kw2:
                        query = f'"{kw1}" OR "{kw2}"'
                    else:
                        query = f'"{kw1}"'

                    queries.append(QueryTask(
                        query=f"({query}){time_suffix}",
                        intent="targeted",
                        topic=kw1.replace("Baguio ", ""),
                        priority=len(queries) + 1,
                    ))
            else:
                queries.append(QueryTask(
                    query=f'"Baguio {area} problem" OR "Baguio {area} concern"{time_suffix}',
                    intent="broad",
                    topic=area,
                    priority=len(queries) + 1,
                ))

            if len(queries) >= self.max_queries:
                break

        # If we don't have enough queries, add more from remaining areas
        if len(queries) < self.max_queries:
            for area in focus_values:
                if len(queries) >= self.max_queries:
                    break
                area_lower = area.lower()
                keywords = FOCUS_CONCERN_KEYWORDS.get(area_lower, [])
                if keywords:
                    # Get any remaining keywords
                    for i in range(len(queries) % len(keywords), len(keywords), 2):
                        if len(queries) >= self.max_queries:
                            break
                        kw1 = keywords[i]
                        kw2 = keywords[i + 1] if i + 1 < len(keywords) else ""
                        query = f'"{kw1}" OR "{kw2}"' if kw2 else f'"{kw1}"'
                        queries.append(QueryTask(
                            query=f"({query}){time_suffix}",
                            intent="targeted",
                            topic=kw1.replace("Baguio ", ""),
                            priority=len(queries) + 1,
                        ))

        if not queries:
            query = f"Baguio City {' '.join(focus_values)} problem OR concern{time_suffix}"
            queries = [QueryTask(query=query, intent="broad", topic="general", priority=1)]

        logger.info("[query_orchestrator] Fallback: %d balanced queries from domain knowledge", len(queries))

        return QueryPlan(
            strategy=f"Balanced fallback (domain knowledge) for {', '.join(focus_values)}",
            queries=queries,
            expected_results=[f"Balanced coverage for {', '.join(focus_values)}"],
        )
