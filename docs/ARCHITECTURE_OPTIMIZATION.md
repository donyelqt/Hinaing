# Architecture Optimization Analysis

> **Thesis Title (Option 1):** 7-Node Agentic Graphs: Multi-Signal Fusion for Verified Context-Aware Public Opinion Synthesis
>
> **Thesis Title (Option 2):** Hinaing: A Neuro-Symbolic Multi-Agent Framework for Epistemic Truth Discovery in Civic Social Listening
>
> **Thesis Title (Option 3):** Hinaing: A Context-Engineered Self-Learning Multi-Agent Agentic AI System with Ensemble Sentiment and 5-Signal Credibility for Public Opinion Analysis in Baguio City
>
> **Thesis Title (Unified):** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

> **Thesis Title:** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

## Executive Summary

After deep analysis of your multi-agent civic sentiment system, I've identified **7 critical optimization opportunities** that can reduce latency by ~60%, cut API costs by ~40%, and improve insight quality significantly.

---

## Current Architecture Issues

### 1. **Sequential Pipeline Bottleneck**
```
Current Flow (Sequential):
orchestrate_queries → fetch_documents → label_sentiment → analyze_enriched → augment_context → theme_agents → build_snapshot
```

**Problem**: Each stage waits for the previous one. Total latency = sum of all stages.

**Impact**: ~15-25 seconds per request with typical document counts.

---

### 2. **Redundant LLM Calls**

| Stage | LLM Calls | Model | Purpose |
|-------|-----------|-------|---------|
| Query Orchestrator | 1-5 | gemini-2.0-flash-exp | ReAct reasoning |
| Sentiment Agent | N/batch_size | gemini-2.5-pro | Per-batch sentiment |
| Theme Agents | 6 | gemini-2.5-pro | Per-theme insights |
| Build Snapshot | 1-2 | gemini-2.0-flash-exp | Narrative generation |

**Problem**: 10-15+ LLM calls per request. Many are redundant.

**Cost Impact**: ~$0.05-0.15 per request at scale.

---

### 3. **In-Memory Vector Store**
```python
self.client = QdrantClient(path=":memory:")  # Current implementation
```

**Problem**: 
- Embeddings recomputed every request
- No persistence across requests
- No semantic deduplication

---

### 4. **Duplicate Sanitization**
`sanitize_text()` is defined in **7 different files**:
- `sentiment_agent.py`
- `theme_agent.py`
- `gemini.py`
- `embeddings.py`
- `chunker.py`
- `snapshot.py`
- `langsearch.py` (implicit)

---

### 5. **Inefficient Theme Routing**
```python
# Current: Keyword matching only
for key, meta in THEME_GROUPS.items():
    keyword_match = any(word in content for word in meta.get("keywords", set()))
```

**Problem**: Documents can match multiple themes → duplicate processing.

---

### 6. **RAG Pipeline Inefficiency**
```
Current: chunk → embed → store → search (per request)
```

**Problem**: Re-embedding same documents repeatedly. No cross-request learning.

---

### 7. **No Caching Layer**
- Same queries hit LangSearch API repeatedly
- No response caching for similar requests
- No embedding cache persistence

---

## Optimized Architecture

### Phase 1: Parallel Pipeline (Quick Win)

```mermaid
flowchart TB
    subgraph Stage1["1. Parallel Init"]
        QO[Query Orchestrator]
        EMB[Warm Embedding Model]
        QO & EMB
    end

    subgraph Stage2["2. Parallel Retrieval"]
        WEB[LangSearch]
        FB[Facebook]
        WEB & FB
    end

    subgraph Stage3["3. Unified Processing"]
        DEDUP[Deduplicate + Rerank]
        SENT[Ensemble Sentiment]
        DEDUP --> SENT
    end

    subgraph Stage4["4. Parallel Analysis"]
        CRED[Credibility]
        THEME[Theme Router]
        RAG[RAG Augment]
        CRED & THEME & RAG
    end

    subgraph Stage5["5. Parallel Theme Insights"]
        T1[Theme 1] & T2[Theme 2] & T3[Theme 3] & T4[Theme 4] & T5[Theme 5] & T6[Theme 6]
    end

    subgraph Stage6["6. Build Response"]
        SNAP[Snapshot Builder]
    end

    Stage1 --> Stage2 --> Stage3 --> Stage4 --> Stage5 --> Stage6
```

