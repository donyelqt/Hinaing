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

## Latest Updates (Nov 27, 2025)
- Added per-agent latency logging across retrieval, sentiment, enrichment, and theme synthesis nodes to prove performance optimizations.
- Parallelized the credibility + theme-routing stage (`analyze_enriched`) and tightened retrieval concurrency so LangSearch and Facebook fetches run together.
- Theme agents now skip Gemini ReAct when a bucket has fewer than two documents, falling back to deterministic insight summaries to cut wasteful LLM calls.

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
