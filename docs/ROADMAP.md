# Project Roadmap

> **Thesis Title:** Hinaing: A Self-Learning Multi-Agent Agentic AI System with RAG for Context-Aware Public Opinion Analysis in Baguio City

This document tracks what has been delivered so far and the remaining work needed to reach the "thesis-grade" target.

> **Context Engineering**: The entire 7-node architecture is a form of context engineering - we design the pipeline structure, agent specializations, keyword clusters, theme definitions, and credibility signals to inject domain-specific knowledge into the system.

## Agent Summary (13 Total)

| Category | Count | Agents |
|----------|-------|--------|
| **Core Pipeline Agents** | 7 | QueryOrchestratorAgent, RetrievalAgent, SentimentAgent, CredibilityAgent, ContextAugmentationAgent, ThemeRouterAgent, CoordinatorAgent |
| **Theme Sub-Agents** | 6 | InfrastructureAgent, HealthAgent, SafetyAgent, TourismAgent, EconomyAgent, EnvironmentAgent |

## Completed Work

### 7-Node Multi-Agent Architecture (13 Agents) - Dec 12, 2025

| Node | Agent(s) | Status |
|------|----------|--------|
| 1 | **QueryOrchestratorAgent** | ✅ ReAct reasoning with KEYWORD_CLUSTERS |
| 2 | **RetrievalAgent** | ✅ LangSearch + Facebook + Reddit |
| 3 | **ContextAugmentationAgent** | ✅ Memory recall from Qdrant |
| 4 | **SentimentAgent + CredibilityAgent + ThemeRouterAgent** | ✅ Parallel via asyncio.gather |
| 5 | **ContextAugmentationAgent** | ✅ Memory consolidation to Qdrant |
| 6 | **6 Theme Agents** | ✅ Parallel via ThreadPoolExecutor |
| 7 | **CoordinatorAgent** | ✅ Narrative generation |

### Agent-Specific Implementations

#### QueryOrchestratorAgent (Context Engineering)
- ReAct reasoning with 4 tools: `analyze_focus_areas`, `generate_query`, `expand_contextual_queries`, `evaluate_query`
- KEYWORD_CLUSTERS for static context engineering (4 clusters per focus area)
- `expand_contextual_queries` for dynamic context engineering (seasonal/temporal awareness)
- 6 diverse queries generated per request
- Time-based search operators (`after:YYYY-MM-DD`)

#### RetrievalAgent
- LangSearch Web API integration
- Facebook ingestion via Apify
- Reddit integration via PRAW (r/baguio, r/Philippines, r/CasualPH)
- Round-robin diversity merge

#### SentimentAgent
- RoBERTa (40%) - `twitter-roberta-base-sentiment-latest`
- Gemini (60%) - Context-aware LLM classification
- Rich metadata: both predictions, confidence scores, model agreement

#### CredibilityAgent (5-Signal Framework)
- Domain Trust (25%) - Tiered scoring (gov.ph = 0.95, social = 0.45)
- Semantic Cross-Reference (20%) - BGE cosine similarity
- Google Fact Check API (15%) - External fact-checker verification
- LLM Pattern Recognition (20%) - Gemini misinformation detection
- Tavily Web Verification (20%) - Real-time claim verification

#### ContextAugmentationAgent (RAG Pipeline)
- `retrieve_knowledge()` (Node 3) - Query embedding → **Cosine similarity search** → Top-K retrieval
- `consolidate_memory()` (Node 5) - Chunk → Embed → Store in Qdrant
- SemanticChunker (400 chars, 100 overlap)
- BGE-small-en-v1.5 embeddings (384 dims)
- Qdrant VectorStore with `Distance.COSINE`

#### ThemeRouterAgent
- Routes documents to 6 theme buckets
- Keyword-based matching with FOCUS_CONCERN_KEYWORDS
- Runs in parallel with SentimentAgent and CredibilityAgent

#### ThemeAgent (×6 Parallel)
- Single `run_theme_agent()` function called 6 times
- Themes: Infrastructure, Health & Wellness, Public Safety, Tourism & Events, Business & Economy, Environment
- ThreadPoolExecutor with 6 workers
- Gemini 2.5 Flash for theme-specific insight generation

### Chat Systems
- **Chat Analyzer** - Streaming SSE with 12-agent pipeline
- **AI Assistant (ChatAgent)** - Single agent for quick Q&A (control group)
- **Intent Detection** - Routes to analyze/simple/followup paths

### Frontend
- Sentiment Generator dashboard with focus area selection
- Chat Analyzer with real-time progress indicator (6 stages)
- AI Assistant with source badges
- Actionable insights cards with evidence links

