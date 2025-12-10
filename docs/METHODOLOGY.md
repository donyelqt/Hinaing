# Methodology

This document describes the research methodology for **Hinaing**, a multi-agent AI system with real-time intelligent search and RAG for context-aware public opinion analysis in Baguio City, Philippines.

## Research Design

### System Development Methodology

The system follows an iterative, agent-based development approach combining:

1. **Multi-Agent Architecture Design** - Decomposing the sentiment analysis pipeline into specialized, cooperating agents
2. **Ensemble Learning** - Combining transformer and LLM models for robust sentiment classification
3. **Retrieval-Augmented Generation (RAG)** - Grounding insights in real-time retrieved context

### Data Sources

| Source | Type | Collection Method | Content |
|--------|------|-------------------|---------|
| LangSearch API | Web | Semantic search + reranking | News articles, blogs, forums |
| Facebook | Social Media | Apify ingestion | Public group posts, comments |
| Reddit | Social Media | API integration (planned) | Community discussions |

### Geographic Scope

All analysis is scoped to **Baguio City, Philippines** through:
- Location-specific search queries (e.g., "Baguio", "BGH", "Kennon Road", "Session Road")
- Local keyword dictionaries per theme
- Time-based filtering for recency (6h, 24h, 3d, 7d windows)

---

## Multi-Agent Architecture

### Agent Orchestration

The system uses **LangGraph** for workflow orchestration with the following agent pipeline:

```
SnapshotRequest
       ↓
1. Query Orchestrator Agent (ReAct)
       ↓
2. Retrieval Agent (LangSearch + Facebook)
       ↓
3. Ensemble Sentiment Agent (RoBERTa + Gemini)
       ↓
4. Credibility Agent ∥ Theme Router Agent (parallel)
       ↓
5. Context Augmentation Agent (RAG)
       ↓
6. Theme Agents (6x parallel)
       ↓
7. Snapshot Builder (Narrative Generation)
       ↓
SnapshotResponse
```

### Agent Descriptions

| Agent | Purpose | Technology |
|-------|---------|------------|
| Query Orchestrator | Generates optimized search queries using ReAct reasoning | Gemini 2.0 Flash, LangChain Tools |
| Retrieval Agent | Fetches documents from multiple sources | LangSearch API, Apify |
| Sentiment Agent | Classifies document sentiment | RoBERTa + Gemini Ensemble |
| Credibility Agent | Scores source trustworthiness | Domain heuristics (.gov.ph, .org) |
| Theme Router | Routes documents to 6 thematic categories | Keyword matching |
| Context Agent | Augments themes with RAG context | MiniLM-L6-v2, Qdrant |
| Theme Agents | Generates insights per theme | Gemini 2.5 Pro |

---

## Sentiment Analysis Methodology

### Ensemble Approach

The system employs a **weighted ensemble** of two complementary models:

| Model | Type | Weight | Strengths |
|-------|------|--------|-----------|
| RoBERTa (`twitter-roberta-base-sentiment-latest`) | Transformer | 40% | Fast inference, trained on 124M tweets, handles social media slang |
| Gemini 2.5 Pro | Large Language Model | 60% | Context-aware, understands local civic issues, nuanced reasoning |

### Why RoBERTa Twitter?

The `cardiffnlp/twitter-roberta-base-sentiment-latest` model was selected because:

1. **Training Data Alignment** - Trained on 124M tweets, matching the informal style of Facebook/Reddit posts
2. **Native 3-Class Output** - Directly outputs positive/negative/neutral (no binary-to-ternary conversion needed)
3. **Benchmark Performance** - 94% accuracy on TweetEval benchmark
4. **Informal Text Handling** - Robust to slang, abbreviations, emoticons, Taglish

### Ensemble Voting Algorithm

```python
# Both models analyze ALL documents
roberta_probs = roberta.predict_batch_with_probs(texts)  # P(neg, neu, pos)
gemini_probs = gemini.analyze_all(documents)             # P(neg, neu, pos)

# Weighted probability combination
combined = {
    "negative": (0.4 * roberta["negative"]) + (0.6 * gemini["negative"]),
    "neutral":  (0.4 * roberta["neutral"])  + (0.6 * gemini["neutral"]),
    "positive": (0.4 * roberta["positive"]) + (0.6 * gemini["positive"]),
}

# Final prediction = argmax
final_label = max(combined, key=combined.get)
```