**Expected Improvement**: 40% latency reduction

---

### Phase 2: Consolidated LLM Strategy

#### Before (10-15 calls):
```
Query Orchestrator: 1-5 calls (ReAct)
Sentiment: N calls (batched)
Theme Agents: 6 calls
Narrative: 1-2 calls
```

#### After (3-4 calls):
```
1. Query Planning: 1 call (direct, no ReAct)
2. Sentiment + Theme Classification: 1 call (combined)
3. Theme Insights: 1 call (batched all themes)
4. Narrative: 1 call
```

**Implementation**:
```python
# Combined prompt for sentiment + theme classification
COMBINED_ANALYSIS_PROMPT = """
Analyze these {n} documents for Baguio City civic monitoring.

For each document, provide:
1. sentiment: positive/negative/neutral with confidence
2. themes: list of matching themes from [infrastructure, health, safety, tourism, economy, environment]
3. key_phrases: 2-3 important phrases

Return JSON array.
"""
```

**Expected Improvement**: 60% cost reduction, 30% latency reduction

---

### Phase 3: Persistent RAG with Semantic Deduplication

```python
# Optimized Vector Store
class PersistentVectorStore:
    def __init__(self):
        # Use file-based Qdrant for persistence
        self.client = QdrantClient(path="./qdrant_data")
        
    async def add_if_new(self, chunks: list[DocumentChunk]) -> int:
        """Only embed and store chunks not already in store."""
        existing_ids = await self._get_existing_ids()
        new_chunks = [c for c in chunks if c.chunk_id not in existing_ids]
        
        if new_chunks:
            return await self.add_chunks(new_chunks)
        return 0
    
    async def semantic_deduplicate(self, docs: list[WebDocument], threshold: float = 0.92) -> list[WebDocument]:
        """Remove semantically similar documents."""
        embeddings = self.embedding_service.embed_batch([d.snippet for d in docs])
        
        unique = []
        for i, (doc, emb) in enumerate(zip(docs, embeddings)):
            is_duplicate = False
            for j, prev_emb in enumerate(embeddings[:i]):
                if cosine_similarity(emb, prev_emb) > threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(doc)
        
        return unique
```

---

### Phase 4: Intelligent Caching

```python
from functools import lru_cache
from hashlib import md5
import redis

class CacheLayer:
    def __init__(self):
        self.redis = redis.Redis()  # Or use in-memory dict for dev
        self.ttl = 300  # 5 minutes
    
    def cache_key(self, request: SnapshotRequest) -> str:
        """Generate cache key from request parameters."""
        key_data = f"{sorted(request.platforms)}:{request.time_window}:{sorted(request.focus_areas)}"
        return md5(key_data.encode()).hexdigest()
    
    async def get_or_compute(self, request: SnapshotRequest, compute_fn) -> SnapshotResponse:
        key = self.cache_key(request)
        
        cached = self.redis.get(key)
        if cached:
            return SnapshotResponse.model_validate_json(cached)
        
        result = await compute_fn(request)
        self.redis.setex(key, self.ttl, result.model_dump_json())
        return result
```

---

### Phase 5: Unified Text Sanitization

```python
# backend/app/utils/text.py
import re
from functools import lru_cache

@lru_cache(maxsize=10000)
def sanitize_text(text: str | None) -> str:
    """Centralized text sanitization with caching."""
    if not text:
        return ""
    
    # Remove surrogate characters (U+D800 to U+DFFF)
    cleaned = re.sub(r'[\ud800-\udfff]', '', str(text))
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
    # Remove zero-width characters
    cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', cleaned)
    
    return cleaned.strip()
```

---

## Optimized Graph Structure

