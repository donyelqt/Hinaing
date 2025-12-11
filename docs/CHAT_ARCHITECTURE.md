# Chat Systems Architecture

## Overview

Hinaing provides two distinct chat interfaces with different architectural patterns:

| Feature | Chat Analyzer | AI Assistant |
|---------|---------------|--------------|
| **Purpose** | Deep sentiment analysis | Quick Q&A |
| **Endpoint** | `POST /chat/analyze` | `POST /chat/` |
| **Response** | Streaming (SSE) | Sync JSON |
| **Pipeline** | 6-agent multi-agent system | Single LLM + tool call |
| **Latency** | 15-45 seconds | 2-5 seconds |

---

## Chat Analyzer System Flow (Mermaid)

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

        subgraph Pipeline["6-Agent Pipeline (Streaming)"]
            subgraph Stage1["1. Query Orchestrator (10%)"]
                QO[Query Orchestrator Agent]
                QO --> |KEYWORD_CLUSTERS| QP[QueryPlan]
            end

            subgraph Stage2["2. Retrieval Agent (25%)"]
                LS[LangSearch + FB Pages]
                RD[Reddit r/baguio]
                LS & RD --> Docs[WebDocuments]
            end

            subgraph Stage3["3. Sentiment Agent (45%)"]
                RB[RoBERTa 40%]
                GM[Gemini 60%]
                RB & GM --> WV[Weighted Voting]
            end

            subgraph Stage4["4. Credibility Agent (60%)"]
                DT[Domain Trust Tier]
                FC[Fact Check API]
                CQ[Content Quality]
                DT & FC & CQ --> CS[Credibility Score]
            end

            subgraph Stage5["5. Context Agent (75%)"]
                CH[Semantic Chunker]
                EM[MiniLM-L6 Embeddings]
                VS[Vector Search]
                CH --> EM --> VS
            end

            subgraph Stage6["6. Theme Agents (90%)"]
                T1[Infrastructure]
                T2[Health]
                T3[Safety]
                T4[Tourism]
                T5[Economy]
                T6[Environment]
            end

            Stage1 --> Stage2 --> Stage3 --> Stage4 --> Stage5 --> Stage6
        end

        subgraph Simple["Simple Q&A Path"]
            CA[Chat Agent]
            LSS[LangSearch]
            GF[Gemini Flash]
            CA --> LSS --> GF
        end

        subgraph Followup["Follow-up Path"]
            Cache[Session Cache]
            RAG[RAG on Cached Results]
            Cache --> RAG
        end

        subgraph Output["Response Builder"]
            NR[Narrative Generator<br/>Gemini 2.5 Pro]
            SR[SnapshotResponse]
            NR --> SR
        end

        Pipeline --> Output
    end

    Request[User Message] --> IntentRouter
    SR --> |SSE Stream| Frontend
    Simple --> |JSON| Frontend
    Followup --> |JSON| Frontend

    style Stage1 fill:#e1f5fe
    style Stage2 fill:#fff3e0
    style Stage3 fill:#f3e5f5
    style Stage4 fill:#e8f5e9
    style Stage5 fill:#fce4ec
    style Stage6 fill:#fff8e1
    style Simple fill:#e0f7fa
    style Followup fill:#f1f8e9
```

---

## Chat Analyzer Sequence Diagram (Mermaid)

```mermaid
sequenceDiagram
    participant Client
    participant API as /chat/analyze
    participant ID as Intent Detector
    participant QO as Query Orchestrator
    participant RA as Retrieval Agent
    participant SA as Sentiment Agent
    participant CA as Credibility Agent
    participant CTX as Context Agent
    participant TA as Theme Agents
    participant GC as Gemini Narrative

    Client->>API: POST {message, session_id, history}
    API->>ID: detect_intent(message, history)
    
    alt Intent = "analyze"
        ID-->>API: "analyze"
        
        API-->>Client: SSE: {stage: "start", progress: 0.0}
        
        API->>QO: parse_user_intent(message)
        QO->>QO: Extract focus_areas
        QO->>QO: Generate KEYWORD_CLUSTERS queries
        API-->>Client: SSE: {stage: "query_orchestrator", progress: 0.1}
        
        API->>RA: fetch_documents(QueryPlan)
        par Parallel Retrieval
            RA->>RA: LangSearch + FB Pages
            RA->>RA: Reddit Search
        end
        RA->>RA: Diversity Merge (round-robin)
        API-->>Client: SSE: {stage: "retrieval", progress: 0.25}
        
        API->>SA: label_sentiment(docs)
        par Ensemble
            SA->>SA: RoBERTa (40%)
            SA->>SA: Gemini (60%)
        end
        API-->>Client: SSE: {stage: "sentiment", progress: 0.45}
        
        API->>CA: analyze_enriched(docs)
        par Parallel
            CA->>CA: Credibility Scoring
            CA->>CA: Theme Routing
        end
        API-->>Client: SSE: {stage: "credibility", progress: 0.6}
        
        API->>CTX: augment_context(theme_docs)
        CTX->>CTX: Chunk → Embed → Vector Search
        API-->>Client: SSE: {stage: "context", progress: 0.75}
        
        API->>TA: theme_agents(augmented)
        par 6 Parallel Agents
            TA->>TA: Infrastructure
            TA->>TA: Health & Safety
            TA->>TA: Tourism & Economy
            TA->>TA: Environment
        end
        API-->>Client: SSE: {stage: "themes", progress: 0.9}
        
        API->>GC: build_snapshot()
        GC->>GC: Narrative (3-5 sentences)
        GC->>GC: Insights (up to 5)
        
        API-->>Client: SSE: {type: "result", data: AnalysisData}
        
    else Intent = "simple"
        ID-->>API: "simple"
        API->>API: run_chat_agent(message)
        API-->>Client: JSON: {message, sources}
        
    else Intent = "followup"
        ID-->>API: "followup"
        API->>API: RAG on _session_cache
        API-->>Client: JSON: {message}
    end