### Documentation
- ARCHITECTURE.md - 7-node multi-agent pipeline with Mermaid diagrams
- CHAT_ARCHITECTURE.md - Chat systems with agent details
- THESIS_FINDINGS.md - Findings with agent-specific contributions
- DEFENSE_GUIDE.md - Defense preparation

## Latest Updates (Dec 12, 2025)

### Self-Learning Verification (ContextAugmentationAgent)
- **Verified Self-Reference Loop**: System successfully recalls past analyses
- Run 1 (Cold Start): 47 external docs, 0 internal docs
- Run 2 (2 mins later): 49 external docs, 20 internal docs recalled
- Proves the 7-Node Multi-Agent Architecture functions as a learning engine

### Documentation Refresh
- Updated all docs to explicitly mention 12 agents
- Added agent-to-node mapping tables
- Added agent-specific implementation details
- Updated LLM model versions (gemini-2.5-flash-lite, gemini-2.5-flash)

## Previous Updates

### Dec 11, 2025
- Chat Analyzer System with streaming SSE progress
- Intent-based routing (analyze/simple/followup)
- Facebook Page Integration via site: operators
- Enhanced narrative generation (50 docs, 3-5 sentences)

### Dec 10, 2025
- **RetrievalAgent**: Reddit Platform Integration via PRAW
- Target subreddits: r/baguio, r/Philippines, r/CasualPH
- Query extraction from QueryOrchestratorAgent output
- Location filtering for Baguio-relevant content

### Dec 9, 2025
- **QueryOrchestratorAgent**: Time-Based Search Operators (`after:YYYY-MM-DD`)
- Multi-layer freshness filtering
- API-level freshness hints to LangSearch

### Dec 4, 2025
- Narrative generation optimization (gemini-2.0-flash-exp)
- Agent tools consolidation
- Baguio-specific search keywords

### Dec 3, 2025
- **QueryOrchestratorAgent**: Phase 2 - ReAct reasoning with 3 tools
- **ContextAugmentationAgent**: Phase 1 - RAG Pipeline (Chunker + Embeddings + Qdrant)

### Nov 29, 2025
- **SentimentAgent**: Full Ensemble (RoBERTa + Gemini)
- Per-agent latency logging
- Parallel analysis via asyncio.gather

## In Progress / Near-Term TODOs

1. **SentimentAgent Tuning**
   - Tune RoBERTa/Gemini weights based on validation set
   - Add confidence calibration for probability outputs

2. **CredibilityAgent Validation**
   - Create labeled dataset for credibility scoring
   - Measure precision/recall of 5-signal framework

3. **Performance Optimization**
   - Profile and optimize slow agents
   - Consider caching for repeated queries

4. **Observability**
   - Export per-agent telemetry to dashboards
   - Configure alerts for drift and low confidence

## Longer-Term Roadmap

1. **RAG Solutions Agent (New Agent)**
   - Recommend follow-up actions per theme
   - Pull guidance from knowledge base

2. **Human-in-the-Loop Review**
   - Interface for analysts to approve/override agent outputs
   - Continuous improvement loop

3. **Additional Data Sources (RetrievalAgent)**
   - Twitter/X integration
   - Local news RSS feeds
   - Government announcement APIs

4. **Scheduled Analysis**
   - Automated periodic snapshots
   - Trend detection over time

## Architecture Summary (13 Agents)

```
SnapshotRequest
    -> Node 1: QueryOrchestratorAgent (ReAct + KEYWORD_CLUSTERS)
    -> Node 2: RetrievalAgent (LangSearch + Facebook + Reddit)
    -> Node 3: ContextAugmentationAgent.retrieve_knowledge() (Qdrant Cosine Similarity)
    -> Node 4: PARALLEL [SentimentAgent + CredibilityAgent + ThemeRouterAgent]
    -> Node 5: ContextAugmentationAgent.consolidate_memory() (Chunk -> Embed -> Store)
    -> Node 6: ThemeAgent ×6 in PARALLEL (Infrastructure, Health, Safety, Tourism, Economy, Environment)
    -> Node 7: CoordinatorAgent.run() (Narrative Generation)
    -> SnapshotResponse
```

## Key Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Total Agents | 13 | 13+ |
| Documents per request | 50-100 | 100+ |
| Latency (full pipeline) | 30-60s | <30s |
| Theme agents (parallel) | 6 | 6 |
| Credibility signals | 5 | 5 |
| Memory recall accuracy | TBD | >80% |
| Sentiment ensemble accuracy | TBD | >85% |
