# Methodology

This document describes the research methodology for **Hinaing**, a multi-agent AI system with real-time intelligent search and Retrieval-Augmented Generation (RAG) for context-aware public opinion analysis in Baguio City, Philippines.

---

## Research Design

### System Development Methodology

The system follows an iterative, agent-based development approach combining:

1. **Multi-Agent Architecture Design** — Decomposing the sentiment analysis pipeline into 13 specialized, cooperating agents organized in a 7-node cognitive architecture
2. **Ensemble Learning** — Combining transformer (RoBERTa) and Large Language Model (Gemini) for robust sentiment classification with weighted voting
3. **Retrieval-Augmented Generation (RAG)** — Grounding insights in real-time retrieved context with a novel cyclic learning loop
4. **Multi-Signal Credibility Framework** — 5-signal ensemble for source quality assessment and misinformation detection

### Data Sources

| Source | Type | Collection Method | Content |
|--------|------|-------------------|---------|
| LangSearch API | Web | Semantic search + reranking | News articles, blogs, forums |
| Facebook | Social Media | Apify scraper integration | Public group posts from Baguio PIO pages |
| Reddit | Social Media | PRAW API (r/baguio, r/Philippines, r/CasualPH) | Community discussions |
| Internal Memory | RAG | Qdrant vector store | Previously analyzed documents |

### Geographic Scope

All analysis is scoped to **Baguio City, Philippines** through:
- Location-specific search queries (e.g., "Baguio", "BGH", "Kennon Road", "Session Road")
- Curated keyword clusters per theme (KEYWORD_CLUSTERS dictionary)
- Location filtering using BAGUIO_LOCATION_TERMS set
- Time-based filtering for recency (6h, 24h, 3d, 7d windows)

---

## 7-Node Multi-Agent Architecture

### Agent Count Summary

| Category | Count | Agents |
|----------|-------|--------|
| Core Pipeline Agents | 7 | QueryOrchestrator, Retrieval, Context, Sentiment, Credibility, ThemeRouter, Coordinator |
| Theme Sub-Agents | 6 | Infrastructure, Health, Safety, Tourism, Economy, Environment |
| **Total** | **13** | 7 core + 6 theme-specific |

### Pipeline Flow

```
SnapshotRequest
       ↓
┌──────────────────────────────────────────────────────────────────┐
│  NODE 1: Query Orchestrator Agent (ReAct)                        │
│  - Generates 6 diverse search queries using KEYWORD_CLUSTERS     │
│  - Model: Gemini 2.5 Flash                                       │
└──────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────┐
│  NODE 2: Retrieval Agent (External)                              │
│  - Parallel batch execution (3 queries per batch)                │
│  - Sources: LangSearch + Facebook + Reddit                       │
│  - Diversity-aware round-robin merging                           │
│  - Max 100 documents                                             │
└──────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────┐
│  NODE 3: Context Agent — Memory Recall (RAG Retrieval)           │
│  - Queries Qdrant vector store per focus area                    │
│  - Cosine similarity search with BGE-small-en-v1.5 embeddings         │
│  - Deduplicates and merges with external documents               │
└──────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────┐
│  NODE 4: Unified Analysis (3 Agents in Parallel)                 │
│  ┌─────────────────┬─────────────────┬─────────────────┐         │
│  │ SentimentAgent  │ CredibilityAgent│ ThemeRouterAgent│         │
│  │ RoBERTa+Gemini  │ 5-Signal        │ 6 Theme Buckets │         │
│  │ Ensemble        │ Framework       │                 │         │
│  └─────────────────┴─────────────────┴─────────────────┘         │
│  Execution: asyncio.gather with 150s timeout                     │
└──────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────┐
│  NODE 5: Context Agent — Memory Consolidation (RAG Ingestion)    │
│  - Chunks enriched documents (400 chars, 100 overlap)            │
│  - Embeds with BGE-small-en-v1.5                                      │
│  - Stores in Qdrant for future recall (LEARNING LOOP)            │
└──────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────┐
│  NODE 6: Theme Agents (6 Agents in Parallel)                     │
│  - ThreadPoolExecutor with max_workers=6                         │
│  - Each agent: Gemini 2.5 Flash for domain-specific insights       │
│  - Themes: Infrastructure, Health, Safety, Tourism, Economy, Env │
└──────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────┐
│  NODE 7: Coordinator Agent (Final Synthesis)                     │
│  - Assembles narrative summary using Gemini 2.5 Flash-Lite              │
│  - Aggregates theme insights                                     │
│  - Computes sentiment breakdown scores                           │
└──────────────────────────────────────────────────────────────────┘
       ↓
SnapshotResponse
```

