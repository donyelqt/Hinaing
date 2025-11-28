# Thesis Findings

## Overview
The prototype now delivers a multi-agent, real-time intelligent search stack for context-aware public opinion analysis in Baguio City. A LangGraph workflow orchestrates specialized agents (query orchestrator, retrieval, sentiment, credibility, theme routing, context augmentation) and invokes Gemini micro-agents per theme to ground insights in the latest civic chatter. This document captures the current evidence, what works well, and the remaining gaps toward a thesis-ready system.

## Current Capabilities

| Capability | Evidence | Notes |
| --- | --- | --- |
| Multi-agent architecture | `backend/app/services/insights/agents.py`, LangGraph workflow in `backend/app/services/insights/graph.py` | Query Orchestrator/Retrieval/Sentiment/Credibility/Theme Router/Context Augmentation agents cooperate via shared `SnapshotState`. |
| AI-powered sentiment analysis | `backend/app/services/agents/sentiment_agent.py` | Gemini-based classification with batch processing, safety filters disabled for civic news, and rule-based fallback. |
| Theme-specific LLM reasoning | `backend/app/services/agents/theme_agent.py` | Direct Gemini calls with theme-specific prompts produce JSON insights for each category. |
| Real-time intelligent search | `agent_tools.search_web_documents` + `fetch_facebook_documents` | Combines LangSearch semantic rerank + Facebook ingestion under the Retrieval Agent. |
| RAG pipeline | `backend/app/services/rag/` | SemanticChunker → EmbeddingService (MiniLM-L6-v2) → Qdrant VectorStore for context augmentation. |
| Credibility tagging | `CredibilityAgent.run` | Domain-based scoring (.gov.ph, .org boost) + recency factors. |
| Snapshot coordination | `build_snapshot` | Integrates agent outputs, Gemini narrative, alerts, and traceable evidence links for the UI. |
| Per-agent telemetry | `backend/app/services/insights/graph.py` | Stage-level duration + document counts logged for benchmarking and observability. |

## Key Findings

### 1. AI-Powered Sentiment Analysis (Nov 29, 2025)
**Problem**: Rule-based keyword matching was inaccurate for nuanced civic discourse (sarcasm, context-dependent sentiment, mixed opinions).

**Solution**: Implemented `GeminiSentimentAgent` with:
- Batch processing (5 documents per API call) for efficiency
- Disabled Gemini safety filters (`BLOCK_NONE`) for legitimate civic news analysis
- Graceful fallback to enhanced rule-based scoring when Gemini fails

**Technical Implementation**:
```python
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}
```

**Rationale**: Civic news often contains reports about crimes, accidents, protests, and public complaints. Gemini's default safety filters incorrectly blocked this legitimate content. Disabling filters is appropriate because:
- Content is factual news reporting, not harmful user-generated content
- The system analyzes public sentiment, not generates harmful content
- Fallback mechanisms ensure reliability when API issues occur

### 2. Agent Modularity Speeds Iteration
New logic (e.g., classifiers, RAG solutions agent) can be introduced by swapping an agent node without rewriting the entire pipeline.

### 3. LLM Micro-Agents Add Nuance but Cost Latency
Theme-specific Gemini calls provide richer insights; selective invocation (skip for <2 docs) reduces wasted LLM time.

### 4. Real-Time Coverage Hinges on LangSearch + Apify
The Retrieval Agent fans out to both; adding more connectors (e.g., Reddit, X) requires only new tool wrappers.

### 5. RAG Pipeline Enhances Context
Context Augmentation Agent uses semantic chunking + vector search to provide relevant context to theme agents.

## Latest Evidence (Nov 29, 2025)
- **AI-Powered Sentiment Agent**: Replaced rule-based keyword matching with `GeminiSentimentAgent`. Processes documents in batches of 5, uses disabled safety filters for civic news, falls back to enhanced rule-based scoring.
- Added per-agent latency logging directly in `backend/app/services/insights/graph.py` (`fetch_documents`, `label_sentiment`, `analyze_enriched`, `theme_agents`) so every node reports runtime + document counts for thesis benchmarking.
- `analyze_enriched` now dispatches `CredibilityAgent` and `ThemeRouterAgent` concurrently via `asyncio.gather`, tightening latency before the Gemini stages.
- Retrieval concurrency tightened by awaiting LangSearch + Facebook futures together in `backend/app/services/insights/agents.py:RetrievalAgent.run`, then conditionally reranking via `LangSearchClient` when both sources return context.
- LangSearch usage now includes rate-limit resilience with retries, exponential backoff, and constrained concurrency.
- Theme routing now relies on six refined categories (from `agent_tools.THEME_GROUPS`), raises per-theme document analysis to 25, logs routing/insight stats.
- Low-signal theme buckets skip Gemini inside `theme_agents`/`_synthesize_theme_insight`, falling back to deterministic summaries when a cluster has <2 docs.

## Gaps & Next Steps
- ✅ ~~Integrate AI-based sentiment model~~ (Completed: GeminiSentimentAgent)
- Integrate fine-tuned credibility models to replace heuristic scoring.
- Add the planned RAG Solutions agent backed by Qdrant for recommendation grounding.
- Switch Qdrant from in-memory to persistent storage for production.
- Export the new per-agent telemetry (latency, doc counts, confidence) to dashboards + tracing for thesis evaluation.
- Document the end-to-end agent flow in an architecture diagram for the dissertation.
- Add Reddit integration (code exists in `backend/app/services/ingestion/reddit.py` but not wired).

## Architecture Flow
```
SnapshotRequest
       ↓
orchestrate_queries (QueryOrchestratorAgent)
       ↓
fetch_documents (RetrievalAgent → LangSearch + Facebook → Rerank)
       ↓
label_sentiment (SentimentAgent - Gemini AI)
       ↓
analyze_enriched (CredibilityAgent ∥ ThemeRouterAgent) ← parallel
       ↓
augment_context (ContextAugmentationAgent → Chunker → Embed → Qdrant)
       ↓
theme_agents (6x Gemini calls in parallel)
       ↓
build_snapshot (GeminiClient narrative + assembly)
       ↓
SnapshotResponse
```

Keeping this doc updated will make it easier to demonstrate thesis impact during defenses and publications.