### Model Agreement Tracking

Each document records agreement status for analysis:
- `full_agreement` - Both models predict same label
- `roberta_dominant` - Final matches RoBERTa, differs from Gemini
- `gemini_dominant` - Final matches Gemini, differs from RoBERTa
- `ensemble_decision` - Final differs from both individual predictions

---

## RAG Pipeline Methodology

### Document Chunking

The **SemanticChunker** splits documents for embedding:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk Size | 400 characters | Balances context vs. embedding quality |
| Chunk Overlap | 100 characters | Maintains context continuity across chunks |
| Min Chunk Size | 50 characters | Filters noise from very short fragments |

**Chunking Strategy:**
1. Combine title + snippet into full text
2. Split into sentences using regex boundaries
3. Group sentences into chunks of target size
4. Apply overlap for context continuity

### Embedding Generation

The **EmbeddingService** uses `sentence-transformers/all-MiniLM-L6-v2`:

| Property | Value |
|----------|-------|
| Model | all-MiniLM-L6-v2 |
| Dimensions | 384 |
| Device | CPU (optimized for Railway containers) |
| Normalization | Pre-normalized for cosine similarity |
| Batch Size | 16 |

**Optimizations:**
- Thread count limited to 2 for container environments
- Gradients disabled globally for inference
- LRU cache for repeated query embeddings

### Vector Storage

**Qdrant** in-memory vector store (vector db later) with:
- Cosine similarity metric
- Top-k retrieval (k=10 per theme)
- Metadata filtering by theme

---

## Query Orchestration Methodology

### ReAct Reasoning Loop

The Query Orchestrator uses **ReAct (Reasoning + Acting)** pattern:

```
Question: [user request]
Thought: [LLM reasoning about approach]
Action: [tool to invoke]
Action Input: [JSON parameters]
Observation: [tool result]
... (repeat 3-4 iterations)
Thought: I have crafted an optimized query.
Final Answer: [optimized query plan]
```

### Custom Tools

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `analyze_focus_areas` | Retrieves curated keywords per focus area | `{"focus_areas": [...]}` | All relevant keywords |
| `generate_query` | Builds OR-combined search query | `{"keywords": [...]}` | Optimized query string |
| `evaluate_query` | Validates keyword coverage | `{"query": "...", "focus_areas": [...]}` | Coverage assessment |

### Time-Based Search Filtering

Multi-layer freshness filtering ensures recent content:

| Layer | Implementation | Example |
|-------|----------------|---------|
| Query-Level | `after:YYYY-MM-DD` suffix | `("Baguio hospital") after:2025-12-09` |
| API-Level | LangSearch `freshness` parameter | `oneDay` for 6h/24h requests |
| Client-Side | `published_at` filtering | Filter docs older than cutoff |

---

## Theme Classification

### Theme Categories

Documents are routed to 6 civic themes:

| Theme | Label | Example Keywords |
|-------|-------|------------------|
| Infrastructure | `infrastructure` | road, traffic, water, power, bridge, construction |
| Health & Wellness | `health` | hospital, clinic, dengue, covid, vaccine, medicine |
| Public Safety | `safety` | crime, police, fire, landslide, accident, emergency |
| Tourism & Events | `tourism` | tourist, hotel, festival, panagbenga, visitor |
| Business & Economy | `economy` | market, vendor, livelihood, SM Prime, price |
| Environment | `environment` | garbage, pollution, waste, tree, climate |

### Theme Agent Processing

Each theme agent:
1. Receives RAG-augmented context (top 10 relevant chunks)
2. Generates structured insights using Gemini 2.5 Pro
3. Includes traceable evidence links to source documents
4. Runs in parallel (6 threads via ThreadPoolExecutor)

---

## Credibility & Misinformation Detection

### Multi-Signal Approach

The Enhanced Credibility Agent combines seven signals with weighted scoring for misinformation risk detection:

