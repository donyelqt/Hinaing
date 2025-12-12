# Chat Systems Architecture

## Overview

Hinaing provides two distinct chat interfaces with different agent architectures:

| Feature | Chat Analyzer (12 Agents) | AI Assistant (1 Agent) |
|---------|---------------------------|------------------------|
| **Purpose** | Deep sentiment analysis | Quick Q&A |
| **Endpoint** | `POST /chat/analyze` | `POST /chat/` |
| **Response** | Streaming (SSE) | Sync JSON |
| **Agent Count** | **12** (6 core + 6 theme) | **1** (ChatAgent) |
| **Pipeline** | 7-node multi-agent | Single LLM + tool call |
| **Latency** | 15-30 seconds | 2-5 seconds |
| **Memory** | Persistent (Qdrant) | None |

## Agent Summary

### Chat Analyzer Agents (12 Total)

| Category | Count | Agents |
|----------|-------|--------|
| **Core Pipeline** | 6 | QueryOrchestratorAgent, RetrievalAgent, SentimentAgent, CredibilityAgent, ContextAugmentationAgent, ThemeRouterAgent |
| **Theme Sub-Agents** | 6 | InfrastructureAgent, HealthAgent, SafetyAgent, TourismAgent, EconomyAgent, EnvironmentAgent |

### AI Assistant Agent (1 Total)

| Agent | Function |
|-------|----------|
| **ChatAgent** | Single ReAct agent with LangSearch tool for quick Q&A |

---

## Chat Analyzer System Flow (12 Agents)

```mermaid
flowchart TB
    subgraph Frontend["Frontend (Next.js 15)"]
        UI[Chat Analyze Page]
        Progress[Progress Indicator<br/>6 Stages]
        Results[Analysis Result Card]
        Sources[Supporting Conversations]
    end

    subgraph Backend["Backend (FastAPI)"]
        subgraph IntentRouter["Intent Detection"]
            ID[detect_intent]
            ID --> |"analyze"| Pipeline
            ID --> |"simple"| Simple
            ID --> |"followup"| Followup
        end

        subgraph Pipeline["7-Node Multi-Agent Pipeline (12 Agents)"]
            subgraph Node1["Node 1: QueryOrchestratorAgent (10%)"]
                QO[QueryOrchestratorAgent]
                QO --> |KEYWORD_CLUSTERS| QP[QueryPlan<br/>6 diverse queries]
            end

            subgraph Node2["Node 2: RetrievalAgent (25%)"]
                RA[RetrievalAgent]
                LS[LangSearch + FB Pages]
                RD[Reddit r/baguio]
                RA --> LS & RD
                LS & RD --> Docs[External Documents]
            end

            subgraph Node3["Node 3: ContextAugmentationAgent - RAG Retrieval (35%)"]
                CTX1[ContextAugmentationAgent]
                EM1[MiniLM-L6-v2<br/>Query Embedding]
                VS[Qdrant<br/>Cosine Similarity]
                TopK[Top-K Results]
                CTX1 --> EM1 --> VS --> TopK
                TopK --> IntDocs[Internal Documents]
                Docs --> Merge[Deduplicate & Merge]
                IntDocs --> Merge
            end

            subgraph Node4["Node 4: 3 Agents in Parallel (55%)"]
                direction TB
                subgraph ParallelOps["asyncio.gather"]
                    SA[SentimentAgent<br/>RoBERTa + Gemini]
                    CA[CredibilityAgent<br/>5-Signal Ensemble]
                    TR[ThemeRouterAgent<br/>6 buckets]
                end
                SA & CA & TR --> ED[Enriched Docs]
            end

            subgraph Node5["Node 5: ContextAugmentationAgent (70%)"]
                CTX2[ContextAugmentationAgent]
                CH[Semantic Chunker]
                EM[MiniLM-L6 Embeddings]
                VS2[Qdrant Store]
                CTX2 --> CH --> EM --> VS2
            end

            subgraph Node6["Node 6: 6 Theme Agents in Parallel (90%)"]
                T1[InfrastructureAgent]
                T2[HealthAgent]
                T3[SafetyAgent]
                T4[TourismAgent]
                T5[EconomyAgent]
                T6[EnvironmentAgent]
            end

            Node1 --> Node2 --> Node3 --> Node4 --> Node5 --> Node6
        end

        subgraph Simple["Simple Q&A Path (1 Agent)"]
            CA2[ChatAgent]
            LSS[LangSearch]
            GF[Gemini Flash]
            CA2 --> LSS --> GF
        end

        subgraph Followup["Follow-up Path"]
            Cache[Session Cache]
            RAG[RAG on Cached Results]
            Cache --> RAG
        end

        subgraph Output["Node 7: CoordinatorAgent"]
            NR[CoordinatorAgent<br/>Gemini 2.5 Pro]
            SR[SnapshotResponse]
            NR --> SR
        end

        Pipeline --> Output
    end

    Request[User Message] --> IntentRouter
    SR --> |SSE Stream| Frontend
    Simple --> |JSON| Frontend
    Followup --> |JSON| Frontend

    style Node1 fill:#e1f5fe
    style Node2 fill:#fff3e0
    style Node3 fill:#e8f5e9
    style Node4 fill:#f3e5f5
    style Node5 fill:#fff8e1
    style Node6 fill:#fce4ec
    style Simple fill:#e0f7fa
    style Followup fill:#f1f8e9
```

