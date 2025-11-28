# Hinaing Docs

This directory houses the thesis documentation for **Hinaing**, a multi-agent, real-time intelligent search platform for context-aware public opinion analysis in Baguio City.

## Contents
- `ROADMAP.md` – high-level milestones, completed work, and next steps.
- `THESIS_FINDINGS.md` – current thesis findings, capabilities, and remaining gaps.
- `README.md` (this file) – quick overview plus links to app resources.

## Application Overview
- **Frontend**: React/TypeScript Sentiment Generator that visualizes snapshots, credibility tags, and alerts.
- **Backend**: FastAPI service running a LangGraph workflow with Retrieval, Sentiment, Credibility, Theme Router agents, plus per-theme Gemini mini-agents.
- **Shared goals**: Provide civic leaders with near real-time sentiment summaries grounded in the latest news, social, and forum discussions.

## Architecture Highlights
1. **Query Orchestrator Agent** generates adaptive query plans (broad + targeted + risk queries) for downstream retrieval.
2. **Retrieval Agent** combines LangSearch semantic rerank + Facebook ingestion to gather documents per request.
3. **Sentiment Agent** (AI-powered) uses Gemini to classify public sentiment as positive/negative/neutral with batch processing and graceful fallback to rule-based scoring.
4. **Credibility Agent** scores domain trustworthiness based on source type (.gov.ph, .org) and recency.
5. **Theme Router Agent** clusters documents into six focused categories via `agent_tools.THEME_GROUPS`, logging routing/insight stats.
6. **Context Augmentation Agent** enriches each theme's state with RAG pipeline (chunking → embeddings → Qdrant vector search).
7. **Gemini Theme Agents** synthesize insights with traceable evidence for each bucket using direct Gemini calls with theme-specific prompts.
8. **Coordinator Agents** merge theme insights, Gemini narrative, and alerting logic into the final snapshot consumed by the frontend.
9. **RAG Solutions Agent** *(planned)* will pull guidance from a Qdrant-backed knowledge base to suggest follow-up actions per theme.
10. **Per-agent telemetry** logs runtime + doc counts inside `backend/app/services/insights/graph.py` for observability.

## Latest Updates (Nov 29, 2025)
- **AI-Powered Sentiment Agent**: Replaced rule-based keyword matching with Gemini-based sentiment classification (`GeminiSentimentAgent`). Processes documents in batches of 5 for efficiency, with safety filters disabled for legitimate civic news analysis. Falls back to enhanced rule-based scoring if Gemini fails.
- Added per-agent latency logging directly in `backend/app/services/insights/graph.py` (`fetch_documents`, `label_sentiment`, `analyze_enriched`, `theme_agents`) so every node reports runtime + document counts for thesis benchmarking.
- `analyze_enriched` now dispatches `CredibilityAgent` and `ThemeRouterAgent` concurrently via `asyncio.gather`, tightening latency before the Gemini stages.
- Retrieval concurrency tightened by awaiting LangSearch + Facebook futures together in `backend/app/services/insights/agents.py:RetrievalAgent.run`, then conditionally reranking via `LangSearchClient` when both sources return context.
- LangSearch retrieval now includes retryable rate-limit handling plus exponential backoff, ensuring 429 responses are throttled with jittered concurrency limits before falling back to graceful degradation.
- Theme routing now relies on six refined categories defined inside `agent_tools.THEME_GROUPS`, logging routing/insight selection stats, raising per-theme analysis to 25 docs.
- Low-signal theme buckets skip Gemini inside `theme_agents`/`_synthesize_theme_insight`, falling back to deterministic summaries when a cluster has <2 docs.

## Tech Stack

### Backend
- **Python 3.11+** with **Poetry** for dependency management
- **FastAPI** – high-performance async web framework
- **LangChain / LangGraph** – multi-agent orchestration and workflow
- **LangSmith** – observability and tracing
- **LangSearch** – semantic web search and reranking API for document retrieval (Intelligent Search)
- **Google Gemini** (`google-generativeai`) – LLM for sentiment analysis and theme agents
- **Qdrant** – vector database for RAG embeddings
- **Sentence Transformers** – local embedding generation (MiniLM-L6-v2)
- **Supabase** – database and auth
- **APScheduler** – background job scheduling
- **Pydantic** – data validation and settings
- **HTTPX** – async HTTP client for external API calls

### Frontend
- **Next.js 15** with **React 19** and **TypeScript**
- **Tailwind CSS** – utility-first styling
- **SWR** – data fetching and caching
- **Supabase JS** – client-side database access
- **Lucide React** – icon library

### DevOps & Tooling
- **Docker** – containerization
- **Ruff** – Python linting
- **ESLint** – TypeScript/JS linting
- **Pytest** – backend testing

### Deployment
- **Railway** – backend hosting and deployment
- **Vercel** – frontend hosting and deployment

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
