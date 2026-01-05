# Hinaing Docs

> **Thesis Title:** Hinaing: A Neuro-Symbolic Multi-Agent Framework for Epistemic Truth Discovery in Civic Social Listening **OR** Hinaing: A Context-Engineered Self-Learning Multi-Agent Agentic AI System with Ensemble Sentiment and 5-Signal Credibility for Public Opinion Analysis in Baguio City

This directory houses the thesis documentation for **Hinaing**, a **hierarchical multi-agent agentic AI system** with real-time intelligent search and self-learning Retrieval-Augmented Generation for context-aware public opinion analysis in Baguio City.

## License

Copyright (c) 2025 Doniele Arys Antonio

This thesis project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) License. See the [LICENSE](../LICENSE) file in the project root for full license text.

Under this license, others are free to share and adapt this work for non-commercial purposes as long as they give appropriate attribution. This means that anyone can use, distribute, and build upon this work for academic and non-commercial purposes while properly crediting the original author.

## System Classification

| Aspect | Classification |
|--------|----------------|
| **Architecture** | Hierarchical Multi-Agent System with Context Engineering |
| **AI Pattern** | Agentic AI (ReAct reasoning, tool use, autonomous planning, multi-agent systems) |
| **Orchestration** | Directed Acyclic Graph (DAG) - LangGraph 7-node pipeline |
| **Learning** | Self-Learning Cyclic RAG (read-write memory loop) |
| **Sentiment** | Ensemble (RoBERTa 40% + LLM 60%) |
| **Credibility** | 5-Signal Weighted Ensemble |

> **Context Engineering**: The entire 7-node architecture is a form of context engineering - we design the pipeline structure, agent specializations, keyword clusters, theme definitions, and credibility signals to inject domain-specific knowledge into the system. Rather than relying on a single LLM prompt, we engineer the context at every node to ensure Baguio-specific civic analysis.

## Agent Summary (13 Total)

| Category | Count | Agents |
|----------|-------|--------|
| **Core Pipeline Agents** | 7 | QueryOrchestratorAgent, RetrievalAgent, SentimentAgent, CredibilityAgent, ContextAugmentationAgent, ThemeRouterAgent, CoordinatorAgent |
| **Theme Sub-Agents** | 6 | InfrastructureAgent, HealthAgent, SafetyAgent, TourismAgent, EconomyAgent, EnvironmentAgent (conditionally spawned) |

> **Note**: Theme Sub-Agents are dynamically spawned by ThemeRouterAgent only when their theme bucket contains documents.

## Novel Contributions

1. **Neuro-Symbolic Cognitive Architecture (Context-Engineered Multi-Agent System)** – Combines rigid expert rules (Symbolic Safety) with flexible LLM reasoning (Neural Nuance). The **7-node pipeline itself is Context Engineering**: each node, agent specialization, keyword cluster, and theme definition injects domain knowledge into the system (Structural Inductive Bias).
2. **Self-Learning Cyclic RAG (Non-Parametric Systemic Learning)** – Node 3 recalls memory → Node 5 writes back. System "learns" via state accumulation without weight updates.
3. **Conditional Sub-Agent Spawning** – Theme agents instantiated only when their bucket has documents (dynamic 7-13 agent count).
4. **5-Signal Epistemic Credibility Framework** – Domain Trust + Semantic Cross-Reference + Google Fact Check + LLM Pattern Detection + Tavily web verification for rigorous truth quantification.
5. **Ensemble Sentiment with Agreement Tracking** – RoBERTa + Gemini with `full_agreement`, `roberta_dominant`, `gemini_dominant` metadata.
6. **A Priori Ontology (KEYWORD_CLUSTERS)** – Pre-defined hierarchical knowledge structure guides the QueryOrchestratorAgent to generate diverse, location-aware queries (Inductive Bias).