---

## Chat Analyzer Sequence Diagram (12 Agents)

```mermaid
sequenceDiagram
    participant Client
    participant API as /chat/analyze
    participant ID as Intent Detector
    participant QO as QueryOrchestratorAgent
    participant RA as RetrievalAgent
    participant CTX as ContextAugmentationAgent
    participant SA as SentimentAgent
    participant CA as CredibilityAgent
    participant TR as ThemeRouterAgent
    participant TA as 6 Theme Agents
    participant CO as CoordinatorAgent

    Client->>API: POST {message, session_id, history}
    API->>ID: detect_intent(message, history)
    
    alt Intent = "analyze"
        ID-->>API: "analyze"
        
        API-->>Client: SSE: {stage: "start", progress: 0.0}
        
        Note over QO: Node 1: QueryOrchestratorAgent
        API->>QO: parse_user_intent(message)
        QO->>QO: ReAct: analyze_focus_areas tool
        QO->>QO: ReAct: generate_query tool (KEYWORD_CLUSTERS)
        QO->>QO: ReAct: evaluate_query tool
        API-->>Client: SSE: {stage: "query_orchestrator", progress: 0.1}
        
        Note over RA: Node 2: RetrievalAgent
        API->>RA: fetch_documents(QueryPlan)
        par Parallel External Retrieval
            RA->>RA: LangSearch + FB Pages
            RA->>RA: Reddit Search (PRAW)
        end
        RA->>RA: Diversity Merge (round-robin)
        API-->>Client: SSE: {stage: "retrieval", progress: 0.25}
        
        Note over CTX: Node 3: RAG Retrieval (Cosine Similarity)
        API->>CTX: retrieve_internal_knowledge(focus_areas)
        CTX->>CTX: Embed query with MiniLM-L6-v2
        CTX->>CTX: Qdrant cosine similarity search
        CTX->>CTX: Top-K most relevant memories
        CTX-->>API: Internal + External (deduplicated)
        API-->>Client: SSE: {stage: "recall", progress: 0.35}
        
        Note over SA,TR: Node 4: 3 Agents in Parallel (asyncio.gather)
        API->>SA: analyze_sentiment(docs)
        API->>CA: score_credibility(docs)
        API->>TR: route_by_theme(docs)
        par asyncio.gather
            SA->>SA: RoBERTa 40% + Gemini 60%
            CA->>CA: 5-signal ensemble
            TR->>TR: Route to 6 theme buckets
        end
        API-->>Client: SSE: {stage: "analyze", progress: 0.55}
        
        Note over CTX: Node 5: ContextAugmentationAgent.consolidate_memory()
        API->>CTX: consolidate_memory(enriched_docs)
        CTX->>CTX: Chunk -> Embed -> Store in Qdrant
        API-->>Client: SSE: {stage: "memory", progress: 0.70}
        
        Note over TA: Node 6: 6 Theme Agents in Parallel (ThreadPoolExecutor)
        API->>TA: generate_insights(theme_docs)
        par 6 Parallel Theme Agents
            TA->>TA: InfrastructureAgent
            TA->>TA: HealthAgent
            TA->>TA: SafetyAgent
            TA->>TA: TourismAgent
            TA->>TA: EconomyAgent
            TA->>TA: EnvironmentAgent
        end
        API-->>Client: SSE: {stage: "themes", progress: 0.9}
        
        Note over CO: Node 7: CoordinatorAgent
        API->>CO: build_snapshot()
        CO->>CO: Narrative generation (Gemini 2.5 Pro)
        
        API-->>Client: SSE: {type: "result", data: AnalysisData}
        
    else Intent = "simple"
        ID-->>API: "simple"
        Note over API: Single ChatAgent
        API->>API: run_chat_agent(message)
        API-->>Client: JSON: {message, sources}
        
    else Intent = "followup"
        ID-->>API: "followup"
        API->>API: RAG on _session_cache
        API-->>Client: JSON: {message}
    end
```

---

## AI Assistant Architecture (1 Agent)

