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
- LangGraph-based agentic workflow already generates snapshots consumed by the UI.
- Authored `backend/README.md` with detailed plans for sentiment/credibility classifier upgrades, observability, and governance.
 - Integrated LangSearch Semantic Rerank API into the web search pipeline so snapshot generation uses semantically reranked web documents by default.

### Documentation
- Created consistency docs (frontend + backend READMEs) plus this roadmap for future contributors.

## 🚧 In Progress / Near-Term TODOs

1. **Backend classifier integration**
   - Plug fine-tuned sentiment and credibility models into `app/services/insights/graph.py`.
   - Emit `confidence`, `model_version`, and `credibility_breakdown` directly in `/insights/snapshot`.

2. **Calibration & QA assets**
   - Assemble labeled validation sets for both sentiment and credibility.
   - Define acceptance thresholds (precision/recall, false-positive rate) and automate reporting after each retrain.

3. **Monitoring & alerts**
   - Publish metrics (`sentiment.*`, `credibility.*`, sample sizes, average confidence) to the observability stack.
   - Configure alerts for drift, low confidence, or inadequate sample coverage.

4. **Documentation expansion**
   - Create `docs/model-log.md` with model versions, dataset hashes, confusion matrices.
   - Add architecture diagrams showing how LangGraph orchestrates the workflow (and how it may evolve into multi-agent form).

## 🧭 Longer-Term Roadmap

1. **Multi-agent evolution**
   - Split the single agent into specialized sub-agents (ingestion, sentiment, credibility, narrative) coordinated by a supervisor.
   - Evaluate parallel execution and retry strategies for each agent.

2. **Real-time intelligent search & RAG**
   - Integrate live search connectors and retrieval-augmented generation so insights reference the freshest context automatically.

3. **Human-in-the-loop review portal**
   - Build an interface for analysts to approve/override classifier outputs, closing the loop for continuous improvement.

Keeping this list up to date ensures everyone knows the current status and the next steps required to deliver a defensible, multi-agent, real-time public opinion analysis platform.
