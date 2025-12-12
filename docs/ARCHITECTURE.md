# Hinaing System Architecture

## Overview

Multi-Agentic AI system with real-time intelligent search and RAG for context-aware public opinion analysis in Baguio City. Features a **7-Node Self-Learning Architecture** that combines external retrieval with internal memory recall and consolidation.

## Agent Count Summary

| Category | Agents | Notes |
|----------|--------|-------|
| **Core Pipeline Agents** | 6 | Query Orchestrator, Retrieval, Sentiment, Credibility, Context, Theme Router |
| **Theme Sub-Agents** | 6 | Infrastructure, Health, Safety, Tourism, Economy, Environment |
| **Total** | **12** | 6 main + 6 theme-specific |

> **Optimization Note**: Sentiment, Credibility, and Theme Router agents now run **in parallel** via `asyncio.gather` in a single unified analysis node, reducing latency significantly.

## LLM Configuration

| Component | Model | Reason |
|-----------|-------|--------|
| **Narrative Summary** | `gemini-2.5-pro` | Comprehensive topic coverage |
| **Query Orchestrator** | `gemini-2.5-flash` | Fast ReAct loop for query planning |
| **Sentiment Agent (LLM)** | `gemini-2.5-pro` | Context-aware classification, 60% ensemble weight |
| **Credibility Agent** | `gemini-2.5-flash` | Fast content quality scoring |
| **Theme Agents (6x)** | `gemini-2.5-flash` | Fast insight generation |
| **Chat Agent** | `gemini-2.0-flash-exp` | Fast Q&A responses |
| **RoBERTa** | `twitter-roberta-base-sentiment-latest` | Local model, 40% ensemble weight |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Local 384-dim vectors for RAG |

## 7-Node Self-Learning Pipeline

The system implements a cyclic learning architecture where fresh external data is merged with internal memory, analyzed, and then consolidated back into the knowledge base.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    7-NODE MULTI-AGENT SELF-LEARNING PIPELINE                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   NODE 1     │    │   NODE 2     │    │   NODE 3     │                  │
│  │   Query      │───▶│  Retrieval   │───▶│   Context    │                  │
│  │ Orchestrator │    │    Agent     │    │    Agent     │                  │
│  │    Agent     │    │ (Web/FB/RD)  │    │  (Recall)    │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                 │                           │
│                                                 ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   NODE 7     │    │   NODE 6     │    │   NODE 4     │                  │
│  │ Coordinator  │◀───│  6 Theme     │◀───│  3 Agents    │                  │
│  │    Agent     │    │   Agents     │    │  (Parallel)  │                  │
│  │ (Narrative)  │    │  (Parallel)  │    │ Sent+Cred+TR │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                 │                           │
│                                                 ▼                           │
│                                          ┌──────────────┐                  │
│                                          │   NODE 5     │                  │
│                                          │   Context    │◀─── LEARNING     │
│                                          │    Agent     │     LOOP         │
│                                          │ (Consolidate)│                  │
│                                          └──────────────┘                  │
│                                                                             │
│  TOTAL: 12 AGENTS (6 Core + 6 Theme)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Node Descriptions (Agent Mapping)

| Node | Agent(s) | Function | Key Components |
|------|----------|----------|----------------|
| 1 | **QueryOrchestratorAgent** | ReAct reasoning to generate diverse search queries | KEYWORD_CLUSTERS, 3 tools, Gemini 2.5 Flash |
| 2 | **RetrievalAgent** | Fetch fresh documents from web, Facebook, Reddit | LangSearch, PRAW, Apify, parallel batching |
| 3 | **ContextAugmentationAgent** | Retrieve relevant memories from vector store | Qdrant, MiniLM embeddings, `retrieve_knowledge()` |
| 4 | **SentimentAgent** + **CredibilityAgent** + **ThemeRouterAgent** | Parallel sentiment + credibility + theme routing | asyncio.gather, RoBERTa+Gemini ensemble, 5-signal credibility |
| 5 | **ContextAugmentationAgent** | Ingest enriched documents into knowledge base | SemanticChunker, VectorStore, `consolidate_memory()` |
| 6 | **6 Theme Agents** (Infrastructure, Health, Safety, Tourism, Economy, Environment) | Generate insights per theme category | 6x parallel Gemini calls, ThreadPoolExecutor |
| 7 | **Coordinator** (GeminiClient) | Assemble final response with narrative | Gemini 2.5 Pro narrative generation |

