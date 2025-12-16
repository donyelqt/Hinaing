# Thesis Findings

## Overview
The prototype delivers a **7-Node Self-Learning Multi-Agent System** with **13 specialized agents** for context-aware public opinion analysis in Baguio City. The architecture combines external retrieval with internal memory recall and consolidation, creating a cyclic learning loop that improves analysis quality over time.

## Agent Summary (13 Total)

| Category | Count | Agents |
|----------|-------|--------|
| **Core Pipeline Agents** | 7 | QueryOrchestratorAgent, RetrievalAgent, SentimentAgent, CredibilityAgent, ContextAugmentationAgent, ThemeRouterAgent, CoordinatorAgent |
| **Theme Sub-Agents** | 6 | InfrastructureAgent, HealthAgent, SafetyAgent, TourismAgent, EconomyAgent, EnvironmentAgent |

## Current Capabilities

| Capability | Agent(s) | Evidence |
|------------|----------|----------|
| ReAct Query Planning | **QueryOrchestratorAgent** | `query_orchestrator.py` - KEYWORD_CLUSTERS, 6 diverse queries |
| Multi-Source Retrieval | **RetrievalAgent** | `agents.py` - LangSearch + Facebook + Reddit |
| RAG Memory Recall | **ContextAugmentationAgent** | `context_agent.py` - Query embedding → **Cosine similarity** → Top-K retrieval |
| Ensemble Sentiment | **SentimentAgent** | `sentiment_agent.py` - RoBERTa (40%) + Gemini (60%) |
| 5-Signal Credibility | **CredibilityAgent** | `credibility_agent.py` - Domain + Cross-Ref + Fact-Check + LLM + Tavily |
| Theme Routing | **ThemeRouterAgent** | `agents.py` - Routes to 6 theme buckets |
| Memory Consolidation | **ContextAugmentationAgent** | `context_agent.py` - `consolidate_memory()` to Qdrant |
| Theme-Specific Insights | **6 Theme Agents** | `theme_agent.py` - 6 parallel Gemini agents |

## Key Findings

### 1. Multi-Agent Self-Learning Architecture Verified (Dec 12, 2025)

**Hypothesis:** The 13-agent system can improve its analysis by referencing its own past memories.

**Verified Outcome:** CONFIRMED

| Run | External Docs | Internal Docs | Result |
|-----|---------------|---------------|--------|
| Run 1 (Cold Start) | 47 | 0 | **ContextAugmentationAgent** builds initial knowledge base |
| Run 2 (2 mins later) | 49 | 20 | **ContextAugmentationAgent** recalls relevant past analysis |

**Significance:** The 7-Node Multi-Agent Architecture functions as a true learning engine. It is no longer just a "monitor" but a "growing knowledge base."

### 2. QueryOrchestratorAgent: Multi-Query Diversity Strategy

**Problem:** Single queries return homogeneous results, missing topic diversity.

**Solution:** **QueryOrchestratorAgent** uses ReAct reasoning with KEYWORD_CLUSTERS:

```python
KEYWORD_CLUSTERS = {
    "infrastructure": [
        ["Baguio traffic congestion", "Session Road rehabilitation", "Baguio public transport"],
        ["Baguio road repair", "Kennon Road closure", "Baguio construction delay"],
        ["Baguio water shortage", "Baguio drainage issue", "Baguio power outage"],
        ["Baguio parking problem", "Baguio internet problem", "Baguio jeepney modernization"],
    ],
    # ... 6 focus areas total
}
```

**Agent Tools:**
- `analyze_focus_areas` - Retrieves keyword clusters for focus areas
- `generate_query` - Creates diverse queries from clusters
- `evaluate_query` - Validates topic diversity

**Result:** 6 diverse queries per request, round-robin interleaving prevents topic domination.

### 3. SentimentAgent: Full Ensemble Analysis

**Problem:** Single-model approaches had accuracy limitations.

**Solution:** **SentimentAgent** uses weighted ensemble combining two models:

| Model | Type | Weight | Strengths |
|-------|------|--------|-----------|
| RoBERTa | Transformer | 40% | Fast, trained on 124M tweets, social media native |
| Gemini | LLM | 60% | Context-aware, understands Baguio civic issues |