```python
# Optimized LangGraph workflow
graph = StateGraph(SnapshotState)

# Stage 1: Parallel initialization
graph.add_node("init", parallel_init)  # Query planning + model warmup

# Stage 2: Parallel retrieval
graph.add_node("retrieve", parallel_retrieve)  # Web + Facebook concurrent

# Stage 3: Unified processing
graph.add_node("process", unified_process)  # Dedupe + Sentiment + Theme in one LLM call

# Stage 4: Parallel theme insights
graph.add_node("insights", parallel_theme_insights)  # All themes in one batched call

# Stage 5: Build response
graph.add_node("build", build_snapshot)

# Linear flow (but internal parallelism)
graph.add_edge(START, "init")
graph.add_edge("init", "retrieve")
graph.add_edge("retrieve", "process")
graph.add_edge("process", "insights")
graph.add_edge("insights", "build")
graph.add_edge("build", END)
```

---

## Implementation Priority

| Priority | Optimization | Effort | Impact | Timeline |
|----------|-------------|--------|--------|----------|
| 🔴 P0 | Consolidate LLM calls | Medium | High (60% cost) | 2-3 days |
| 🔴 P0 | Parallel retrieval | Low | Medium (30% latency) | 1 day |
| 🟡 P1 | Persistent vector store | Medium | Medium (no re-embed) | 2 days |
| 🟡 P1 | Unified sanitization | Low | Low (code quality) | 0.5 day |
| 🟢 P2 | Response caching | Medium | High (repeat queries) | 1-2 days |
| 🟢 P2 | Semantic deduplication | Medium | Medium (quality) | 1-2 days |

---

## Quick Wins (Implement Today)

### 1. Remove ReAct Overhead from Query Orchestrator

The ReAct loop adds 3-5 LLM calls for simple query building. Replace with direct call:

```python
# backend/app/services/agents/query_orchestrator.py

class QueryOrchestratorAgent:
    def run(self, request: SnapshotRequest) -> QueryPlan:
        """Direct query generation without ReAct overhead."""
        focus_values = request.focus_areas or [self.fallback_focus]
        
        # Direct keyword aggregation (no LLM needed)
        all_keywords = []
        for area in focus_values:
            keywords = FOCUS_CONCERN_KEYWORDS.get(area.lower(), [])
            all_keywords.extend(keywords)
        
        unique = list(dict.fromkeys(all_keywords))
        
        if unique:
            or_terms = " OR ".join(f'"{kw}"' for kw in unique[:15])  # Limit to 15
            query = f"({or_terms})"
        else:
            query = f"Baguio City {' '.join(focus_values)} problem OR concern"
        
        return QueryPlan(
            strategy=f"Direct query with {len(unique)} keywords",
            queries=[QueryTask(query=query, intent="targeted", priority=1)],
            expected_results=[f"Results for {', '.join(focus_values)}"],
        )
```

**Impact**: Saves 3-5 LLM calls, ~2-5 seconds latency

### 2. Batch Theme Insights in Single Call

```python
# Instead of 6 separate theme agent calls, batch them:

def batch_theme_insights(theme_docs: dict[str, list[WebDocument]]) -> list[Insight]:
    """Generate all theme insights in a single LLM call."""
    
    # Build combined context
    themes_context = []
    for theme_key, docs in theme_docs.items():
        if not docs:
            continue
        doc_summaries = [f"- {d.title}: {d.snippet[:100]}" for d in docs[:3]]
        themes_context.append(f"## {theme_key}\n" + "\n".join(doc_summaries))
    
    prompt = f"""Analyze these civic documents for Baguio City and generate insights.

{chr(10).join(themes_context)}

For each theme with documents, generate ONE insight with:
- category: theme name
- title: concise insight title
- detail: actionable detail under 200 chars
- evidence: relevant URLs

Return JSON array of insights."""

    # Single LLM call for all themes
    response = model.generate_content(prompt)
    return parse_insights(response.text)
```

**Impact**: 6 calls → 1 call, ~5-10 seconds saved

---

## Metrics to Track

After optimization, monitor:

1. **Latency**: P50, P95, P99 response times
2. **LLM Costs**: Tokens consumed per request
3. **Cache Hit Rate**: % of requests served from cache
4. **Embedding Reuse**: % of chunks already in vector store
5. **Quality**: User feedback on insight relevance

---

## Next Steps

1. **Immediate**: Implement Quick Wins (1-2 days)
2. **This Week**: Consolidate LLM calls (P0)
3. **Next Week**: Persistent vector store + caching (P1)
4. **Ongoing**: Monitor metrics and iterate

Would you like me to implement any of these optimizations now?
