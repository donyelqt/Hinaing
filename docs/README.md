# Hinaing Docs

This directory houses the thesis documentation for **Hinaing**, a multi-agent, real-time intelligent search platform for context-aware public opinion analysis in Baguio City.

## Contents
- `ROADMAP.md` – high-level milestones, completed work, and next steps.
- `THESIS_FINDINGS.md` – current thesis findings, capabilities, and remaining gaps.
- `README.md` (this file) – quick overview plus links to app resources.

## Application Overview
- **Frontend**: React/TypeScript Sentiment Generator that visualizes snapshots, credibility tags, and alerts.
- **Backend**: FastAPI service running a LangGraph workflow with Retrieval, Sentiment, Credibility, Theme Router agents, plus per-theme Gemini ReAct mini-agents.
- **Shared goals**: Provide civic leaders with near real-time sentiment summaries grounded in the latest news, social, and forum discussions.

## Architecture Highlights
1. **Retrieval Agent** combines LangSearch semantic rerank + Facebook ingestion to gather documents per request.
2. **Sentiment & Credibility Agents** enrich every document with sentiment scores and domain credibility notes.
3. **Theme Router Agent** clusters documents into Health/Safety, Infra/Env, and Tourism/Economy buckets.
4. **Gemini Theme Agents** (ReAct) synthesize insights with traceable evidence for each bucket.
5. **RAG Solutions Agent** *(planned)* will pull guidance from a Qdrant-backed knowledge base to suggest follow-up actions per theme.
6. **Coordinator Agents** merge theme insights, Gemini narrative, and alerting logic into the final snapshot consumed by the frontend.
7. **Per-agent telemetry instrumentation** logs runtime + doc counts inside `backend/app/services/insights/graph.py` stages for observability rollouts.

## Latest Updates (Nov 27, 2025)
- Added per-agent latency logging directly in `backend/app/services/insights/graph.py` (`fetch_documents`, `label_sentiment`, `analyze_enriched`, `theme_agents`) so every node reports runtime + document counts for thesis benchmarking.
- `analyze_enriched` now dispatches `CredibilityAgent` and `ThemeRouterAgent` concurrently via `asyncio.gather`, tightening latency before the Gemini stages.
- Retrieval concurrency tightened by awaiting LangSearch + Facebook futures together in `backend/app/services/insights/agents.py:RetrievalAgent.run`, then conditionally reranking via `LangSearchClient` when both sources return context.
- Low-signal theme buckets skip Gemini ReAct inside `theme_agents`/`_synthesize_theme_insight`, falling back to deterministic summaries when a cluster has <2 docs.
- This docs folder (`README.md`, `ROADMAP.md`, `THESIS_FINDINGS.md`) now mirrors the live multi-agent flow and flags the upcoming Qdrant-backed RAG Solutions agent.

## Getting Started
1. Install dependencies via Poetry (backend) and npm (frontend).
2. Set environment variables for LangSearch + Google Gemini.
3. Run `poetry run uvicorn app.main:create_app --factory --reload` for the backend.
4. In `frontend/`, run `npm install` then `npm run dev` and open the Sentiment Generator UI.

## Key Docs & References
- Backend architecture and agents: `backend/app/services/insights/graph.py`, `backend/app/services/insights/agents.py`.
- Frontend usage guide: `frontend/README.md`.
- Roadmap and thesis findings (this docs folder).

Keep this README updated as the thesis evolves (e.g., when the RAG Solutions agent or Qdrant vector store is added).
