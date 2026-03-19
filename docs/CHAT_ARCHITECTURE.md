# Chat Systems Architecture

> **Thesis Title (Option 1):** 7-Node Agentic Graphs: Multi-Signal Fusion for Verified Context-Aware Public Opinion Synthesis
>
> **Thesis Title (Option 2):** Hinaing: A Neuro-Symbolic Multi-Agent Framework for Epistemic Truth Discovery in Civic Social Listening
>
> **Thesis Title (Option 3):** Hinaing: A Context-Engineered Self-Learning Multi-Agent Agentic AI System with Ensemble Sentiment and 5-Signal Credibility for Public Opinion Analysis in Baguio City
>
> **Thesis Title (Unified):** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

> **Context Engineering**: The entire 7-node architecture is a form of context engineering - we design the pipeline structure, agent specializations, emerging concerns, theme definitions, and credibility signals to inject domain-specific knowledge into the system.

> **Thesis Title:** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

> **Context Engineering**: The entire 7-node architecture is a form of context engineering - we design the pipeline structure, agent specializations, emerging concerns, theme definitions, and credibility signals to inject domain-specific knowledge into the system.

## Overview

Hinaing provides two distinct chat interfaces with different agent architectures:

| Feature | Chat Analyzer (13 Agents) | AI Assistant (1 Agent) |
|---------|---------------------------|------------------------|
| **Purpose** | Deep sentiment analysis | Quick Q&A |
| **Endpoint** | `POST /chat/analyze/start` | `POST /chat/` |
| **Response** | Background Task + Polling | Sync JSON |
| **Agent Count** | **13** (7 core + 6 theme) | **1** (ChatAgent) |
| **Pipeline** | 7-node multi-agent | Single LLM + tool call |
| **Latency** | 15-30 seconds | 2-5 seconds |
| **Memory** | Persistent (Qdrant) | None |

## Mobile-Resilient Architecture

The Chat Analyzer uses a **Background Task + Polling** pattern that survives:
- Mobile alt-tab / screen off
- Network interruptions
- Browser tab suspension

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant TM as TaskManager
    participant Pipeline as 13-Agent Pipeline

    Client->>API: POST /chat/analyze/start
    API->>TM: create_task() → task_id
    API->>Pipeline: submit_task(task_id, pipeline)
    API-->>Client: { task_id, session_id }
    
    Note over Client: User can alt-tab, screen off
    
    loop Poll every 1.5s (max 60 polls)
        Client->>API: GET /chat/analyze/status/{task_id}
        API->>TM: get_task(task_id)
        TM-->>API: { status, progress, stage, result? }
        API-->>Client: TaskState
        
        alt status == "completed"
            Note over Client: Display result
        else status == "running"
            Note over Client: Update progress UI
        else status == "failed"
            Note over Client: Show error
        end
    end
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat/analyze/start` | POST | Start background analysis, returns `task_id` |
| `/chat/analyze/status/{task_id}` | GET | Poll for progress and result |
| `/chat/analyze` | POST | Legacy SSE streaming (deprecated) |
| `/chat/analyze/sync` | POST | Synchronous (blocking) analysis |

## Agent Summary

### Chat Analyzer Agents (13 Total)

| Category | Count | Agents |
|----------|-------|--------|
| **Core Pipeline** | 7 | QueryOrchestratorAgent, RetrievalAgent, SentimentAgent, CredibilityAgent, ContextAugmentationAgent, ThemeRouterAgent, CoordinatorAgent |
| **Theme Sub-Agents** | 6 | InfrastructureAgent, HealthAgent, SafetyAgent, TourismAgent, EconomyAgent, EnvironmentAgent |

### AI Assistant Agent (1 Total)

| Agent | Function |
|-------|----------|
| **ChatAgent** | Single ReAct agent with LangSearch tool for quick Q&A |

---

## Chat Analyzer System Flow (13 Agents)

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

        subgraph Pipeline["7-Node Multi-Agent Pipeline (13 Agents)"]
            subgraph Node1["Node 1: QueryOrchestratorAgent (10%) - Context Engineering"]
                QO[QueryOrchestratorAgent]
                QO --> |FOCUS_CONCERN_KEYWORDS + get_temporal_context| QP[QueryPlan<br/>6 diverse queries]
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
                EM1[BGE-small-en-v1.5<br/>Query Embedding]
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
                EM[BGE Embeddings]
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
            NR[CoordinatorAgent<br/>Gemini 2.5 Flash-Lite]
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

## Chat Analyzer Sequence Diagram (13 Agents)

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
        
        Note over QO: Node 1: QueryOrchestratorAgent (Context Engineering)
        API->>QO: parse_user_intent(message)
        QO->>QO: ReAct: get_domain_context tool (Dynamic Context Engineering)
        QO->>QO: ReAct: get_temporal_context tool (dynamic context engineering)
        QO->>QO: ReAct: validate_query_diversity tool
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
        CTX->>CTX: Embed query with BGE-small-en-v1.5
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
        CO->>CO: CoordinatorAgent.run() (Gemini 2.5 Flash-Lite)
        
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

**Important**: The Chat Agent uses **Groq** (not Gemini) as the primary LLM provider for fast inference.

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
            GF[Groq (llama-3.3-70b)]
            ID[Intent Detection]
            CA --> GF --> ID
        end

        subgraph Search["LangSearch Client"]
            LS[LangSearch API<br/>30-day window]
            LS --> |web docs| CA
        end

        ID --> |greeting/identity| Direct[Direct Response]
        ID --> |civic question| Search
        Search --> |grounded prompt| GF
        GF --> |final_response| Response[JSON Response + Sources]
    end

    Request[User Message + History] --> SingleAgent
    Response --> Frontend

    style SingleAgent fill:#e1f5fe
    style Search fill:#fff3e0
    style Direct fill:#f1f8e9
```

