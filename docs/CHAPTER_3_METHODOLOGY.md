# Chapter 3: Methodology

This chapter presents the procedures on how this study obtained data from various sources. This phase proceeds with the research design methodology, Software Development Methodology, Scope and Delimitation (Geographical and Technical), Data Gathering Techniques, Sources of Data and Software Development Tools.

## Research Design Methodology

This research adopts the **Design Science Research (DSR)** paradigm. Design Science Research is a research paradigm focused on creating innovative artifacts to solve practical problems while maintaining scientific rigor. The method is characterized by its dual strength on balancing research relevance and rigor, with Information Systems researchers largely adopting and accepting it (Akoka et al., 2023). It is applicable to the study due to its aim to generate innovative solutions to real-world problems (Tuunanen et al., 2024). It is a popular paradigm in engineering and other disciplines where understanding the problem and creating a subsequent solution through artefact development (Weber et al., 2023; Eybers et al., 2023). The core of this approach is to design, build, and evaluate a novel multi-agent AI system for public opinion analysis and generate a contribution to the knowledge base for artificial intelligence in governance.

## Software Development Methodology

The project adopted the **Spiral Model** for its software development lifecycle. This iterative methodology was selected as it is exceptionally well-suited for complex, experimental research projects where requirements evolve, and risks need to be managed. It is a modification from the combination of the waterfall model and prototyping model with an emphasis on evaluation carried out systemically. It is more focused on carrying risk analysis from each stage as sentiment analysis requires continuous refinement of classification algorithms and feature extraction methods. The Spiral Model's iterative nature allows developers to integrate additions by determining accuracy based on requirements (Sari et al., 2022). Each development cycle, or "spiral," consisted of four key phases: 1) identifying objectives, 2) analyzing risks through experimentation and prototyping, 3) developing the system components, and 4) evaluating the results to plan the next iteration.

During the development phase of each spiral, principles from **Agent-Oriented Software Engineering (AOSE)** were applied to design, build, and test the specialized agents that form the core of the public opinion analysis system. The implementation uses dataclass workers to realize these concepts, where each worker is an autonomous agent with distinct roles, responsibilities, and capabilities. This process provides a method for complex system development using agent-based modelling, which effectively supports public opinion sentiment analysis projects through goal-oriented and autonomous agent architectures. It addresses ontological gaps between systems and their environments using organization concepts as development fundamentals (Wautelet et al., 2021). Agent-oriented software engineering enables autonomous agents to mine, classify, and report sentiment data while maintaining human oversight, bridging the gap between complex analytical requirements and stakeholder expectations on sentiment analysis.

### 7-Node Multi-Agent Architecture

The system implements a **7-node directed acyclic graph (DAG)** using LangGraph, where each node represents a distinct processing stage with specialized autonomous agents:

| Node | Agent(s) | Function | Parallelism |
|------|----------|----------|-------------|
| 1 | QueryOrchestratorAgent | ReAct reasoning with KEYWORD_CLUSTERS for 6 diverse queries | Sequential |
| 2 | RetrievalAgent | LangSearch + Facebook + Reddit ingestion | Sequential |
| 3 | ContextAugmentationAgent | Qdrant cosine similarity search for memory recall | Sequential |
| 4 | SentimentAgent + CredibilityAgent + ThemeRouterAgent | Parallel analysis (asyncio.gather) | **Parallel (3 agents)** |
| 5 | ContextAugmentationAgent | Consolidates memory back to Qdrant | Sequential |
| 6 | 6 Theme Sub-Agents | Infrastructure, Health, Safety, Tourism, Economy, Environment | **Parallel (up to 6)** |
| 7 | CoordinatorAgent | Final narrative synthesis | Sequential |

**Total: 18 Autonomous Agents** (7 Core + 5 Credibility Sub-Agents + 6 Theme Sub-Agents)

### Agent Categories

