# Models Setup: 7-Node Agent Harness (Stress Test Configuration)

**Date:** April 16, 2026
**Scope:** Model wiring behind the 7-Node AgenticHinaing pipeline as evaluated by the IBM senior-engineer stress test (`rpj-score/dqt-validation`)
**Source of truth:** `github.com/donyelqt/Hinaing` (committed `main` branch)

---

## Summary

The harness uses **4 distinct inference backends** across its 7 nodes:

| Backend | Role | Models |
|---|---|---|
| **Google Gemini** | 1 node (Node 1) | `gemini-2.5-flash-lite` |
| **Groq** | 4 nodes (4A, 4B, 6, 7) + claim extraction | `llama-3.3-70b-versatile`, `llama-4-scout-17b-16e-instruct`, `llama-3.1-8b-instant` |
| **Local transformers** | 2 components | `cardiffnlp/twitter-roberta-base-sentiment-latest`, `MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33` |
| **Embedding service** | 3 nodes (3, 4C, 5) | `BAAI/bge-large-en-v1.5`, `BAAI/bge-small-en-v1.5` |

**5 of 7 nodes run an LLM.** Nodes 2, 3, and 5 are non-LLM (pure API / vector-DB).

---

## Per-Node Model Wiring

### Node 1 — Query Orchestration
- **Model:** `gemini-2.5-flash-lite` (Google Gemini)
- **Class:** `ChatGoogleGenerativeAI` (langchain-google-genai)
- **File:** `backend/app/services/agents/query_orchestrator.py:372`
- **Temperature:** 0.4
- **Purpose:** ReAct-style agentic query synthesis with tool calls
- **Note:** Hardcoded directly — does **not** go through `get_node_llm()`. The `llm_provider_query_orchestrator = "groq"` config key is dead for this node.

### Node 2 — External Retrieval
- **No LLM.** Pure API calls: LangSearch (web), Facebook (Apify), Reddit (PRAW).

### Node 3 — Internal Memory Recall
- **No LLM.** Qdrant vector search with `BAAI/bge-large-en-v1.5` embeddings.

### Node 4A — Sentiment Analysis (Ensemble)
- **LLM:** `llama-3.3-70b-versatile` (Groq)
  - File: `backend/app/services/agents/sentiment_agent.py:155`
  - `get_groq_provider("llama-3.3-70b-versatile")`
  - Weight: **60%** of ensemble
- **Local:** `cardiffnlp/twitter-roberta-base-sentiment-latest` (RoBERTa, HuggingFace)
  - Weight: **40%** of ensemble
- **Combined:** weighted average → final label + confidence

### Node 4B — Credibility (5-Signal Ensemble)
- **LLM signal (20% of score):** `meta-llama/llama-4-scout-17b-16e-instruct` (Groq)
  - File: `backend/app/services/agents/credibility_agent.py:356`
  - Class: `LLMCredibilityAnalyzer`
- **Other 4 signals (no LLM):**
  - Domain Trust (25%) — heuristic domain table
  - Cross-Reference (20%) — BGE-small cosine similarity
  - Fact Check (15%) — Google Fact Check API
  - Tavily (20%) — Tavily web verification API

### Node 4C — Theme Routing
- **No LLM.** `BAAI/bge-large-en-v1.5` embeddings + cosine similarity (threshold 0.35) + keyword fallback.

### Node 5 — Memory Consolidation
- **No LLM.** Qdrant ingestion with `BAAI/bge-large-en-v1.5` embeddings.

### Node 6 — Theme Agents (×6)
- **Model:** `meta-llama/llama-4-scout-17b-16e-instruct` (Groq)
- **File:** `backend/app/services/agents/theme_agent.py:223`
- **6 sub-agents:** Infrastructure, Health, Safety, Tourism, Economy, Environment
- **Purpose:** Generate 3 actionable recommendations each with evidence URLs

### Node 7 — Coordinator / Narrative Synthesis
- **Model:** `meta-llama/llama-4-scout-17b-16e-instruct` (Groq)
- **File:** `backend/app/services/nlp/gemini.py:45` — `LLMNarrativeClient(model_name="meta-llama/llama-4-scout-17b-16e-instruct")`
- **Wrapper:** `backend/app/services/agents/coordinator_agent.py`
- **Purpose:** Final narrative summary + insight assembly

### Post-Generation Verification (not a graph node)
- **Claim extraction:** `meta-llama/llama-4-scout-17b-16e-instruct` (Groq) — `claim_extractor.py:21`
- **NLI entailment:** `MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33` (local) — `entailment_checker.py:28`

---

## Provider Selection Wiring

`backend/app/core/config.py` (ground truth):

```python
llm_provider_query_orchestrator: str = "groq"   # dead — Node 1 hardcodes Gemini
llm_provider_sentiment: str = "groq"
llm_provider_credibility: str = "groq"
llm_provider_theme_agents: str = "groq"
llm_provider_coordinator: str = "groq"
groq_default_model: str = "llama-3.3-70b-versatile"
```

`backend/app/services/llm/factory.py:get_node_llm()` maps each node name to its config key, defaulting to `"groq"`, with a silent Gemini fallback only on exception.

`get_llm_provider()` defaults:
- Groq → `llama-3.1-8b-instant`
- Gemini → `gemini-2.5-flash-lite`
- OpenRouter → `deepseek/deepseek-chat`

---

## Discrepancy with `docs/MODEL_USAGE_BY_NODE.md`

The existing `MODEL_USAGE_BY_NODE.md` claims a **unified Gemini 2.5 Flash Lite architecture** — "ALL LLM nodes (5 nodes)", "No Groq dependencies: Simplified architecture, single provider."

**This is incorrect.** The committed code defaults 4 of 5 LLM nodes to Groq. Only Node 1 uses Gemini. The doc describes a migration that never landed in `config.py`.

**Recommendation:** Either (a) update `MODEL_USAGE_BY_NODE.md` to match the code, or (b) complete the migration by setting all 5 config keys to `"gemini"`. Option (a) is lower-risk and more truthful; the actual architecture is a **multi-provider, hybrid neuro-symbolic** system, which fits the thesis framing better than a single-provider story.

---

## Why This Does Not Affect the IBM Stress-Test Score

The `dqt-validation` framework scores **agent trajectory and route**, not underlying providers. Its `reference_trajectory` field for every scenario is:

```
["query_orchestrator", "retrieval", "recall", "analyze", "memory", "themes", "snapshot"]
```

The framework observes the node *sequence* via Hinaing's `progress_callback` hook, not which model sits behind each node. The Trajectory section scored **18.00/18 (perfect)** and Efficiency **8.00/8** regardless of provider. The model choice is a documentation-accuracy matter, not an evaluation-integrity one.

---

## Environment Variables Consumed

| Variable | Used by |
|---|---|
| `GROQ_API_KEY` | Nodes 4A, 4B, 6, 7 + claim extraction |
| `GEMINI_API_KEY` | Node 1 (`query_orchestrator.py`) |
| `GOOGLE_FACT_CHECK_API_KEY` | Node 4B (Fact Check signal) |
| `TAVILY_API_KEY` | Node 4B (Tavily signal) |
| `LANGSEARCH_API_KEY` | Node 2 |
| `LLM_FORCE_OPENROUTER` (+ `OPENROUTER_API_KEY`) | Optional transparent Groq→OpenRouter routing |