### LLM Configuration

| Component | Model | Rationale |
|-----------|-------|-----------|
| QueryOrchestratorAgent | Gemini 2.5 Flash-Lite | Fast ReAct loop for query planning |
| SentimentAgent (LLM) | Gemini 2.5 Flash-Lite | Context-aware classification, 60% ensemble weight |
| CredibilityAgent | Gemini 2.5 Flash-Lite | Fast content quality scoring |
| ThemeAgent (×6) | Gemini 2.5 Flash | Theme-specific insight generation |
| CoordinatorAgent | Gemini 2.5 Flash-Lite | Narrative generation |
| RoBERTa | twitter-roberta-base-sentiment-latest | Local model, 40% ensemble weight |
| Embeddings | BAAI/bge-small-en-v1.5 | Local 384-dim vectors for RAG |

---

## Sentiment Analysis Methodology

### Ensemble Architecture

The system employs a **full ensemble** where both models analyze ALL documents, with predictions combined via weighted voting:

| Model | Type | Weight | Strengths |
|-------|------|--------|-----------|
| RoBERTa (`twitter-roberta-base-sentiment-latest`) | Transformer | 40% | Fast inference, trained on 124M tweets, handles social media slang |
| Gemini 2.5 Flash-Lite | Large Language Model | 60% | Context-aware, understands local civic issues, nuanced reasoning |

### Why RoBERTa Twitter?

The `cardiffnlp/twitter-roberta-base-sentiment-latest` model was selected because:

1. **Training Data Alignment** — Trained on 124M tweets, matching the informal style of Facebook/Reddit posts
2. **Native 3-Class Output** — Directly outputs positive/negative/neutral probabilities
3. **Benchmark Performance** — State-of-the-art on TweetEval benchmark
4. **Informal Text Handling** — Robust to slang, abbreviations, emoticons, Taglish

### Ensemble Voting Algorithm

```python
# Step 1: RoBERTa processes all documents (batch inference)
roberta_probs = roberta.predict_batch_with_probs(texts)  # Returns P(neg, neu, pos)

# Step 2: Gemini processes all documents (batches of 15)
gemini_probs = gemini.analyze_all(documents)  # Returns P(neg, neu, pos) with confidence

# Step 3: Weighted probability combination
ROBERTA_WEIGHT = 0.4
GEMINI_WEIGHT = 0.6

combined = {
    "negative": (ROBERTA_WEIGHT * roberta["negative"]) + (GEMINI_WEIGHT * gemini["negative"]),
    "neutral":  (ROBERTA_WEIGHT * roberta["neutral"])  + (GEMINI_WEIGHT * gemini["neutral"]),
    "positive": (ROBERTA_WEIGHT * roberta["positive"]) + (GEMINI_WEIGHT * gemini["positive"]),
}

# Step 4: Final prediction = argmax of combined probabilities
final_label = max(combined, key=combined.get)
final_confidence = combined[final_label]
```

### Model Agreement Tracking

Each document records agreement status for analysis quality assessment:

| Agreement Type | Description |
|----------------|-------------|
| `full_agreement` | Both models predict the same label |
| `roberta_dominant` | Final matches RoBERTa, differs from Gemini |
| `gemini_dominant` | Final matches Gemini, differs from RoBERTa |
| `ensemble_decision` | Final differs from both individual predictions |

### Memory Optimization

The sentiment analysis includes production hardening:
- **Sequential Processing**: RoBERTa runs first, then Gemini (prevents OOM on Railway)
- **Timeout Protection**: 120s total timeout, 30s per Gemini batch
- **Batch Size**: 15 documents per Gemini API call
- **Unicode Sanitization**: Removes surrogate characters that break APIs

---

## 5-Signal Credibility Framework

### Overview

The CredibilityAgent implements a **Multi-Signal Verification Strategy** with weighted ensemble scoring. Each signal is independently measurable for ablation studies.

