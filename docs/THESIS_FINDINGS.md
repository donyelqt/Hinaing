# Thesis Findings

## Overview
The prototype now delivers a multi-agent, real-time intelligent search stack for context-aware public opinion analysis in Baguio City. A LangGraph workflow orchestrates specialized agents (retrieval, sentiment, credibility, theme routing) and invokes Gemini ReAct micro-agents per theme to ground insights in the latest civic chatter. This document captures the current evidence, what works well, and the remaining gaps toward a thesis-ready system.

## Current Capabilities

| Capability | Evidence | Notes |
| --- | --- | --- |
| Multi-agent architecture | `backend/app/services/insights/agents.py`, LangGraph workflow in `backend/app/services/insights/graph.py` | Retrieval/Sentiment/Credibility/Theme Router agents cooperate via shared `SnapshotState`. |
| Theme-specific LLM reasoning | `_synthesize_theme_insight` in `graph.py` | Gemini ReAct agent produces JSON insights for Health/Safety, Infra/Env, Tourism/Economy buckets. |
| Real-time intelligent search | `agent_tools.search_web_documents` + `fetch_facebook_documents` | Combines LangSearch semantic rerank + Facebook ingestion under the Retrieval Agent. |
| Sentiment & credibility tagging | `SentimentAgent.run`, `CredibilityAgent.run` | Deterministic scoring ensures every document has sentiment + domain credibility metadata. |
| Snapshot coordination | `build_snapshot` | Integrates agent outputs, Gemini narrative, alerts, and traceable evidence links for the UI. |
| Per-agent telemetry instrumentation | `backend/app/services/insights/graph.py` (`fetch_documents`, `label_sentiment`, `analyze_enriched`, `theme_agents`) | Stage-level duration + document counts logged for benchmarking and observability rollouts. |

## Key Findings
1. **Agent modularity speeds iteration** – New logic (e.g., classifiers, RAG solutions agent) can be introduced by swapping an agent node without rewriting the entire pipeline.
2. **LLM micro-agents add nuance but cost latency** – Theme-specific Gemini calls provide richer insights; caching or selective invocation will be needed for production SLAs.
3. **Real-time coverage hinges on LangSearch + Apify** – The Retrieval Agent already fans out to both; adding more connectors (e.g., Reddit, X) requires only new tool wrappers.
4. **Observability is the next blocker** – With multiple agents, we need per-agent metrics (latency, doc counts, confidence) and drift alerts to keep the system defensible.

## Latest Evidence (Nov 27, 2025)
- Added per-agent latency logging directly in `backend/app/services/insights/graph.py` (`fetch_documents`, `label_sentiment`, `analyze_enriched`, `theme_agents`) so every node reports runtime + document counts for thesis benchmarking.
- `analyze_enriched` now dispatches `CredibilityAgent` and `ThemeRouterAgent` concurrently via `asyncio.gather`, tightening latency before the Gemini stages.
- Retrieval concurrency tightened by awaiting LangSearch + Facebook futures together in `backend/app/services/insights/agents.py:RetrievalAgent.run`, then conditionally reranking via `LangSearchClient` when both sources return context.
- Low-signal theme buckets skip Gemini ReAct inside `theme_agents`/`_synthesize_theme_insight`, falling back to deterministic summaries when a cluster has <2 docs.
- `docs/README.md` and `ROADMAP.md` now mirror the live multi-agent flow and call out the planned Qdrant-backed RAG Solutions agent.

## Gaps & Next Steps
- Integrate fine-tuned sentiment/credibility models to replace heuristic scoring.
- Add the planned RAG Solutions agent backed by Qdrant for recommendation grounding.
- Export the new per-agent telemetry (latency, doc counts, confidence) to dashboards + tracing for thesis evaluation.
- Document the end-to-end agent flow in an architecture diagram for the dissertation.

Keeping this doc updated will make it easier to demonstrate thesis impact during defenses and publications.