### Chat Agent Specifications

| Aspect | Implementation |
|--------|----------------|
| **LLM Provider** | **Groq** (`groq/compound` - llama-3.3-70b) |
| **Retrieval** | LangSearch web search ONLY (30-day window) |
| **Memory** | Conversation buffer (last 6 messages) - **NO Qdrant** |
| **Intent Detection** | Keyword-based (greeting, identity, civic, sentiment) |
| **Latency** | 1-2 seconds |
| **Verification** | None (LLM grounding only) |
| **Sentiment Analysis** | None |

### Dead Code (Not Used)

The following are defined but **NEVER called** in production:

```python
# Imported but never used
from ..agents.context_agent import ContextAugmentationAgent  # ← Never called

# Defined but never called
context_agent = ContextAugmentationAgent()  # ← Dead code
def search_sentiment_data(...)  # ← Dead code
tools_map = {...}  # ← Dead code
def _is_sentiment_query(...)  # ← Dead code
```

**Actual retrieval flow**:
```python
# Line 209: ONLY retrieval call
search_client = LangSearchClient()
web_docs = await search_client.search(query=fresh_query, time_window="30d", limit=20)
```

---

## Agent Comparison: Chat Analyzer vs AI Assistant

| Aspect | Chat Analyzer (13 Agents) | AI Assistant (1 Agent) |
|--------|---------------------------|------------------------|
| **QueryOrchestratorAgent** | ✅ ReAct with 3 tools (context engineering) | ❌ None |
| **RetrievalAgent** | ✅ LangSearch + FB + Reddit | ⚠️ LangSearch + Memory |
| **ContextAugmentationAgent** | ✅ Memory recall + consolidation | ⚠️ Memory recall only (via tool) |
| **SentimentAgent** | ✅ RoBERTa + Gemini ensemble | ❌ None |
| **CredibilityAgent** | ✅ 5-signal framework | ❌ None |
| **ThemeRouterAgent** | ✅ 6 theme buckets | ❌ None |
| **6 Theme Agents** | ✅ Parallel Gemini | ❌ None |
| **ChatAgent** | ❌ Not used | ✅ Single agent |
| **Memory** | ✅ Qdrant persistent | ✅ Read-only RAG |
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

## Streaming Response Format (13 Agents)

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Server->>Client: {type: "progress", stage: "start", progress: 0.0}
    Note right of Server: Starting 13-agent pipeline
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

## Component Architecture (13 Agents)

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
        BGE[BGE-small<br/>Embeddings]
    end

    subgraph ChatAnalyze["Chat Analyzer (12 Agents)"]
        CA_QO[QueryOrchestratorAgent]
        CA_RA[RetrievalAgent]
        CA_CTX[ContextAugmentationAgent]
        CA_SA[SentimentAgent]
        CA_CR[CredibilityAgent]
        CA_TR[ThemeRouterAgent]
        CA_T1[ThemeAgent: Infrastructure]
        CA_T2[ThemeAgent: Health]
        CA_T3[ThemeAgent: Safety]
        CA_T4[ThemeAgent: Tourism]
        CA_T5[ThemeAgent: Economy]
        CA_T6[ThemeAgent: Environment]
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
    BGE --> CA_CTX

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
│   │   │   ├── embeddings.py    # BGE service
│   │   │   └── vector_store.py  # Qdrant client
│   │   ├── ingestion/
│   │   │   ├── reddit.py        # PRAW integration
│   │   │   └── facebook.py      # Apify integration
│   │   └── langsearch.py        # Web search + FB enrichment
```

---

## Performance Comparison

| Metric | Chat Analyzer (13 Agents) | AI Assistant (1 Agent) |
|--------|---------------------------|------------------------|
| Agent Count | **13** | **1** |
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
- Enables follow-up questions without re-running 13-agent pipeline
- Uses Gemini RAG on cached `SnapshotResponse`