## System Flow Diagram

```mermaid
flowchart TB
    subgraph Frontend["Frontend (Next.js 15)"]
        UI[Sentiment Dashboard]
        Insights[Actionable Insights Cards]
        Sources[Source Evidence Links]
    end

    subgraph Backend["Backend (FastAPI + LangGraph)"]
        subgraph Workflow["7-Node Multi-Agent Pipeline"]
            
            subgraph Node1["Node 1: Query Orchestrator Agent (ReAct)"]
                QO[QueryOrchestratorAgent]
                T1[analyze_focus_areas tool]
                T2[generate_query tool]
                T3[evaluate_query tool]
                QO --> T1 & T2 & T3
                QP[QueryPlan<br/>6 diverse queries]
                T1 & T2 & T3 --> QP
            end

            subgraph Node2["Node 2: Retrieval Agent"]
                RA[RetrievalAgent]
                LS[LangSearch Web API]
                FB[Facebook Ingestion]
                RD[Reddit r/baguio]
                RA --> LS & FB & RD
                RR[Diversity Merge]
                LS & FB & RD --> RR
                ExtDocs[External Documents]
                RR --> ExtDocs
            end

            subgraph Node3["Node 3: Context Agent (Memory Recall)"]
                CTX[ContextAugmentationAgent]
                VS1[Qdrant Vector Search]
                EM1[MiniLM Embeddings]
                CTX --> VS1
                IntDocs[Internal Documents]
                VS1 --> IntDocs
                Merge[Deduplicate & Merge]
                ExtDocs --> Merge
                IntDocs --> Merge
            end

            subgraph Node4["Node 4: Unified Analysis (3 Agents in Parallel)"]
                direction TB
                subgraph Parallel["asyncio.gather"]
                    SA[SentimentAgent<br/>RoBERTa 40% + Gemini 60%]
                    CA[CredibilityAgent<br/>5-Signal Ensemble]
                    TR[ThemeRouterAgent<br/>6 theme buckets]
                end
                SA & CA & TR --> ED[Enriched + Routed Docs]
            end

            subgraph Node5["Node 5: Context Agent (Memory Consolidation)"]
                CTX2[ContextAugmentationAgent]
                SC[Semantic Chunker<br/>400 chars]
                ES[Embedding Service<br/>MiniLM-L6-v2]
                VS2[Qdrant VectorStore]
                CTX2 --> SC --> ES --> VS2
            end

            subgraph Node6["Node 6: Theme Agents (6 Agents in Parallel)"]
                TH1[InfrastructureAgent]
                TH2[HealthAgent]
                TH3[SafetyAgent]
                TH4[TourismAgent]
                TH5[EconomyAgent]
                TH6[EnvironmentAgent]
                TI[Theme Insights]
                TH1 & TH2 & TH3 & TH4 & TH5 & TH6 --> TI
            end

            subgraph Node7["Node 7: Coordinator Agent"]
                GC[GeminiClient<br/>gemini-2.5-pro]
                NR[Narrative Generation]
                GC --> NR
                SR[SnapshotResponse]
                NR --> SR
            end

            Node1 --> Node2 --> Node3 --> Node4
            Node4 --> Node5 --> Node6 --> Node7
        end
    end

    Request[SnapshotRequest] --> Node1
    SR --> Response[SnapshotResponse JSON]
    Response --> Frontend

    style Node1 fill:#e1f5fe
    style Node2 fill:#fff3e0
    style Node3 fill:#e8f5e9
    style Node4 fill:#f3e5f5
    style Node5 fill:#fff8e1
    style Node6 fill:#fce4ec
    style Node7 fill:#e0f2f1
```