| Signal | Weight | Description |
|--------|--------|-------------|
| Domain Trust | 25% | Source reputation based on tiered domain scoring |
| Semantic Cross-Reference | 20% | Corroboration detection using BGE embeddings |
| Google Fact Check API | 15% | External verification against fact-checker database |
| LLM Pattern Recognition | 20% | Gemini analyzes for misinformation patterns |
| Tavily Web Verification | 20% | Real-time web search for claim corroboration |

### Signal 1: Domain Trust (25%)

Tiered scoring based on source domain reputation:

| Tier | Score Range | Examples |
|------|-------------|----------|
| Government | 0.90–0.95 | gov.ph, pia.gov.ph, pna.gov.ph |
| Fact-Checkers | 0.85–0.90 | verafiles.org, rappler.com |
| Established News | 0.75–0.82 | inquirer.net, philstar.com, gmanetwork.com |
| Organizations | 0.65–0.70 | .org.ph, .org |
| Social Media | 0.40–0.50 | facebook.com, reddit.com, twitter.com |
| User-Generated | 0.35–0.45 | medium.com, wordpress.com |

### Signal 2: Semantic Cross-Reference (20%)

Uses **BGE-small-en-v1.5 embeddings** to detect corroboration across independent sources:

```python
# Embed all documents
embeddings = embedding_service.embed_batch(doc_texts)

# Compute cosine similarity between document pairs
similarity = cosine_similarity(emb_i, emb_j)

# Threshold: 0.70 cosine similarity = semantically same story
if similarity >= 0.70 and domain_i != domain_j:
    corroborating_sources.add(domain_j)
```

**Corroboration Scoring:**

| Independent Corroborating Sources | Score |
|-----------------------------------|-------|
| 3+ sources | 0.95 (well-corroborated) |
| 2 sources | 0.85 (good corroboration) |
| 1 source | 0.70 (some corroboration) |
| 0 sources | 0.45 (single source) |

**Why Semantic over Keyword Matching?**
- Captures meaning, not just word overlap
- Handles paraphrasing and synonyms
- More robust to different writing styles

### Signal 3: Google Fact Check API (15%)

Queries Google's Fact Check Tools API to find existing fact-checks:

```python
claims = await search_fact_checks(
    query=f"{doc.title} {doc.snippet}"[:200],
    api_key=api_key,
    language_code="en",
    max_age_days=365
)
```

**Rating Score Mapping:**

| Fact-Check Rating | Score |
|-------------------|-------|
| True / Accurate | 0.95 |
| Mostly True | 0.85 |
| Half True / Mixture | 0.55–0.60 |
| Mostly False | 0.25 |
| False / Pants on Fire | 0.05–0.10 |
| Unproven / Unverified | 0.50 |

### Signal 4: LLM Pattern Recognition (20%)

Gemini 2.5 Flash analyzes content for misinformation indicators:

**Detected Patterns:**

| Pattern Type | Examples | Severity |
|--------------|----------|----------|
| Conspiracy Framing | "they don't want you to know", "wake up", "sheeple" | High |
| False Certainty | "100% proven", "scientists baffled" | High |
| Sensationalism | "exposed!", "shocking" | Medium |
| False Urgency | "share before deleted" | Medium |
| Social Proof Manipulation | "going viral", "everyone is talking" | Medium |
| Delegitimization | "fake news", "mainstream media lies" | Medium |

**Output Format:**
```json
{
  "score": 0.75,
  "reasoning": "Professional language, specific details, but single source",
  "red_flags": ["UNVERIFIED_CLAIMS"],
  "misinfo_risk": "low"
}
```

### Signal 5: Tavily Web Verification (20%)

Real-time web search to verify claims against authoritative sources:

```python
result = tavily_client.search(
    query=f"{claim} fact check verified",
    search_depth="advanced",
    include_answer=True,
    max_results=5
)
```

**Trusted Verification Domains:**
- Government: gov.ph, pia.gov.ph, pna.gov.ph
- Major News: inquirer.net, philstar.com, gmanetwork.com, abs-cbn.com
- Fact-Checkers: rappler.com, verafiles.org
- International: reuters.com, ap.org, bbc.com

**Verification Status:**

| Status | Condition | Score |
|--------|-----------|-------|
| `verified` | 2+ trusted sources confirm | 0.85–0.95 |
| `partial` | 1 trusted source or some confirmation | 0.60–0.70 |
| `unverified` | No trusted coverage found | 0.50 |
| `disputed` | Contradiction signals without confirmation | 0.30 |
| `contradicted` | 3+ strong contradiction signals | 0.20 |