## Contents
- `ARCHITECTURE.md` – Detailed implementation diagram with internal agent components, tools, and APIs
- `ARCHITECTURE_SUMMARY.md` – High-level conceptual diagram with 7-node DAG pipeline and temporal memory loop
- `CHAT_ARCHITECTURE.md` – Chat Analyzer (13 agents) and AI Assistant (1 agent) systems
- `ROADMAP.md` – High-level milestones, completed work, and next steps
- `THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md` – The Single Source of Truth for Research Gaps, Novel Contributions, and Theoretical Definitions (PhD Edition)
- `THESIS_FINDINGS.md` – Current thesis findings, capabilities, and remaining gaps
- `DEFENSE_GUIDE.md` – Thesis defense preparation and key differentiators
- `README.md` (this file) – Quick overview plus links to app resources

## Application Overview

### Frontend (Next.js 15 + React 19)
- **Sentiment Generator** – Dashboard for configuring and running 13-agent analysis
- **Chat Analyzer** – Conversational interface with streaming 13-agent pipeline
- **AI Assistant** – Quick Q&A with single ChatAgent + LangSearch

### Backend (FastAPI + LangGraph)
7-Node Multi-Agent Pipeline (13 Agents):

| Node | Agent(s) | Function |
|------|----------|----------|
| 1 | **QueryOrchestratorAgent** | ReAct reasoning with KEYWORD_CLUSTERS for 6 diverse queries |
| 2 | **RetrievalAgent** | LangSearch + Facebook + Reddit ingestion |
| 3 | **ContextAugmentationAgent** | Qdrant cosine similarity search for memory recall |
| 4 | **SentimentAgent** + **CredibilityAgent** + **ThemeRouterAgent** | Parallel analysis (asyncio.gather) |
| 5 | **ContextAugmentationAgent** | Ingest enriched documents to vector store |
| 6 | **ThemeAgent ×6** | `run_theme_agent()` ×6 via ThreadPoolExecutor |
| 7 | **CoordinatorAgent** | `coordinator_agent.run()` for narrative generation |

## Architecture Highlights (13 Agents)

### 1. QueryOrchestratorAgent (ReAct + Context Engineering)
Located in `backend/app/services/agents/query_orchestrator.py`:
- Uses KEYWORD_CLUSTERS for topic diversity (context engineering with 6 curated keyword clusters per focus area)
- Tools: `analyze_focus_areas`, `generate_query`, `expand_contextual_queries`, `evaluate_query`
- Gemini 2.5 Flash for fast reasoning
- Time-based search operators (`after:YYYY-MM-DD`)

### 2. RetrievalAgent
Located in `backend/app/services/insights/agents.py`:
- **LangSearch** – Web search with semantic reranking
- **Facebook** – Apify integration for public pages
- **Reddit** – PRAW integration for r/baguio, r/Philippines, r/CasualPH
- Round-robin interleaving for topic diversity

### 3. SentimentAgent (Ensemble)
Located in `backend/app/services/agents/sentiment_agent.py`:
- **RoBERTa** (40%) – `twitter-roberta-base-sentiment-latest`, trained on 124M tweets
- **Gemini** (60%) – Context-aware LLM classification
- Rich metadata: both predictions, confidence scores, model agreement

### 4. CredibilityAgent (5-Signal)
Located in `backend/app/services/agents/credibility_agent.py`:
- Domain Trust (25%) – Tiered scoring by source type
- Semantic Cross-Reference (20%) – BGE cosine similarity
- Google Fact Check API (15%) – External fact-checker verification
- LLM Pattern Recognition (20%) – Gemini misinformation detection
- Tavily Web Verification (20%) – Real-time claim verification

### 5. ContextAugmentationAgent (RAG)
Located in `backend/app/services/agents/context_agent.py`:
- **SemanticChunker** – 400 chars, 100 overlap
- **EmbeddingService** – BGE-small-en-v1.5 (384 dimensions, CPU-optimized)
- **VectorStore** – Qdrant with **cosine similarity** search
- `retrieve_knowledge()` (Node 3) – Embeds query → Cosine similarity search → Top-K retrieval
- `consolidate_memory()` (Node 5) – Chunks → Embeds → Stores in Qdrant

### 6. ThemeRouterAgent
Located in `backend/app/services/insights/agents.py`:
- Routes documents to 6 theme buckets based on keywords
- Runs in parallel with SentimentAgent and CredibilityAgent