```

---

## AI Assistant Architecture (Mermaid)

```mermaid
flowchart TB
    subgraph Frontend["Frontend (Next.js 15)"]
        ChatUI[Chat Page]
        MsgBubble[Message Bubbles]
        SourceBadges[Source Badges]
    end

    subgraph Backend["Backend (FastAPI)"]
        subgraph ChatAgent["Chat Agent"]
            GF[Gemini 2.0 Flash]
            FC[Function Calling]
            GF --> FC
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

    Request[User Message + History] --> ChatAgent
    Response --> Frontend

    style ChatAgent fill:#e1f5fe
    style Search fill:#fff3e0
```

---

## AI Assistant Sequence Diagram (Mermaid)

```mermaid
sequenceDiagram
    participant Client
    participant API as /chat/
    participant Agent as Gemini Flash Agent
    participant Tool as search_civic_data
    participant LS as LangSearch

    Client->>API: POST {message, history, jurisdiction}
    API->>Agent: start_chat(history)
    Agent->>Agent: Analyze message
    
    alt Needs Search
        Agent->>Tool: function_call(query)
        Tool->>LS: search(query + "Baguio City")
        LS-->>Tool: List[WebDocument]
        Tool->>Tool: Format results
        Tool-->>Agent: Formatted context
        Agent->>Agent: Generate response with context
    else Direct Answer
        Agent->>Agent: Generate response
    end
    
    Agent-->>API: {response, sources}
    API-->>Client: JSON {response, sources[]}
```

---

## Intent Detection Logic

```mermaid
flowchart TD
    MSG[User Message] --> KW{Contains analyze keywords?}
    
    KW --> |Yes| ANALYZE[Intent: analyze]
    KW --> |No| HIST{Has recent analysis<br/>in history?}
    
    HIST --> |Yes| FU{Contains followup keywords?}
    HIST --> |No| FOCUS{Contains focus area<br/>+ Baguio context?}
    
    FU --> |Yes| FOLLOWUP[Intent: followup]
    FU --> |No| SIMPLE[Intent: simple]
    
    FOCUS --> |Yes| ANALYZE
    FOCUS --> |No| SIMPLE

    style ANALYZE fill:#f3e5f5
    style SIMPLE fill:#e0f7fa
    style FOLLOWUP fill:#f1f8e9
```

### Intent Keywords

| Intent | Keywords |
|--------|----------|
| **analyze** | "analyze", "sentiment", "public opinion", "how do citizens feel", "civic sentiment", "generate insight" |
| **followup** | "tell me more", "explain", "why", "what about", "sources", "evidence", "based on the analysis" |
| **simple** | Default (no analysis keywords detected) |

---

## Data Sources Integration

```mermaid
flowchart LR
    subgraph Sources["Data Sources"]
        LS[LangSearch Web API]
        FB[Facebook Pages]
        RD[Reddit]
    end

    subgraph FBPages["Baguio Facebook Pages"]
        PIO[BaguioCityPIO]
        GOV[BaguioCityGovernment]
        LAB[baboratoryph]
    end

    subgraph Subreddits["Target Subreddits"]
        R1[r/baguio]
        R2[r/Philippines]
        R3[r/CasualPH]
    end

    LS --> |"query OR site:facebook.com/..."| FBPages
    RD --> Subreddits

    FBPages --> Docs[WebDocuments]
    Subreddits --> Docs
    LS --> Docs

    style Sources fill:#e1f5fe
    style FBPages fill:#e8f5e9
    style Subreddits fill:#fff3e0