### Final Credibility Score Calculation

```python
final_score = (
    WEIGHTS["domain"] * domain_score +           # 0.25
    WEIGHTS["cross_reference"] * xref_score +    # 0.20
    WEIGHTS["fact_check"] * fact_check_score +   # 0.15
    WEIGHTS["llm"] * llm_score +                 # 0.20
    WEIGHTS["tavily"] * tavily_score             # 0.20
)

# Credibility Tiers
if final_score >= 0.75: tier = "high"
elif final_score >= 0.55: tier = "medium"
elif final_score >= 0.35: tier = "low"
else: tier = "very_low"  # Potential misinformation
```

---

## RAG Pipeline Methodology

### Cyclic Learning Architecture (Novel Contribution)

Unlike standard RAG systems that are read-only, Hinaing implements a **Read-Write Memory Loop**:

1. **Node 3 (Recall)**: Fetches relevant history BEFORE analysis
2. **Node 5 (Consolidation)**: Writes NEW analysis back into memory AFTER enrichment

**Result**: The system learns from each run. Run #10 has access to insights from Runs #1–9.

### Document Chunking (SemanticChunker)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk Size | 400 characters | Balances context vs. embedding quality |
| Chunk Overlap | 100 characters | Maintains context continuity |
| Min Chunk Size | 50 characters | Filters noise from short fragments |

**Chunking Strategy:**
1. Combine title + snippet into full text
2. Split into sentences using regex boundaries
3. Group sentences into chunks of target size
4. Apply overlap for context continuity
5. Generate unique chunk_id using SHA-256 hash

### Embedding Generation (EmbeddingService)

| Property | Value |
|----------|-------|
| Model | BAAI/bge-small-en-v1.5 |
| Dimensions | 384 |
| Device | CPU (optimized for Railway containers) |
| Normalization | Pre-normalized for cosine similarity |
| Batch Size | 16 |
| Thread Count | 2 (controlled for container environments) |

**Optimizations:**
- Gradients disabled globally for inference
- LRU cache for repeated query embeddings (max 100)
- Unicode sanitization before tokenization

### Vector Storage (Qdrant)

| Property | Value |
|----------|-------|
| Storage | Qdrant Cloud |
| Distance Metric | Cosine similarity |
| Collection | `baguio_documents` |
| Retrieval | Top-k per focus area (k=10) |

### Memory Recall Strategy

```python
async def retrieve_knowledge(focus_areas: list[str], limit: int = 20):
    """Targeted searches per focus area for coverage."""
    per_area_limit = max(3, limit // len(focus_areas) + 1)
    
    for area in focus_areas:
        # Expand query with FOCUS_CONCERN_KEYWORDS
        query_text = f"{area} {' '.join(rich_keywords)}"
        
        # Cosine similarity search
        results = await vector_store.search(query=query_text, k=per_area_limit)
```

---

## Query Orchestration Methodology

### ReAct Reasoning Loop

The QueryOrchestratorAgent uses **ReAct (Reasoning + Acting)** pattern with Gemini 2.5 Flash:

```
Question: Create search queries for Baguio City civic monitoring
Thought: I need to analyze focus areas and generate diverse queries
Action: analyze_focus_areas
Action Input: {"focus_areas": ["health", "safety"]}
Observation: {"clusters": [...], "instruction": "Generate ONE query per cluster"}
Thought: I should generate queries from each cluster for diversity
Action: generate_query
Action Input: {"clusters": [...]}
Observation: {"queries": [...], "type": "diverse_multi_query"}
Thought: I have crafted diverse queries covering all topics
Final Answer: {"strategy": "multi-query for topic diversity", "queries": [...]}
```

### Custom Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `analyze_focus_areas` | Retrieves KEYWORD_CLUSTERS per focus area | `{"focus_areas": [...]}` | Keyword clusters organized by topic |
| `generate_query` | Builds diverse queries from clusters | `{"clusters": [...]}` | Multiple queries (max 6) |
| `evaluate_query` | Validates topic diversity | `{"queries": [...], "focus_areas": [...]}` | Coverage assessment |