| Signal | Weight | Description |
|--------|--------|-------------|
| Domain Trust | 20% | Tiered trust scores by domain type |
| Cross-Reference | 15% | Semantic corroboration across independent sources |
| Google Fact Check API | 15% | External verification against fact-checker database |
| Gemini LLM Analysis | 20% | Content quality and misinformation pattern detection |
| Content Signals | 10% | Clickbait/quality heuristics + author attribution |
| Recency | 5% | Content freshness scoring |
| Tavily Verification | 15% | Real-time web search for claim corroboration |

### Domain Trust Tiers

| Tier | Score | Examples |
|------|-------|----------|
| Government | 0.90-0.95 | .gov.ph, pia.gov.ph |
| Fact-Checkers | 0.85-0.90 | verafiles.org, rappler.com |
| Established News | 0.75-0.80 | inquirer.net, philstar.com, gmanetwork.com |
| Organizations | 0.65-0.70 | .org, .org.ph |
| Social Media | 0.40-0.45 | facebook.com, reddit.com |

### Google Fact Check API Integration

The system queries Google's Fact Check Tools API to find existing fact-checks:

```python
claims = await search_fact_checks(
    query=f"{doc.title} {doc.snippet}",
    api_key=api_key,
    language_code="en",
    max_age_days=365
)

RATING_SCORES = {
    "true": 0.95,
    "mostly true": 0.85,
    "half true": 0.60,
    "mostly false": 0.30,
    "false": 0.10,
}
```

**Why Google Fact Check API?**
- Indexes Philippine fact-checkers (Rappler, Vera Files)
- 10,000 requests/day free tier
- Fast response (~200ms)
- Returns structured ClaimReview data

### LLM Credibility Analysis

Gemini 2.0 Flash assesses content quality considering:
1. Source legitimacy
2. Factual specificity (names, dates, locations)
3. Professional language
4. Misinformation indicators

Returns: `{"score": 0.X, "reasoning": "...", "red_flags": [...]}`

### Semantic Cross-Reference

The cross-reference signal uses **semantic similarity** to detect corroboration across independent sources:

```python
# Embed all documents using MiniLM-L6-v2
embeddings = embedding_service.embed_batch(doc_texts)

# Compute cosine similarity between documents
similarity = cosine_similarity(emb_i, emb_j)

# Threshold: 0.70 = semantically same story
if similarity >= 0.70 and domain_i != domain_j:
    corroborating_sources += 1
```

**Why Semantic over Keyword Matching?**
- Captures meaning, not just word overlap
- Handles paraphrasing and synonyms
- More robust to different writing styles
- MiniLM-L6-v2 is fast (384 dimensions, CPU-optimized)

**Corroboration Scoring:**
| Corroborating Sources | Score |
|-----------------------|-------|
| 3+ independent sources | 0.95 |
| 2 independent sources | 0.85 |
| 1 independent source | 0.70 |
| No corroboration | 0.45 |

### Content Quality Signals

| Signal | Effect | Detection |
|--------|--------|-----------|
| ALL CAPS | -0.20 | Title or content in uppercase |
| Excessive punctuation | -0.15 | More than 3 exclamation marks |
| Clickbait phrases | -0.10 | "shocking", "you won't believe" |
| Attribution | +0.10 | "according to", "reported by" |
| Official sources | +0.05 | "mayor", "city council" |
| Author byline | +0.10 | "by John Smith", "reported by Jane" |
| Specific dates | +0.05 | Date patterns in content |
| Specific numbers | +0.05 | Statistics, percentages |

**Author Attribution Detection:**
Named journalists add credibility. Patterns detected:
- `by [Name] [Surname]`
- `written by [Name]`
- `[Name], reporter/correspondent/editor`
- `staff writer/reporter`

### Credibility Tiers

| Tier | Score Range | Interpretation |
|------|-------------|----------------|
| High | ≥ 0.75 | Trusted source, verified content |
| Medium | 0.55-0.74 | Generally reliable |
| Low | 0.35-0.54 | Requires verification |
| Very Low | < 0.35 | Potential misinformation |

### Recency Factor

