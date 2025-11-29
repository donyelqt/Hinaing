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
- LangGraph workflow now integrates dedicated Retrieval, Sentiment, Credibility, and Theme Router agents plus theme-specific Gemini mini-agents—i.e., the multi-agent stack is live in production.
- **Full Ensemble Sentiment Agent**: RoBERTa transformer + Gemini LLM analyze ALL documents with weighted voting (40%/60%) for maximum accuracy.
- Integrated LangSearch Semantic Rerank API + Facebook ingestion into the retrieval agent so snapshots already leverage real-time intelligent search across multiple platforms.
- Instrumented per-agent latency logging (retrieval, sentiment, enrichment, theme agents) and added selective Gemini skipping for low-document themes to cut wasted LLM time.
- Parallelized `analyze_enriched` (Credibility + Theme Router) via `asyncio.gather`, tightened LangSearch + Facebook concurrency inside `RetrievalAgent.run`.

### Documentation
- Created consistency docs (frontend + backend READMEs) plus this roadmap for future contributors.
- Synced `README.md`, `ROADMAP.md`, and `THESIS_FINDINGS.md` so each mirrors the live LangGraph workflow.

## 🔄 Latest Updates (Nov 29, 2025)
- **Full Ensemble Sentiment Agent**: Upgraded from hybrid (selective Gemini) to full ensemble approach:
  - RoBERTa (`twitter-roberta-base-sentiment`) analyzes ALL documents → probability distribution
  - Gemini LLM analyzes ALL documents → probability distribution
  - Weighted voting combines predictions (40% RoBERTa + 60% Gemini)
  - Rich metadata: both predictions, confidence scores, model agreement status
- Added per-agent latency logging directly in `backend/app/services/insights/graph.py` for thesis benchmarking.
- `analyze_enriched` now dispatches `CredibilityAgent` and `ThemeRouterAgent` concurrently via `asyncio.gather`.
- Retrieval concurrency tightened by awaiting LangSearch + Facebook futures together.
- LangSearch retrieval now applies rate-limit resilience with retriable 429 handling, exponential backoff.
- Theme routing uses six refined categories, increases per-theme document analysis to 25 docs.
- Low-signal theme buckets skip Gemini, falling back to deterministic summaries when cluster has <2 docs.

## 🚧 In Progress / Near-Term TODOs

1. **Sentiment Ensemble Optimization**
   - ✅ Full ensemble with RoBERTa + Gemini (completed Nov 29, 2025)
   - Tune ensemble weights based on validation set performance
   - Add confidence calibration for probability outputs

2. **Credibility Enhancement**
   - Plug fine-tuned credibility models into the agent pipeline.
   - Emit `confidence`, `model_version`, and `credibility_breakdown` directly in `/insights/snapshot`.

3. **Calibration & QA assets**
   - Assemble labeled validation sets for both sentiment and credibility.
   - Define acceptance thresholds (precision/recall, false-positive rate) and automate reporting.

4. **Observability & performance**
   - Export per-agent latency & doc-count metrics to observability stack (Prometheus/LangSmith).
   - Configure alerts for drift, low confidence, or inadequate sample coverage.

5. **Documentation expansion**
   - Create `docs/model-log.md` with model versions, dataset hashes, confusion matrices.
   - Add updated architecture diagrams showing ensemble sentiment flow.

## 🧭 Longer-Term Roadmap

1. **Multi-agent evolution (next phase)**
   - Introduce a RAG Solutions agent backed by Qdrant to recommend actions per theme.
   - Explore parallel execution, retries, and shared memory across agents.

2. **Real-time intelligent search & RAG**
   - Integrate live search connectors and retrieval-augmented generation so insights reference the freshest context automatically.

3. **Human-in-the-loop review portal**
   - Build an interface for analysts to approve/override classifier outputs, closing the loop for continuous improvement.

Keeping this list up to date ensures everyone knows the current status and the next steps required to deliver a defensible, multi-agent, real-time public opinion analysis platform.