### KEYWORD_CLUSTERS Structure

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
    "tourism": [...],
    "economy": [...],
    "environment": [...],
}
```

### Multi-Query Diversity Strategy

1. **One query per cluster** ensures topic diversity
2. **Max 6 queries** for full topic coverage
3. **Round-robin merging** prevents any single topic from dominating results
4. **Time suffix** added to queries (e.g., `after:2025-12-14`)

### Time-Based Search Filtering

| Layer | Implementation | Example |
|-------|----------------|---------|
| Query-Level | `after:YYYY-MM-DD` suffix | `("Baguio hospital") after:2025-12-14` |
| API-Level | LangSearch `freshness` parameter | `oneDay` for 6h/24h |
| Client-Side | `published_at` filtering | Filter docs older than cutoff |

---

## Theme Classification & Insight Generation

### Theme Categories

| Theme Key | Label | Focus Values | Example Keywords |
|-----------|-------|--------------|------------------|
| `infrastructure` | Infrastructure | {infrastructure} | road, traffic, water, power, bridge |
| `health` | Health & Wellness | {health} | hospital, dengue, covid, vaccine |
| `safety` | Public Safety | {safety} | crime, police, landslide, accident |
| `tourism` | Tourism & Events | {tourism} | tourist, hotel, panagbenga, burnham |
| `economy` | Business & Economy | {economy, business} | market, vendor, SM Prime, livelihood |
| `environment` | Environment | {environment} | garbage, pollution, tree, flooding |

### Theme Routing Algorithm

```python
def route_documents_by_theme(documents, focus_areas):
    """Strict content matching using expanded keywords."""
    
    # Merge config keywords with FOCUS_CONCERN_KEYWORDS
    expanded_keywords = merge_keywords(THEME_GROUPS, FOCUS_CONCERN_KEYWORDS)
    
    for doc in documents:
        content = f"{doc.title} {doc.snippet} {doc.url}".lower()
        
        for theme_key in active_themes:
            keywords = expanded_keywords[theme_key]
            if any(kw in content for kw in keywords):
                theme_docs[theme_key].append(doc)
```

### Theme Agent Execution

Each theme agent runs in parallel using `ThreadPoolExecutor(max_workers=6)`:

```python
def run_theme_agent(theme_label: str, prompt: str, documents: list[dict]):
    """Direct Gemini 2.5 Flash call for theme-specific insights."""
    
    # Build context with URLs for evidence
    doc_lines = [f"- [{title}]({url}): {snippet}" for doc in documents[:5]]
    
    # Theme-specific focus instruction
    focus = theme_focus.get(theme_label, f"Focus on {theme_label} aspects only.")
    
    # Generate structured JSON insight
    response = model.generate_content(prompt)
    
    return {
        "title": "Concise insight title",
        "detail": "Actionable detail under 240 characters",
        "evidence": ["actual_urls_from_documents"]
    }
```

---

## Retrieval Agent Methodology

### Multi-Source Retrieval

The RetrievalAgent fetches documents from three sources in parallel:

| Source | Method | Limit | Notes |
|--------|--------|-------|-------|
| Web | LangSearch API | 10 per query | Semantic search + reranking |
| Facebook | Apify scraper | Variable | Baguio PIO public pages |
| Reddit | PRAW API | 25 total | r/baguio, r/Philippines, r/CasualPH |

### Parallel Batch Execution

```python
# Run queries in parallel batches of 3
batch_size = 3
for batch_start in range(0, len(queries), batch_size):
    batch = queries[batch_start:batch_start + batch_size]
    
    # Brief pause between batches for rate limits
    if batch_start > 0:
        await asyncio.sleep(1.5)
    
    # Run batch in parallel
    results = await asyncio.gather(*[fetch_query(task) for task in batch])
```

### Diversity-Aware Merging

```python
def _merge_with_diversity(topic_results, other_results):
    """Round-robin through topics, taking 3 docs at a time from each."""
    
    docs_per_round = 3
    
    while True:
        for topic in topics:
            merged.extend(topic_results[topic][start:start + docs_per_round])
        
        if not added_this_round:
            break
    
    merged.extend(other_results)  # Facebook, Reddit at end
    return merged
