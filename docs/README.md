# Hinaing Docs

This directory houses the thesis documentation for **Hinaing**, a multi-agent, real-time intelligent search platform for context-aware public opinion analysis in Baguio City.

## Contents
- `ROADMAP.md` – high-level milestones, completed work, and next steps.
- `THESIS_FINDINGS.md` – current thesis findings, capabilities, and remaining gaps.
- `README.md` (this file) – quick overview plus links to app resources.

## Application Overview
- **Frontend**: React/TypeScript Sentiment Generator that visualizes snapshots, credibility tags, and alerts.
- **Backend**: FastAPI service running a LangGraph workflow with Query Orchestrator, Retrieval, Sentiment, Credibility, Theme Router, Context Augmentation agents, plus per-theme Gemini mini-agents.
- **Shared goals**: Provide civic leaders with near real-time sentiment summaries grounded in the latest news, social, and forum discussions.

## Architecture Highlights
1. **Query Orchestrator Agent (ReAct)** uses LLM-powered reasoning loop (Thought → Action → Observation) with 3 custom tools to generate adaptive query plans. Located in `backend/app/services/agents/query_orchestrator.py`.
   - `analyze_focus_areas` - Determines search strategy per focus area (urgent/trend/broad)
   - `generate_query` - Creates optimized search queries with location + temporal context
   - `evaluate_query` - Scores query quality (0-1) before execution
   - Uses Gemini 2.0 Flash for reasoning, typically 3-4 iterations per plan
   - Fallback plan generation when ReAct fails
2. **Retrieval Agent** combines LangSearch semantic rerank + Facebook ingestion to gather documents per request, using orchestrated query plans.
3. **Ensemble Sentiment Agent** uses weighted voting of RoBERTa transformer (40%) + Gemini LLM (60%) for maximum accuracy sentiment classification.
4. **Credibility Agent** scores domain trustworthiness based on source type (.gov.ph, .org) and recency.
5. **Theme Router Agent** clusters documents into six focused categories via `agent_tools.THEME_GROUPS`, logging routing/insight stats.
6. **Context Augmentation Agent** enriches each theme's state with RAG pipeline:
   - `SemanticChunker` - Sentence-based chunking with overlap (400 chars, 100 overlap)
   - `EmbeddingService` - MiniLM-L6-v2 embeddings (384 dimensions, CPU-optimized)
   - `VectorStore` - Qdrant in-memory vector search with cosine similarity
7. **Gemini Theme Agents** synthesize insights with traceable evidence for each bucket using direct Gemini calls with theme-specific prompts. Runs in parallel (6 threads via ThreadPoolExecutor). Respects focus area filtering.
8. **Coordinator Agents** merge theme insights, Gemini narrative, and alerting logic into the final snapshot consumed by the frontend.
9. **RAG Solutions Agent** *(planned)* will pull guidance from a Qdrant-backed knowledge base to suggest follow-up actions per theme.
10. **Per-agent telemetry** logs runtime + doc counts inside `backend/app/services/insights/graph.py` for observability.

## Latest Updates (Dec 4, 2025)
- **Narrative Generation Optimization**: Switched from `gemini-2.5-pro` to `gemini-2.0-flash-exp` for narrative generation (~5x faster response times while maintaining quality).
- **Agent Tools Consolidation**: Migrated tool definitions to centralized `agent_tools.py`, removed redundant `tools.py`.
- **Baguio-Specific Search Enhancement**: Added local keywords (BGH, Kennon Road, Session Road, etc.) to `context_agent.py` for improved local search relevance.
- **Robust Query Parsing**: `query_orchestrator.py` now handles flexible LLM output formats (string/object queries, fallback field names).

## Previous Updates (Dec 3, 2025)
- **Phase 2 Complete: Query Orchestrator Agent (ReAct)** - Implemented LLM-powered reasoning loop (Thought → Action → Observation) with 3 custom tools for adaptive query planning. Uses Gemini 2.0 Flash, typically 3-4 iterations per plan with fallback generation when ReAct fails.
- **Phase 1 Complete: RAG Pipeline** - Full context augmentation system with SemanticChunker (sentence-based, 400 chars, 100 overlap), EmbeddingService (MiniLM-L6-v2, 384 dims), and Qdrant VectorStore (in-memory, cosine similarity). Integrated into workflow between theme routing and theme agents.
- **Full Ensemble Sentiment Agent**: Both RoBERTa (transformer) and Gemini (LLM) analyze ALL documents, with weighted voting (40% RoBERTa, 60% Gemini) for maximum accuracy. Provides rich metadata including both model predictions, confidence scores, and agreement metrics.
- **Parallel Theme Agent Execution**: Theme agents now run in parallel using ThreadPoolExecutor (6 workers) for faster insight generation.
- Per-agent latency logging in `graph.py` (`orchestrate_queries`, `fetch_documents`, `label_sentiment`, `analyze_enriched`, `augment_context`, `theme_agents`) for thesis benchmarking.
- `analyze_enriched` dispatches `CredibilityAgent` and `ThemeRouterAgent` concurrently via `asyncio.gather`.
- Retrieval uses orchestrated query plans from ReAct agent, with LangSearch + Facebook futures together and conditional semantic reranking.
- Theme agents receive RAG-augmented context (top 10 chunks per theme) for higher quality insights.
- **Focus Area Filtering**: Theme agents now respect user-specified focus areas, only generating insights for relevant themes.

## Tech Stack

### Backend
- **Python 3.11+** with **Poetry** for dependency management
- **FastAPI** – high-performance async web framework
- **LangChain / LangGraph** – multi-agent orchestration and workflow
- **LangSmith** – observability and tracing
- **LangSearch** – semantic web search and reranking API for document retrieval (Intelligent Search)
- **Google Gemini** (`google-generativeai`) – LLM for sentiment ensemble and theme agents (Gemini 2.5 Pro with 3000 max tokens, batch_size=12 for sentiment)
- **HuggingFace Transformers** – RoBERTa sentiment model (`twitter-roberta-base-sentiment`)
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
- Sentiment ensemble: `backend/app/services/agents/sentiment_agent.py`.
- Frontend usage guide: `frontend/README.md`.
- Roadmap and thesis findings (this docs folder).

Keep this README updated as the thesis evolves.