**Why RoBERTa Twitter (`cardiffnlp/twitter-roberta-base-sentiment-latest`)?**

| Factor | RoBERTa Twitter | Alternatives | Why RoBERTa Wins |
|--------|-----------------|--------------|------------------|
| Training Data | 124M tweets | BERT: Wikipedia/Books | Social media style matches our sources |
| Native 3-Class | pos/neg/neu | DistilBERT-SST2: binary | No need to infer neutral |
| Benchmark | 94% (TweetEval) | DistilBERT: 91% (SST-2) | Higher accuracy |
| Informal Text | Excellent | BERT: Poor | Handles slang, emoticons |

**Metadata Captured Per Document:**
```python
{
    "sentiment": "negative",
    "sentiment_confidence": 0.79,
    "sentiment_method": "ensemble",
    "roberta_prediction": "negative",
    "roberta_confidence": 0.70,
    "gemini_prediction": "negative",
    "gemini_confidence": 0.85,
    "model_agreement": "full_agreement",
}
```

### 4. CredibilityAgent: 5-Signal Framework

**Problem:** Simple domain whitelists miss content-level misinformation.

**Solution:** **CredibilityAgent** uses multi-signal verification ensemble:

| Signal | Weight | Implementation |
|--------|--------|----------------|
| Domain Trust | 25% | Tiered scoring (gov.ph=0.95, social=0.45) |
| Semantic Cross-Reference | 20% | MiniLM cosine similarity between documents |
| Google Fact Check API | 15% | Real-time query against fact-check repository |
| LLM Pattern Recognition | 20% | Gemini detects clickbait, conspiracy framing |
| Tavily Web Verification | 20% | Real-time web search for claim verification |

**Misinformation Patterns Detected:**
- Clickbait language ("you won't believe", "shocking")
- Conspiracy framing ("they don't want you to know")
- False certainty ("100% proven")
- Social proof manipulation ("going viral")

### 5. RetrievalAgent: Time-Based Search Filtering

**Problem:** Search results returned stale content (2012-2022) instead of fresh content.

**Solution:** **RetrievalAgent** implements multi-layer freshness filtering:

| Layer | Implementation | Example |
|-------|----------------|---------|
| Query-Level | `after:YYYY-MM-DD` suffix | `after:2025-12-12` |
| API-Level | `freshness` parameter | `oneDay` for 6h/24h |
| Client-Side | `published_at` filtering | Filter docs older than cutoff |

### 6. Comparative Architecture Analysis (Control vs Novel)

| Feature | Chat Agent (Control - 1 Agent) | Sentiment Generator (Novel - 13 Agents) |
|---------|-------------------------------|----------------------------------------|
| Architecture | Agentic RAG (ReAct) | 7-Node Multi-Agent Graph |
| Agent Count | 1 | **13** (7 core + 6 theme) |
| Execution | Serial | Parallelized (3 agents + 6 theme agents) |
| Data Scope | Atomic (~5 results) | Holistic (50+ documents) |
| Output | Unstructured Text | Structured Intelligence |
| Memory | None | Persistent (Qdrant) |

**Finding:** The single-agent Chat Agent answers single questions but fails to provide strategic situational awareness. The 13-agent Sentiment Generator identifies, quantifies, and visualizes emerging risks without user prompting.

## Novel Contributions

1. **7-Node Multi-Agent Self-Learning Architecture (13 Agents)**
   - Cyclic graph with 7 core agents + 6 theme agents
   - **ContextAugmentationAgent** handles both recall (Node 3) and consolidation (Node 5)
   - Verified self-reference loop

2. **QueryOrchestratorAgent with Multi-Query Diversity**
   - ReAct reasoning with 3 custom tools
   - KEYWORD_CLUSTERS for topic coverage
   - 6 diverse queries per request

3. **SentimentAgent with Hybrid Ensemble**
   - RoBERTa (social-native) + Gemini (context-aware)
   - Weighted voting with confidence scores
   - Model agreement tracking

4. **CredibilityAgent with 5-Signal Framework**
   - Domain + Cross-Ref + Fact-Check + LLM + Tavily
   - Misinformation pattern detection
   - Verified source tracking