## Detailed Agent Flow (Sequence Diagram)

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant QO as Query Orchestrator
    participant RA as Retrieval Agent
    participant MEM as Memory (Qdrant)
    participant ANALYZE as Unified Analysis
    participant TA as Theme Agents
    participant GC as GeminiClient

    Client->>API: POST /insights/snapshot
    API->>QO: SnapshotRequest
    
    Note over QO: ReAct Loop (Gemini 2.5 Flash)
    QO->>QO: analyze_focus_areas → KEYWORD_CLUSTERS
    QO->>QO: generate_query → 6 diverse queries
    QO->>QO: evaluate_query → diversity check
    QO-->>RA: QueryPlan (6 queries)

    par Parallel External Retrieval (Batches of 3)
        RA->>RA: LangSearch Web API
        RA->>RA: Facebook Ingestion
        RA->>RA: Reddit r/baguio, r/Philippines
    end
    RA->>RA: Diversity Merge (round-robin)
    RA-->>MEM: External Documents

    Note over MEM: Node 3: Internal Recall
    MEM->>MEM: Vector search per focus area
    MEM-->>ANALYZE: External + Internal (deduplicated)

    Note over ANALYZE: Node 4: All 3 run in parallel via asyncio.gather
    par Unified Analysis (Single Node)
        ANALYZE->>ANALYZE: Sentiment (RoBERTa 40% + Gemini 60%)
        ANALYZE->>ANALYZE: Credibility (5-signal ensemble)
        ANALYZE->>ANALYZE: Theme Routing (6 buckets)
    end
    ANALYZE-->>MEM: Enriched Documents

    Note over MEM: Node 5: Memory Consolidation
    MEM->>MEM: Chunk → Embed → Store
    MEM-->>TA: Theme-routed documents

    par 6 Theme Agents (ThreadPool)
        TA->>TA: Infrastructure
        TA->>TA: Health & Wellness
        TA->>TA: Public Safety
        TA->>TA: Tourism & Events
        TA->>TA: Business & Economy
        TA->>TA: Environment
    end
    TA-->>GC: Theme Insights

    GC->>GC: Narrative Generation (Gemini 2.5 Pro)
    GC-->>API: SnapshotResponse
    API-->>Client: JSON Response
```

## Component Architecture

```mermaid
graph LR
    subgraph External["External Services"]
        LS[LangSearch API]
        FB[Facebook/Apify]
        RD[Reddit/PRAW]
        GEMINI[Google Gemini API]
        TAVILY[Tavily API]
        GFACT[Google Fact Check API]
    end

    subgraph Models["ML Models"]
        ROBERTA[RoBERTa<br/>twitter-roberta-base-sentiment-latest]
        MINILM[MiniLM-L6-v2<br/>Sentence Embeddings]
    end

    subgraph Storage["Storage"]
        QDRANT[Qdrant<br/>Vector Store<br/>Persistent Disk]
        SUPA[Supabase<br/>Database]
    end

    subgraph LangGraphNodes["LangGraph Pipeline (7 Nodes)"]
        NODE1[Node 1: Query Orchestrator]
        NODE2[Node 2: External Retrieval<br/>Web/FB/Reddit]
        NODE3[Node 3: Internal Retrieval<br/>Memory Recall]
        
        subgraph NODE4["Node 4: Unified Analysis (asyncio.gather)"]
            SNA[Sentiment Agent]
            CRA[Credibility Agent]
            TRA[Theme Router]
        end
        
        NODE5[Node 5: Memory Consolidation<br/>Ingest to Qdrant]
        
        subgraph NODE6["Node 6: Theme Agents (ThreadPool)"]
            TH1[Infrastructure]
            TH2[Health]
            TH3[Safety]
            TH4[Tourism]
            TH5[Economy]
            TH6[Environment]
        end
        
        NODE7[Node 7: Build Snapshot<br/>Narrative Generation]
    end

    %% External connections
    LS --> NODE2
    FB --> NODE2
    RD --> NODE2
    GEMINI --> NODE1
    GEMINI --> SNA
    GEMINI --> CRA
    GEMINI --> TH1 & TH2 & TH3 & TH4 & TH5 & TH6
    GEMINI --> NODE7
    TAVILY --> CRA
    GFACT --> CRA
    ROBERTA --> SNA
    MINILM --> NODE3
    MINILM --> NODE5
    QDRANT --> NODE3
    QDRANT --> NODE5

    %% Pipeline flow
    NODE1 --> NODE2
    NODE2 --> NODE3
    NODE3 --> NODE4
    NODE4 --> NODE5
    NODE5 --> NODE6
    NODE6 --> NODE7