```mermaid
flowchart TB
    subgraph Frontend["Frontend (Next.js 15)"]
        ChatUI[Chat Page]
        MsgBubble[Message Bubbles]
        SourceBadges[Source Badges]
    end

    subgraph Backend["Backend (FastAPI)"]
        subgraph SingleAgent["ChatAgent (1 Agent)"]
            CA[ChatAgent]
            GF[Gemini 2.0 Flash]
            FC[Function Calling]
            CA --> GF --> FC
        end

        subgraph Tools["Available Tools"]
            SCD[search_civic_data]
        end

        subgraph Search["LangSearch Client"]
            LS[LangSearch API]
            FB[+ Facebook PIO Pages]
            LS --> FB
        end

        FC --> |tool_call| SCD
        SCD --> Search
        Search --> |results| FC
        FC --> |final_response| Response[JSON Response]
    end

    Request[User Message + History] --> SingleAgent
    Response --> Frontend

    style SingleAgent fill:#e1f5fe
    style Search fill:#fff3e0
```

---

## Agent Comparison: Chat Analyzer vs AI Assistant

| Aspect | Chat Analyzer (12 Agents) | AI Assistant (1 Agent) |
|--------|---------------------------|------------------------|
| **QueryOrchestratorAgent** | ✅ ReAct with 3 tools | ❌ None |
| **RetrievalAgent** | ✅ LangSearch + FB + Reddit | ❌ LangSearch only (via tool) |
| **ContextAugmentationAgent** | ✅ Memory recall + consolidation | ❌ None |
| **SentimentAgent** | ✅ RoBERTa + Gemini ensemble | ❌ None |
| **CredibilityAgent** | ✅ 5-signal framework | ❌ None |
| **ThemeRouterAgent** | ✅ 6 theme buckets | ❌ None |
| **6 Theme Agents** | ✅ Parallel Gemini | ❌ None |
| **ChatAgent** | ❌ Not used | ✅ Single agent |
| **Memory** | ✅ Qdrant persistent | ❌ None |
| **Parallelization** | ✅ Nodes 4 + 6 | ❌ None |

---

## Intent Detection Logic

```mermaid
flowchart TD
    MSG[User Message] --> KW{Contains analyze keywords?}
    
    KW --> |Yes| ANALYZE[Intent: analyze<br/>-> 12 Agents]
    KW --> |No| HIST{Has recent analysis<br/>in history?}
    
    HIST --> |Yes| FU{Contains followup keywords?}
    HIST --> |No| FOCUS{Contains focus area<br/>+ Baguio context?}
    
    FU --> |Yes| FOLLOWUP[Intent: followup<br/>-> RAG on cache]
    FU --> |No| SIMPLE[Intent: simple<br/>-> 1 Agent]
    
    FOCUS --> |Yes| ANALYZE
    FOCUS --> |No| SIMPLE

    style ANALYZE fill:#f3e5f5
    style SIMPLE fill:#e0f7fa
    style FOLLOWUP fill:#f1f8e9
```

### Intent Keywords

| Intent | Keywords | Agent Path |
|--------|----------|------------|
| **analyze** | "analyze", "sentiment", "public opinion", "civic sentiment" | 12 Agents |
| **followup** | "tell me more", "explain", "why", "sources" | RAG on cache |
| **simple** | Default (no analysis keywords) | 1 Agent (ChatAgent) |

---

## Streaming Response Format (12 Agents)

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Server->>Client: {type: "progress", stage: "start", progress: 0.0}
    Note right of Server: Starting 12-agent pipeline
    Server->>Client: {type: "progress", stage: "query_orchestrator", progress: 0.1}
    Note right of Server: QueryOrchestratorAgent
    Server->>Client: {type: "progress", stage: "retrieval", progress: 0.25}
    Note right of Server: RetrievalAgent
    Server->>Client: {type: "progress", stage: "recall", progress: 0.35}
    Note right of Server: ContextAugmentationAgent.retrieve_knowledge()
    Server->>Client: {type: "progress", stage: "analyze", progress: 0.55}
    Note right of Server: SentimentAgent + CredibilityAgent + ThemeRouterAgent
    Server->>Client: {type: "progress", stage: "memory", progress: 0.70}
    Note right of Server: ContextAugmentationAgent.consolidate_memory()
    Server->>Client: {type: "progress", stage: "themes", progress: 0.9}
    Note right of Server: 6 Theme Agents
    Server->>Client: {type: "result", stage: "complete", progress: 1.0, data: {...}}
    Note right of Server: CoordinatorAgent