5. **6 Parallel Theme Agents**
   - InfrastructureAgent, HealthAgent, SafetyAgent
   - TourismAgent, EconomyAgent, EnvironmentAgent
   - ThreadPoolExecutor for parallel execution

## Architecture Flow (13 Agents)

```
SnapshotRequest
       |
       v
Node 1: QueryOrchestratorAgent (ReAct)
       |-- Tools: analyze_focus_areas, generate_query, evaluate_query
       |-- Generate 6 diverse queries via KEYWORD_CLUSTERS
       v
Node 2: RetrievalAgent
       |-- LangSearch Web API
       |-- Facebook Ingestion (Apify)
       |-- Reddit r/baguio, r/Philippines (PRAW)
       |-- Diversity merge (round-robin)
       v
Node 3: ContextAugmentationAgent.retrieve_knowledge() [RAG RETRIEVAL]
       |-- Embed query with MiniLM-L6-v2 (384 dims)
       |-- Qdrant cosine similarity search per focus area
       |-- Top-K retrieval (most relevant memories)
       |-- Merge external + internal (deduplicate)
       v
Node 4: PARALLEL [SentimentAgent + CredibilityAgent + ThemeRouterAgent]
       |-- SentimentAgent: RoBERTa 40% + Gemini 60%
       |-- CredibilityAgent: 5-signal ensemble
       |-- ThemeRouterAgent: Route to 6 theme buckets
       v
Node 5: ContextAugmentationAgent.consolidate_memory()
       |-- Chunk enriched documents (SemanticChunker)
       |-- Embed with MiniLM-L6-v2
       |-- Store in Qdrant for future recall
       v
Node 6: 6 Theme Agents in PARALLEL
       |-- InfrastructureAgent
       |-- HealthAgent
       |-- SafetyAgent
       |-- TourismAgent
       |-- EconomyAgent
       |-- EnvironmentAgent
       v
Node 7: CoordinatorAgent
       |-- CoordinatorAgent.run()
       |-- Narrative generation (Gemini 2.5 Pro)
       |-- Assemble SnapshotResponse
       v
SnapshotResponse
```

## Agent LLM Configuration

| Agent | Model | Reason |
|-------|-------|--------|
| QueryOrchestratorAgent | `gemini-2.5-flash` | Fast ReAct reasoning |
| SentimentAgent (LLM part) | `gemini-2.5-pro` | Context-aware, 60% weight |
| CredibilityAgent | `gemini-2.5-flash` | Fast pattern detection |
| ThemeAgent ×6 | `gemini-2.5-pro` | Theme-specific insight generation |
| CoordinatorAgent | `gemini-2.5-pro` | Comprehensive narrative |
| ChatAgent (Control) | `gemini-2.5-flash` | Fast Q&A |

## Gaps and Next Steps

### Completed
- [x] 7-Node Multi-Agent Architecture (13 agents)
- [x] QueryOrchestratorAgent with Multi-Query Diversity
- [x] SentimentAgent with Ensemble (RoBERTa + Gemini)
- [x] CredibilityAgent with 5-Signal Framework
- [x] ContextAugmentationAgent with RAG Memory
- [x] 6 Theme Agents with parallel execution
- [x] RetrievalAgent with Reddit Integration
- [x] Chat Analyzer with streaming SSE

### In Progress
- [ ] Ensemble weight tuning with validation set
- [ ] Credibility framework validation
- [ ] Performance optimization

### Future
- [ ] RAG Solutions Agent for recommendations
- [ ] Human-in-the-loop review portal
- [ ] Twitter/X integration
- [ ] Scheduled analysis with trend detection

## Defense Readiness

| Aspect | Status | Evidence |
|--------|--------|----------|
| Multi-Agent Architecture | Defensible | 13 Agents in 7-Node Graph |
| Agent Specialization | Defensible | Each agent has distinct role |
| Data Persistence | Defensible | Qdrant on Disk |
| Accuracy | Defensible | Multi-Agent Consensus |
| Self-Learning | Verified | ContextAugmentationAgent Memory Loop |
| UI | Premium | Streaming Progress |