```

---

## Streaming Response Format

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Server->>Client: {type: "progress", stage: "start", progress: 0.0}
    Server->>Client: {type: "progress", stage: "query_orchestrator", progress: 0.1}
    Server->>Client: {type: "progress", stage: "retrieval", progress: 0.25}
    Server->>Client: {type: "progress", stage: "sentiment", progress: 0.45}
    Server->>Client: {type: "progress", stage: "credibility", progress: 0.6}
    Server->>Client: {type: "progress", stage: "context", progress: 0.75}
    Server->>Client: {type: "progress", stage: "themes", progress: 0.9}
    Server->>Client: {type: "result", stage: "complete", progress: 1.0, data: {...}}
```

---

## Component Architecture

```mermaid
graph LR
    subgraph External["External Services"]
        LS[LangSearch API]
        GEMINI[Google Gemini API]
        APIFY[Apify/Facebook]
    end

    subgraph Models["ML Models"]
        ROBERTA[RoBERTa<br/>Sentiment]
        MINILM[MiniLM-L6<br/>Embeddings]
    end

    subgraph ChatAnalyze["Chat Analyzer"]
        CA_ID[Intent Detector]
        CA_QO[Query Orchestrator]
        CA_RA[Retrieval Agent]
        CA_SA[Sentiment Agent]
        CA_CR[Credibility Agent]
        CA_CTX[Context Agent]
        CA_TA[Theme Agents]
        CA_NR[Narrative Generator]
    end

    subgraph AIAssistant["AI Assistant"]
        AA_AG[Chat Agent]
        AA_FC[Function Calling]
    end

    LS --> CA_RA & AA_FC
    APIFY --> CA_RA
    GEMINI --> CA_QO & CA_SA & CA_TA & CA_NR & AA_AG
    ROBERTA --> CA_SA
    MINILM --> CA_CTX

    CA_ID --> CA_QO --> CA_RA --> CA_SA --> CA_CR --> CA_CTX --> CA_TA --> CA_NR
```

---

## File Structure

```
backend/
├── app/
│   ├── routers/
│   │   ├── chat_analyze.py      # /chat/analyze - Streaming SSE
│   │   └── chat.py              # /chat/ - Sync JSON
│   ├── services/
│   │   ├── agents/
│   │   │   ├── chat_agent.py    # AI Assistant (Gemini + tools)
│   │   │   ├── query_orchestrator.py
│   │   │   ├── sentiment_agent.py
│   │   │   ├── credibility_agent.py
│   │   │   ├── context_agent.py
│   │   │   ├── theme_agent.py
│   │   │   └── gemini.py        # ReAct agent
│   │   ├── insights/
│   │   │   ├── graph.py         # LangGraph workflow
│   │   │   ├── agents.py        # Agent orchestrators
│   │   │   └── agent_tools.py   # Tool implementations
│   │   ├── nlp/
│   │   │   └── gemini.py        # Gemini client
│   │   └── langsearch.py        # Web search + FB enrichment

frontend/
├── src/features/chat/
│   ├── chat-analyze-page.tsx    # Chat Analyzer UI
│   │   ├── ProgressIndicator    # 6-stage progress
│   │   ├── AnalysisResultCard   # Rich results display
│   │   └── WelcomeScreen        # Suggestions
│   └── chat-page.tsx            # AI Assistant UI
│       ├── MessageBubble        # With source badges
│       └── WelcomeScreen        # Quick prompts
```

---

## Performance Comparison

| Metric | Chat Analyzer | AI Assistant |
|--------|---------------|--------------|
| Avg Latency | 20-40s | 2-5s |
| Documents Processed | Up to 50 | Up to 5 |
| LLM Calls | 8-12 | 1-2 |
| Streaming | Yes (SSE) | No |
| Session Cache | Yes | No |
| Sentiment Scoring | Yes (per-doc) | No |
| Credibility Scoring | Yes (5-signal) | No |
| Structured Output | Yes | Text + Sources |

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

    Analyze[Analyze Request] --> |"Cache result"| Session
    Followup[Follow-up Request] --> |"Read cache"| Session
    Session --> |"RAG query"| Response[Contextual Answer]
```

Chat Analyzer maintains in-memory session cache:
- Stores analysis results by `session_id`
- Enables follow-up questions without re-running pipeline
- Uses Gemini RAG on cached `SnapshotResponse`