```

---

## Component Architecture (12 Agents)

```mermaid
graph LR
    subgraph External["External Services"]
        LS[LangSearch API]
        GEMINI[Google Gemini API]
        APIFY[Apify/Facebook]
        PRAW[Reddit/PRAW]
        TAVILY[Tavily API]
        GFACT[Google Fact Check]
    end

    subgraph Models["ML Models"]
        ROBERTA[RoBERTa<br/>Sentiment]
        MINILM[MiniLM-L6<br/>Embeddings]
    end

    subgraph ChatAnalyze["Chat Analyzer (12 Agents)"]
        CA_QO[QueryOrchestratorAgent]
        CA_RA[RetrievalAgent]
        CA_CTX[ContextAugmentationAgent]
        CA_SA[SentimentAgent]
        CA_CR[CredibilityAgent]
        CA_TR[ThemeRouterAgent]
        CA_T1[InfrastructureAgent]
        CA_T2[HealthAgent]
        CA_T3[SafetyAgent]
        CA_T4[TourismAgent]
        CA_T5[EconomyAgent]
        CA_T6[EnvironmentAgent]
        CA_CO[CoordinatorAgent]
    end

    subgraph AIAssistant["AI Assistant (1 Agent)"]
        AA_AG[ChatAgent]
    end

    LS --> CA_RA & AA_AG
    APIFY --> CA_RA
    PRAW --> CA_RA
    GEMINI --> CA_QO & CA_SA & CA_CR & CA_T1 & CA_T2 & CA_T3 & CA_T4 & CA_T5 & CA_T6 & CA_CO & AA_AG
    TAVILY --> CA_CR
    GFACT --> CA_CR
    ROBERTA --> CA_SA
    MINILM --> CA_CTX

    CA_QO --> CA_RA --> CA_CTX
    CA_CTX --> CA_SA & CA_CR & CA_TR
    CA_SA & CA_CR & CA_TR --> CA_CTX
    CA_CTX --> CA_T1 & CA_T2 & CA_T3 & CA_T4 & CA_T5 & CA_T6
    CA_T1 & CA_T2 & CA_T3 & CA_T4 & CA_T5 & CA_T6 --> CA_CO
```

---

## Agent File Structure

```
backend/
├── app/
│   ├── routers/
│   │   ├── chat_analyze.py      # /chat/analyze - 12 Agents (Streaming SSE)
│   │   └── chat.py              # /chat/ - 1 Agent (Sync JSON)
│   ├── services/
│   │   ├── agents/
│   │   │   ├── chat_agent.py           # ChatAgent (AI Assistant)
│   │   │   ├── query_orchestrator.py   # QueryOrchestratorAgent
│   │   │   ├── sentiment_agent.py      # SentimentAgent
│   │   │   ├── credibility_agent.py    # CredibilityAgent
│   │   │   ├── context_agent.py        # ContextAugmentationAgent
│   │   │   ├── theme_agent.py          # 6 Theme Agents
│   │   │   └── gemini.py               # ReAct agent utilities
│   │   ├── insights/
│   │   │   ├── graph.py         # 7-Node LangGraph workflow
│   │   │   ├── agents.py        # RetrievalAgent, ThemeRouterAgent
│   │   │   └── agent_tools.py   # Tool implementations
│   │   ├── rag/
│   │   │   ├── chunker.py       # Semantic chunking
│   │   │   ├── embeddings.py    # MiniLM service
│   │   │   └── vector_store.py  # Qdrant client
│   │   ├── ingestion/
│   │   │   ├── reddit.py        # PRAW integration
│   │   │   └── facebook.py      # Apify integration
│   │   └── langsearch.py        # Web search + FB enrichment
```

---

## Performance Comparison

| Metric | Chat Analyzer (12 Agents) | AI Assistant (1 Agent) |
|--------|---------------------------|------------------------|
| Agent Count | **12** | **1** |
| Avg Latency | 15-30s | 2-5s |
| Documents Processed | Up to 100 | Up to 5 |
| LLM Calls | 8-12 | 1-2 |
| Streaming | Yes (SSE) | No |
| Memory | Persistent (Qdrant) | None |
| Sentiment Scoring | Yes (ensemble) | No |
| Credibility Scoring | Yes (5-signal) | No |
| Structured Output | Yes | Text + Sources |
| Parallelization | Nodes 4 + 6 | None |

---

## Session Management

```mermaid
flowchart LR
    subgraph Session["Session Cache"]
        S1[session_id]
        S2[SnapshotResponse]
        S3[focus_areas]
        S4[timestamp]
    end

    Analyze[Analyze Request<br/>12 Agents] --> |"Cache result"| Session
    Followup[Follow-up Request] --> |"Read cache"| Session
    Session --> |"RAG query"| Response[Contextual Answer]
```

Chat Analyzer maintains in-memory session cache:
- Stores analysis results by `session_id`
- Enables follow-up questions without re-running 12-agent pipeline
- Uses Gemini RAG on cached `SnapshotResponse`