```

### Document Filtering Pipeline

1. **Excluded Sources**: Remove Wikipedia, TripAdvisor, booking sites
2. **Location Filter**: Keep only documents mentioning Baguio-related terms
3. **Time Filter**: Apply time window cutoff
4. **Deduplication**: Remove duplicate URLs and similar titles
5. **Cap**: Maximum 100 documents

---

## Evaluation Metrics

### Sentiment Analysis

| Metric | Target | Measurement |
|--------|--------|-------------|
| Ensemble Accuracy | > 85% | Against labeled validation set |
| Model Agreement Rate | > 70% | Percentage of `full_agreement` |
| Per-Batch Latency | < 5s | 15 documents per Gemini batch |

### Credibility Assessment

| Metric | Target | Measurement |
|--------|--------|-------------|
| Signal Coverage | 5/5 signals | All signals computed per document |
| High Credibility Rate | > 40% | Documents with score ≥ 0.75 |
| Misinformation Detection | Flag rate | Documents with `misinfo_risk: high` |

### System Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| End-to-End Latency | < 30s | Full snapshot generation |
| Document Retrieval | 50–100 docs | Per snapshot request |
| Theme Coverage | 6/6 themes | All requested themes with insights |
| Memory Consolidation | > 0 chunks | New knowledge stored per run |

### Observability

Per-node telemetry tracked via MetricsCollector:
- `query_orchestrator` — Query planning duration, query count
- `external_retrieval` — Retrieval duration, document count by source
- `internal_retrieval` — RAG recall duration, relevance scores
- `sentiment` — Analysis duration, distribution, agreement rate
- `credibility` — Scoring duration, average score, tier distribution
- `theme_routing` — Routing duration, documents per theme
- `memory_consolidation` — Ingestion duration, chunks stored
- `theme_agents` — Insight generation duration
- `coordinator` — Narrative generation duration

---

## Technology Stack

### Backend

| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python 3.11+) |
| Package Manager | Poetry |
| Orchestration | LangChain, LangGraph |
| LLM | Google Gemini (2.5 Flash-Lite, 2.5 Flash) |
| Transformer | HuggingFace Transformers (RoBERTa) |
| Embeddings | Sentence Transformers (BGE-small-en-v1.5) |
| Vector DB | Qdrant Cloud |
| Web Search | LangSearch API |
| Fact-Checking | Google Fact Check API, Tavily API |
| Social Media | PRAW (Reddit), Apify (Facebook) |
| Observability | LangSmith |
| Deployment | Railway |

### Frontend

| Component | Technology |
|-----------|------------|
| Framework | Next.js 15, React 19 |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Data Fetching | SWR |
| State Management | React hooks |

---

## Scientific Contributions

### 1. Cyclic Learning Graph (Novel)

Standard RAG systems are read-only. Hinaing implements a **Read-Write Memory Loop** where:
- Node 3 recalls past learnings BEFORE analysis
- Node 5 writes new learnings AFTER analysis
- Each run enriches the knowledge base for future queries

### 2. Distributed Cognition via Specialized Agents

Unlike monolithic LLM approaches, Hinaing decomposes analysis into 13 specialized agents:
- Each agent is grounded in domain-specific context
- The Health Agent ignores traffic data, reducing noise and hallucination
- Parallel execution reduces latency

### 3. 5-Signal Credibility Ensemble

Multi-signal verification treats "truth" as consensus of independent signals:
- Each signal is independently measurable for ablation studies
- Combines static (domain trust) and dynamic (real-time verification) signals
- Detects misinformation patterns beyond simple fact-checking

### 4. Ensemble Sentiment with Agreement Tracking

Weighted voting between transformer and LLM provides:
- Speed and consistency from RoBERTa
- Contextual understanding from Gemini
- Agreement tracking for confidence calibration

---

## Limitations

1. **Ensemble Weight Tuning** — Current 40/60 weights are heuristic; validation set optimization pending
2. **Credibility Ground Truth** — No labeled misinformation dataset for Philippine civic content
3. **Language Support** — Optimized for English; Taglish/Filipino support is implicit via RoBERTa
4. **Rate Limits** — Gemini (15 RPM), Tavily (1000/month) constrain throughput
5. **Vector Store Scale** — Now using Qdrant Cloud for production-grade scalability and persistence

---

## Future Work

1. **Ensemble Weight Optimization** — Tune weights using labeled validation set
2. **Fine-Tuned Credibility Model** — Train classifier on Philippine misinformation dataset
3. **Streaming Insights** — Progressive rendering as theme agents complete
4. **Evaluation Harness** — Automated metrics for sentiment accuracy, RAG relevance (MRR, NDCG)
5. **Supervisor Agent** — Re-route documents when theme agents return low-quality insights