| Category | Count | Agents |
|----------|-------|--------|
| Core Pipeline Agents | 7 | QueryOrchestratorAgent, RetrievalAgent, SentimentAgent, CredibilityAgent, ContextAugmentationAgent, ThemeRouterAgent, CoordinatorAgent |
| Credibility Sub-Agents | 5 | DomainTrustAgent, CrossReferenceAgent, FactCheckAgent, LLMAnalysisAgent, TavilyAgent (parallel execution) |
| Theme Sub-Agents | 6 | InfrastructureAgent, HealthAgent, SafetyAgent, TourismAgent, EconomyAgent, EnvironmentAgent (conditionally spawned) |

---

## Scope and Delimitation

### Geographic Scope

The geographic scope is set to **Baguio City, Philippines** through:
- Location-specific queries (e.g., "Baguio", "Session Road", "Burnham Park", "Kennon Road")
- Curated keyword clusters per theme (KEYWORD_CLUSTERS dictionary)
- Location filtering using BAGUIO_LOCATION_TERMS set
- Time-based filtering for recency (6h, 24h, 3d, 7d windows)

Implementing the following data gathering parameters ensures the analysis remains geographically accurate, topically relevant, and temporally valid. By narrowing the focus to a specific timeframe, noise that can skew results are eliminated.

Baguio City has a unique socio-economic and environmental landscape. Without location-specific queries, the sentiment will be diluted with general Philippine data. Location-specific queries ensure that the opinions being analyzed belong to residents or visitors physically present in the city. Approximately 25% of geotagged content can be non-local, with specific queries such as "Baguio", "Session Road" or "Burnham Park" helps filter out irrelevant global noise (Hecht, 2016).

Keyword clustering ensures that a negative sentiment on a topic is not grouped with an unrelated topic. As an example, words such as "traffic", "trapick" and "Session Road gridlock" are grouped into a "Mobility" cluster, allowing sentiment to measure against specific city issues rather than general moods (Goodey, n.d.)

The location-filtering method verifies that the data-point is originating from the actual coordinates of Baguio City. This allows for other functionalities such as heat-mapping, which can be expanded to specific statements concentrated in various communities. The location filtering parameter catches people talking about the city and location-filtering, with the GPS metadata, gathers people experiencing Baguio City.

With the possible staleness and volatility of public opinion, sentiment analysis may suffer from concept drifts where old data no longer reflects the current reality. With the time-based filtering, this will allow sentiment spikes before, during and after major city events (Rozi, 2018; Cao, 2025).

### Technical Scope

While the system is designed for high-fidelity data retrieval and synthesis, multiple technical and data handling scopes are encountered:

1. **Ensemble Methodology**: The current iteration uses a heuristic 40/60 ensemble weight distribution for data processing (RoBERTa 40%, Gemini 60%). While functional, formal optimization against a dedicated validation set remains outside the scope of the study.

2. **Infrastructure and Scalability**: To ensure production-grade persistence and scalability, the study is delimited to the use of Qdrant Cloud for vector storage. The throughput of the analysis is subject to the operational limits of integrated APIs:
   - Gemini: 15 requests per minute
   - Tavily: 1,000 requests per month

3. **Language Support**: The system is primarily optimized for English-language processing. While support for "TagLish" and "Filipino" is implicitly provided through the RoBERTa model, deep semantic nuance in local dialects is not the primary objective.

4. **Credibility Ground Truth**: Due to the absence of a standardized, labeled misinformation dataset specifically for Philippine civic content, the study does not claim to provide absolute "ground truth" for credibility. Rather, the study focuses on trend identification and sentiment patterns within the gathered data.

---

## Data Gathering Techniques

The research employs a **multi-modal data acquisition strategy** to ensure a comprehensive capture of public sentiment and factual context. Data is retrieved through a combination of automated API integrations, web scraping, and vector-based retrieval from internal repositories.

### Data Acquisition Methods

| Method | Source | Description |
|--------|--------|-------------|
| Semantic Search + Reranking | LangSearch API | Performs semantic search across news outlets, blogs, and forums with intelligent reranking |
| Web Scraping | Apify | Cloud platform for Facebook data extraction from public pages |
| Social API | PRAW | Python Reddit API Wrapper for community data collection |
| Vector Retrieval | Qdrant Cloud | Similarity search from previously analyzed documents |

