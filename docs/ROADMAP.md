# Project Roadmap

**Thesis Title:** _Multi-agent agentic AI with real-time intelligent search and RAG for context-aware public opinion analysis_

This document tracks what has been delivered so far and the remaining work needed to reach the "thesis-grade" target.

## ✅ Completed Work

### Frontend (Sentiment Generator UI)
- Parsed JSON summaries into human-readable narratives and evidence cards.
- Added legitimacy vs potential fake-news indicators beside sentiment scores.
- Introduced inline loading animations (overall sentiment card, actionable insights placeholder).
- Documented sentiment/credibility computations and long-term accuracy roadmap in `frontend/README.md`.

### Backend
- LangGraph workflow now integrates dedicated Retrieval, Sentiment, Credibility, and Theme Router agents plus theme-specific Gemini ReAct mini-agents—i.e., the multi-agent stack is live in production.
- Authored `backend/README.md` with detailed plans for sentiment/credibility classifier upgrades, observability, and governance.
- Integrated LangSearch Semantic Rerank API + Facebook ingestion into the retrieval agent so snapshots already leverage real-time intelligent search across multiple platforms.
- Instrumented per-agent latency logging (retrieval, sentiment, enrichment, theme agents) and added selective Gemini skipping for low-document themes to cut wasted LLM time.
- Parallelized `analyze_enriched` (Credibility + Theme Router) via `asyncio.gather`, tightened LangSearch + Facebook concurrency inside `RetrievalAgent.run`, and kept deterministic fallbacks for low-signal themes when Gemini ReAct is skipped.

### Documentation
- Created consistency docs (frontend + backend READMEs) plus this roadmap for future contributors.
- Synced `README.md`, `ROADMAP.md`, and `THESIS_FINDINGS.md` so each mirrors the live LangGraph workflow and upcoming Qdrant-backed RAG Solutions agent.

## 🔄 Latest Updates (Nov 29, 2025)
- **AI-Powered Sentiment Agent**: Replaced rule-based keyword matching with `GeminiSentimentAgent` for accurate sentiment classification. Uses batch processing (5 docs per API call), disabled safety filters for civic news, and graceful fallback to enhanced rule-based scoring.
- Added per-agent latency logging directly in `backend/app/services/insights/graph.py` (`fetch_documents`, `label_sentiment`, `analyze_enriched`, `theme_agents`) so every node reports runtime + document counts for thesis benchmarking.
- `analyze_enriched` now dispatches `CredibilityAgent` and `ThemeRouterAgent` concurrently via `asyncio.gather`, tightening latency before the Gemini stages.
- Retrieval concurrency tightened by awaiting LangSearch + Facebook futures together in `backend/app/services/insights/agents.py:RetrievalAgent.run`, then conditionally reranking via `LangSearchClient` when both sources return context.
- LangSearch retrieval now applies rate-limit resilience with retriable 429 handling, exponential backoff, and constrained concurrency.
- Theme routing now uses six closer-aligned sub-themes defined in `agent_tools.THEME_GROUPS`, increases per-theme document analysis from 5 to 25, logs routing/insight stats.
- Low-signal theme buckets skip Gemini inside `theme_agents`/`_synthesize_theme_insight`, falling back to deterministic summaries when a cluster has <2 docs.
- Documentation (`README.md`, `ROADMAP.md`, `THESIS_FINDINGS.md`) now explicitly mirrors the live multi-agent flow.

## 🚧 In Progress / Near-Term TODOs

1. **LLM/classifier alignment**
   - ✅ Sentiment Agent now uses Gemini for AI-powered classification (completed Nov 29, 2025).
   - Plug fine-tuned credibility models into the agent pipeline.
   - Emit `confidence`, `model_version`, and `credibility_breakdown` directly in `/insights/snapshot`.

2. **Calibration & QA assets**
   - Assemble labeled validation sets for both sentiment and credibility.
   - Define acceptance thresholds (precision/recall, false-positive rate) and automate reporting after each retrain.

3. **Observability & performance**
   - Export the new per-agent latency & doc-count metrics to the observability stack (Prometheus/LangSmith) with dashboards.
   - Configure alerts for drift, low confidence, or inadequate sample coverage; profile agent latency and consider lightweight Gemini caching for hotspots.

4. **Documentation expansion**
   - Create `docs/model-log.md` with model versions, dataset hashes, confusion matrices.
   - Add updated architecture diagrams showing the current multi-agent workflow and planned RAG additions.

## 🧭 Longer-Term Roadmap

1. **Multi-agent evolution (next phase)**
   - Introduce a RAG Solutions agent backed by Qdrant to recommend actions per theme.
   - Explore parallel execution, retries, and shared memory across agents.

2. **Real-time intelligent search & RAG**
   - Integrate live search connectors and retrieval-augmented generation so insights reference the freshest context automatically.

3. **Human-in-the-loop review portal**
   - Build an interface for analysts to approve/override classifier outputs, closing the loop for continuous improvement.

Keeping this list up to date ensures everyone knows the current status and the next steps required to deliver a defensible, multi-agent, real-time public opinion analysis platform.