### 7. ThemeAgent (×6 Parallel Execution)
Located in `backend/app/services/agents/theme_agent.py`:
- Single `run_theme_agent()` function called 6 times with different theme labels
- Themes: Infrastructure, Health & Wellness, Public Safety, Tourism & Events, Business & Economy, Environment
- ThreadPoolExecutor with 6 workers for parallel execution

### 8. ChatAgent (Control Group)
Located in `backend/app/services/agents/chat_agent.py`:
- Single agent for quick Q&A
- Gemini 2.0 Flash with function calling
- Baseline comparison for thesis

## Latest Updates (Dec 12, 2025)

### 7-Node Multi-Agent Self-Learning Architecture
- **Node 3**: ContextAugmentationAgent retrieves memories from Qdrant
- **Node 5**: ContextAugmentationAgent ingests enriched documents back
- **Verified Self-Reference Loop**: System successfully recalls past analyses

### Multi-Query Diversity Strategy (QueryOrchestratorAgent)
- KEYWORD_CLUSTERS organized by topic (4 clusters per focus area)
- 6 diverse queries generated per request
- Round-robin diversity merge prevents topic domination

### 5-Signal Credibility Framework (CredibilityAgent)
- Domain Trust + Semantic Cross-Reference + Google Fact Check + LLM Analysis + Tavily
- Misinformation pattern detection (clickbait, conspiracy framing, false certainty)
- Verified sources tracking for claim corroboration

### Reddit Integration (RetrievalAgent)
- PRAW integration for r/baguio, r/Philippines, r/CasualPH
- Query extraction from QueryOrchestratorAgent output
- Location filtering for Baguio-relevant content

## Tech Stack

### Backend
- **Python 3.11+** with **Poetry**
- **FastAPI** – Async web framework
- **LangChain / LangGraph** – Multi-agent orchestration
- **LangSmith** – Observability and tracing
- **LangSearch** – Semantic web search API
- **Google Gemini** – LLM (2.5-flash-lite, 2.5-flash)
- **HuggingFace Transformers** – RoBERTa sentiment model
- **Qdrant** – Vector database (Qdrant Cloud)
- **Sentence Transformers** – BGE-small-en-v1.5 embeddings
- **PRAW** – Reddit API client
- **Apify** – Facebook scraping
- **Tavily** – Web search for fact-checking
- **Supabase** – Database and auth

### Frontend
- **Next.js 15** with **React 19** and **TypeScript**
- **Tailwind CSS** – Utility-first styling
- **SWR** – Data fetching and caching
- **Lucide React** – Icon library

### DevOps
- **Docker** – Containerization
- **Google Cloud Run** – Backend hosting (asia-southeast1)
- **Vercel** – Frontend hosting

## Getting Started
1. Install dependencies via Poetry (backend) and npm (frontend)
2. Set environment variables for LangSearch, Gemini, Reddit, Tavily
3. Run `poetry run uvicorn app.main:create_app --factory --reload` for backend
4. In `frontend/`, run `npm install` then `npm run dev`

## Key Agent Files

| Agent | File |
|-------|------|
| QueryOrchestratorAgent | `backend/app/services/agents/query_orchestrator.py` |
| RetrievalAgent | `backend/app/services/insights/agents.py` |
| SentimentAgent | `backend/app/services/agents/sentiment_agent.py` |
| CredibilityAgent | `backend/app/services/agents/credibility_agent.py` |
| ContextAugmentationAgent | `backend/app/services/agents/context_agent.py` |
| ThemeRouterAgent | `backend/app/services/insights/agents.py` |
| ThemeAgent (×6) | `backend/app/services/agents/theme_agent.py` |
| CoordinatorAgent | `backend/app/services/agents/coordinator_agent.py` |
| ChatAgent (Control) | `backend/app/services/agents/chat_agent.py` |
| LangGraph Pipeline | `backend/app/services/insights/graph.py` |

## Documentation
- **System Architecture**: `docs/ARCHITECTURE.md`
- **Chat Architecture**: `docs/CHAT_ARCHITECTURE.md`
- **Thesis Findings**: `docs/THESIS_FINDINGS.md`
- **Defense Guide**: `docs/DEFENSE_GUIDE.md`
- **Roadmap**: `docs/ROADMAP.md`
