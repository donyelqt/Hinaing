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

## Key Findings
1. **Agent modularity speeds iteration** – New logic (e.g., classifiers, RAG solutions agent) can be introduced by swapping an agent node without rewriting the entire pipeline.
2. **LLM micro-agents add nuance but cost latency** – Theme-specific Gemini calls provide richer insights; caching or selective invocation will be needed for production SLAs.
3. **Real-time coverage hinges on LangSearch + Apify** – The Retrieval Agent already fans out to both; adding more connectors (e.g., Reddit, X) requires only new tool wrappers.
4. **Observability is the next blocker** – With multiple agents, we need per-agent metrics (latency, doc counts, confidence) and drift alerts to keep the system defensible.

## Gaps & Next Steps
- Integrate fine-tuned sentiment/credibility models to replace heuristic scoring.
- Add the planned RAG Solutions agent backed by Qdrant for recommendation grounding.
- Instrument per-agent telemetry + tracing for thesis evaluation.
- Document the end-to-end agent flow in an architecture diagram for the dissertation.

Keeping this doc updated will make it easier to demonstrate thesis impact during defenses and publications.