---

## Sources of Data

The study identifies **four primary streams** of information, categorized by their digital origin:

1. **LangSearch API**: The system performs semantic search across news outlets, blogs, and forums, providing a high-level overview of formal public discourse. The semantic reranking ensures relevance-weighted results.

2. **Facebook (via Apify)**: The system captures actual public opinion from social media. The collected Facebook data focuses on public government pages, such as the Baguio Public Information Office, to track official announcements and citizen sentiment.

3. **Reddit (via PRAW)**: The data targets hyper-local communities, specifically r/baguio, r/Philippines and r/CasualPH to gather nuanced and long-form community discussions.

4. **Qdrant Vector Store**: A Retrieval-Augmented Generation component uses a Qdrant vector store to access previously analyzed documents, ensuring that the search is grounded in historical context and existing internal data. This enables the **self-learning cyclic RAG** architecture where:
   - Node 3 recalls past learnings BEFORE analysis
   - Node 5 writes new learnings AFTER analysis

---

## Software Development Tools

### Backend

| Category | Technology | Purpose |
|----------|------------|---------|
| Core Development | Python 3.11+ with Poetry | Primary programming language with dependency management |
| Web Framework | FastAPI | High-performance async API development |
| LLM Orchestration | LangChain / LangGraph | Multi-agent workflow orchestration using DAGs |
| Observability | LangSmith | Debugging, testing, and monitoring |
| LLM | Google Gemini (2.5 Flash/Lite) | Primary language model for reasoning tasks |
| Transformer | HuggingFace Transformers (RoBERTa) | Sentiment analysis with twitter-roberta-base-sentiment-latest |
| Vector Database | Qdrant Cloud | High-performance similarity search |
| Embeddings | Sentence Transformers (BGE-large-en-v1.5) | 1024-dimensional semantic embeddings with Hybrid Search support |
| Web Search | LangSearch / Tavily | Real-time fact-checking and semantic retrieval |
| Social APIs | PRAW (Reddit), Apify (Facebook) | Social media data collection |
| Deployment | Google Cloud Run (asia-southeast1) | Serverless container hosting |

### Frontend

| Category | Technology | Purpose |
|----------|------------|---------|
| Framework | Next.js 15 + React 19 | Full-stack React framework with Server Components |
| Language | TypeScript | Type-safe development |
| Styling | Tailwind CSS | Utility-first CSS framework |
| Data Fetching | SWR | Remote data synchronization |
| Icons | Lucide React | Lightweight SVG icon library |

### DevOps

| Category | Technology | Purpose |
|----------|------------|---------|
| Containerization | Docker | Standardized deployment units |
| Backend Hosting | Google Cloud Run | Auto-scaling serverless containers |
| Frontend Hosting | Vercel | Optimized Next.js deployment |
| Version Control | GitHub | Collaborative source management |

---

## System Architecture Summary

The **AgenticHinaing** system implements a **7-node self-learning multi-agent architecture** with 18 autonomous agents:

1. **Query Orchestration** (Node 1): AI-powered query synthesis using ReAct reasoning with temporal awareness
2. **Retrieval** (Node 2): Multi-source parallel fetching from LangSearch, Facebook, Reddit
3. **Memory Recall** (Node 3): **Hybrid Search** (Dense BGE-large 1024D + Sparse BM25) with **Temporal-Aware RRF** from Qdrant vector store
4. **Parallel Analysis** (Node 4): Ensemble sentiment (RoBERTa + Gemini) + 5-signal credibility + theme routing with **Smart Reuse** (81% API cost reduction)
5. **Memory Consolidation** (Node 5): Self-learning write-back to vector store with **Analysis Consolidation**
6. **Theme Analysis** (Node 6): 6 domain-specific theme agents in parallel
7. **Synthesis** (Node 7): Coordinator agent generates final narrative with **Vector-Symbolic Epistemic Entailment** for credibility verification

This architecture demonstrates **context engineering** as a novel contribution—where the pipeline structure itself injects domain knowledge rather than relying solely on prompt engineering.