Documents are scored by freshness:
| Age | Score |
|-----|-------|
| < 6 hours | 1.00 |
| 6-24 hours | 0.90 |
| 1-3 days | 0.75 |
| 3-7 days | 0.60 |
| 1 week - 1 month | 0.45 |
| > 1 month | 0.35 |

### Tavily Claim Verification

The system uses Tavily API for real-time web search to verify claims against authoritative sources:

```python
# Search for corroborating evidence
result = await tavily_search(
    query=f"{doc.title} Baguio Philippines",
    include_domains=["gov.ph", "inquirer.net", "rappler.com", ...],
    max_results=5
)

# Score based on trusted source matches
if trusted_matches >= 3:
    score = 0.95  # Strong verification
elif trusted_matches == 2:
    score = 0.85  # Good verification
elif trusted_matches == 1:
    score = 0.70  # Some verification
else:
    score = 0.45  # No trusted verification
```

**Why Tavily?**
- Real-time web search (not just database lookup like Google Fact Check)
- Can filter by trusted domains (.gov.ph, established news)
- Provides claim-level verification
- 1,000 free API credits/month

**Trusted Verification Domains:**
- Government: gov.ph, pia.gov.ph, pna.gov.ph
- Major News: inquirer.net, philstar.com, gmanetwork.com, abs-cbn.com
- Fact-checkers: rappler.com, verafiles.org
- International: reuters.com, ap.org, bbc.com

### Misinformation Pattern Detection

The system detects common misinformation indicators:

| Pattern Type | Examples | Severity |
|--------------|----------|----------|
| Conspiracy Framing | "they don't want you to know", "wake up" | High |
| False Certainty | "100% proven", "scientists baffled" | High |
| Sensationalism | "exposed!", "shocking" | Medium |
| False Urgency | "share before deleted" | Medium |
| Social Proof Manipulation | "going viral", "everyone is talking" | Medium |

Documents with detected patterns receive penalty scores and are flagged with specific red flags for analyst review.

---

## Evaluation Metrics

### Sentiment Analysis

| Metric | Target | Measurement |
|--------|--------|-------------|
| Accuracy | > 85% | Against labeled validation set |
| Model Agreement | > 70% | Percentage of full_agreement |
| Latency | < 5s | Per batch of 12 documents |

### System Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| End-to-End Latency | < 30s | Full snapshot generation |
| Document Retrieval | > 20 docs | Per snapshot request |
| Theme Coverage | 6/6 themes | All themes with insights |

### Observability

Per-agent telemetry logged in `graph.py`:
- `orchestrate_queries` - Query planning duration
- `fetch_documents` - Retrieval duration + doc count
- `label_sentiment` - Sentiment analysis duration
- `analyze_enriched` - Credibility + routing duration
- `augment_context` - RAG pipeline duration
- `theme_agents` - Insight generation duration

---

## Technology Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python 3.11+) |
| Orchestration | LangChain, LangGraph |
| LLM | Google Gemini (2.5 Pro, 2.0 Flash) |
| Transformer | HuggingFace Transformers (RoBERTa) |
| Embeddings | Sentence Transformers (MiniLM-L6-v2) |
| Vector DB | Qdrant (in-memory) |
| Search | LangSearch API |
| Observability | LangSmith |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Next.js 15, React 19 |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Data Fetching | SWR |

---

## Limitations

1. **Ensemble Weight Tuning** - Current 40/60 weights are heuristic; validation set optimization pending
2. **Credibility Heuristics** - Domain-based scoring lacks ML-based verification
3. **Vector Store Persistence** - Qdrant runs in-memory; production requires persistent storage
4. **Language Support** - Optimized for English; Taglish/Filipino support is implicit via RoBERTa
5. **Real-Time Constraints** - LLM rate limits (15 RPM for Gemini) affect throughput

---

## Future Work (draft)

1. **Ensemble Weight Optimization** - Tune weights using labeled validation set
2. **Fine-Tuned Credibility Model** - Replace heuristics with ML classifier
3. **RAG Solutions Agent** - Recommend actions per theme from knowledge base
4. **Persistent Vector Storage** - Migrate Qdrant to persistent mode
5. **Human-in-the-Loop** - Review portal for analyst feedback integration