```

## Theme Groups

| Theme | Label | Keywords | Focus Values |
|-------|-------|----------|--------------|
| infrastructure | Infrastructure | road, traffic, water, power, bridge, construction, kennon, session road | infrastructure |
| health | Health & Wellness | hospital, clinic, dengue, covid, vaccine, medicine, bgh | health |
| safety | Public Safety | crime, police, fire, landslide, accident, emergency, flood, walkout, protest | safety |
| tourism | Tourism & Events | tourist, hotel, festival, panagbenga, visitor, burnham, overcrowding | tourism |
| economy | Business & Economy | market, vendor, livelihood, mallification, SM Prime, price, displacement | economy, business |
| environment | Environment | garbage, pollution, waste, tree, climate, air quality, flooding | environment |

## The 5-Signal Credibility Framework

The `CredibilityAgent` employs a **Multi-Signal Verification Strategy** with weighted ensemble:

| Signal | Weight | Description |
|--------|--------|-------------|
| **Domain Trust** | 25% | Tiered scoring (gov.ph = 0.95, social media = 0.45) |
| **Semantic Cross-Reference** | 20% | MiniLM embeddings for cosine similarity between documents |
| **Google Fact Check API** | 15% | Real-time query against Google's fact-check repository |
| **LLM Pattern Recognition** | 20% | Gemini analyzes for clickbait, conspiracy framing, misinformation |
| **Tavily Web Verification** | 20% | Real-time web search to verify claims against authoritative sources |

### Domain Trust Tiers

| Tier | Score | Examples |
|------|-------|----------|
| Government | 0.90-0.95 | gov.ph, pia.gov.ph, pna.gov.ph |
| Fact-checkers | 0.85-0.90 | verafiles.org, rappler.com |
| Established News | 0.75-0.82 | inquirer.net, philstar.com, gmanetwork.com |
| Organizations | 0.65-0.70 | .org.ph, .org |
| Social Media | 0.40-0.50 | facebook.com, reddit.com, twitter.com |
| User-generated | 0.35-0.45 | medium.com, wordpress.com |

## Time-Based Search Filtering

Multi-layer approach to prioritize fresh content:

### 1. Query-Level Time Operators
Search queries include Google-style `after:YYYY-MM-DD` operators:

| Time Window | Search Suffix | Example |
|-------------|---------------|---------|
| 6h | `after:{today}` | `after:2025-12-12` |
| 24h | `after:{yesterday}` | `after:2025-12-11` |
| 3d | `after:{3 days ago}` | `after:2025-12-09` |
| 7d | `after:{7 days ago}` | `after:2025-12-05` |

### 2. API-Level Freshness Hints
LangSearch API receives a `freshness` parameter:
- `6h` / `24h` → `oneDay`
- `3d` / `7d` → `oneWeek`

### 3. Client-Side Time Filtering
Documents filtered by `published_at` timestamp after retrieval.

## Multi-Query Diversity Strategy

The Query Orchestrator generates **6 diverse queries** using KEYWORD_CLUSTERS:

```python
KEYWORD_CLUSTERS = {
    "infrastructure": [
        ["Baguio traffic congestion", "Session Road rehabilitation", "Baguio public transport"],
        ["Baguio road repair", "Kennon Road closure", "Baguio construction delay"],
        ["Baguio water shortage", "Baguio drainage issue", "Baguio power outage"],
        ...
    ],
    "health": [...],
    "safety": [...],
    ...
}
```

**Strategy**: One query per cluster ensures topic diversity. Results are merged using round-robin interleaving to prevent any single topic from dominating.

## Data Flow Summary (12 Agents)

```
SnapshotRequest
    → Node 1: QueryOrchestratorAgent (ReAct + KEYWORD_CLUSTERS)
    → Node 2: RetrievalAgent (LangSearch + Facebook + Reddit)
    → Node 3: ContextAugmentationAgent.retrieve_knowledge() (Qdrant Memory Recall)
    → Node 4: PARALLEL [SentimentAgent + CredibilityAgent + ThemeRouterAgent]
    → Node 5: ContextAugmentationAgent.consolidate_memory() (Chunk → Embed → Store)
    → Node 6: 6 ThemeAgents in PARALLEL (Infrastructure, Health, Safety, Tourism, Economy, Environment)
    → Node 7: CoordinatorAgent (Narrative Generation with Gemini 2.5 Pro)
    → SnapshotResponse
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+, Poetry |
| Orchestration | LangChain, LangGraph |
| LLM | Google Gemini (2.5-pro for narrative/sentiment, 2.5-flash for orchestration/credibility/theme) |
| Sentiment | RoBERTa (twitter-roberta-base-sentiment-latest) |
| Embeddings | MiniLM-L6-v2 (384 dimensions) |
| Vector DB | Qdrant (persistent disk storage) |
| Search | LangSearch API |
| Social | Reddit (PRAW), Facebook (Apify) |
| Fact-Check | Google Fact Check API, Tavily |
| Database | Supabase |
| Observability | LangSmith |

## Hybrid Architectures (Control vs Novel)

### A. The Chat Agent (Control Group)
- **Pattern:** Agentic RAG (ReAct Loop)
- **Goal:** Single-turn, atomic question answering
- **Stack:** Gemini 2.0 Flash + LangSearch
- **Behavior:** Reactive, waiting for user input

### B. The Sentiment Generator (Novel Contribution)
- **Pattern:** Hierarchical Graph-Based Multi-Agent System with Self-Learning
- **Goal:** Holistic, proactive landscape analysis with memory
- **Stack:** LangGraph + 7-Node Pipeline + Ensemble Sentiment + 5-Signal Credibility
- **Behavior:** Proactive, scans environment, learns from each run

## Key Implementation Files

| Component | File |
|-----------|------|
| LangGraph Pipeline | `backend/app/services/insights/graph.py` |
| Agent Orchestrators | `backend/app/services/insights/agents.py` |
| Agent Tools | `backend/app/services/insights/agent_tools.py` |
| Query Orchestrator | `backend/app/services/agents/query_orchestrator.py` |
| Sentiment Agent | `backend/app/services/agents/sentiment_agent.py` |
| Credibility Agent | `backend/app/services/agents/credibility_agent.py` |
| Context Agent | `backend/app/services/agents/context_agent.py` |
| Theme Agent | `backend/app/services/agents/theme_agent.py` |
| RAG Chunker | `backend/app/services/rag/chunker.py` |
| RAG Embeddings | `backend/app/services/rag/embeddings.py` |
| RAG Vector Store | `backend/app/services/rag/vector_store.py` |
| LangSearch Client | `backend/app/services/langsearch.py` |
| Reddit Ingestion | `backend/app/services/ingestion/reddit.py` |
| Facebook Ingestion | `backend/app/services/ingestion/facebook.py` |
