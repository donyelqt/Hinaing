# RAG Vector Database Integration Plan

## Problem Statement

The current `augment_context` step in the pipeline is **redundant**:
- Uses in-memory Qdrant (`:memory:`) - data lost after each request
- Chunks and embeds the **same documents** that were just fetched
- Searches those same documents to find "relevant" chunks
- No historical context accumulation
- Adds ~1-2s latency without providing new information

## Solution: Persistent RAG with Historical Context

Transform the RAG system from redundant to valuable by:
1. Using **persistent storage** (file-based Qdrant)
2. **Accumulating historical documents** over time
3. **Augmenting fresh results** with related historical data
4. Enabling **trend analysis** for theme agents

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ENHANCED RAG PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  CURRENT FLOW (Redundant):                                              │
│  ─────────────────────────                                              │
│  fetch_docs → sentiment → credibility → augment_context → theme_agents  │
│                                              ↑                          │
│                                    (same docs, in-memory, lost)         │
│                                                                          │
│  NEW FLOW (Value-Added):                                                │
│  ───────────────────────                                                │
│  fetch_docs → sentiment → credibility → [PERSIST TO QDRANT]             │
│                                              ↓                          │
│                              [SEARCH HISTORICAL + FRESH]                │
│                                              ↓                          │
│                                    theme_agents (enriched context)      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Persistent Vector Store (Day 1)

**Goal**: Replace in-memory storage with file-based persistence

**Files to modify**:
- `backend/app/services/rag/vector_store.py`
- `backend/app/core/config.py`

**Steps**:
1. Add `QDRANT_PATH` environment variable (default: `./qdrant_data`)
2. Change `QdrantClient(path=":memory:")` to `QdrantClient(path=settings.qdrant_path)`
3. Add collection versioning for schema changes
4. Add `.gitignore` entry for `qdrant_data/`

**Code Change**:
```python
# vector_store.py
def __init__(self):
    settings = get_settings()
    qdrant_path = getattr(settings, 'qdrant_path', './qdrant_data')
    
    # Use persistent storage
    self.client = QdrantClient(path=qdrant_path)
```

---

### Phase 2: Document Deduplication (Day 1)

**Goal**: Prevent storing duplicate documents

**Files to modify**:
- `backend/app/services/rag/vector_store.py`
- `backend/app/schemas/rag.py`

**Steps**:
1. Generate deterministic document IDs from URL hash
2. Check existence before inserting
3. Update metadata if document already exists (fresher sentiment, etc.)

**Code Change**:
```python
async def add_chunks(self, chunks: list[DocumentChunk], deduplicate: bool = True) -> int:
    if deduplicate:
        # Check which chunks already exist
        existing_ids = self._get_existing_ids([c.chunk_id for c in chunks])
        chunks = [c for c in chunks if c.chunk_id not in existing_ids]
    
    if not chunks:
        logger.info("All chunks already exist, skipping insert")
        return 0
    # ... rest of insert logic
```

---

### Phase 3: Historical Context Retrieval (Day 2)

**Goal**: Augment fresh documents with related historical data

**Files to modify**:
- `backend/app/services/agents/context_agent.py`
- `backend/app/services/insights/graph.py`

**New Flow**:
```
1. Fresh documents arrive (28 docs from current search)
2. Store fresh docs in persistent Qdrant
3. For each theme, search Qdrant for:
   - Fresh docs (from this request)
   - Historical docs (from past requests, same theme)
4. Merge and deduplicate results
5. Pass enriched context to theme agents
```

**Code Change**:
```python
async def augment_context(
    self,
    fresh_documents: list[WebDocument],
    theme: str,
    include_historical: bool = True,
    historical_limit: int = 20,
) -> AugmentedContext:
    # Store fresh documents
    fresh_chunks = self.chunker.chunk_documents(fresh_documents)
    await self.vector_store.add_chunks(fresh_chunks, deduplicate=True)
    
    # Search for relevant context (includes historical)
    theme_query = self._build_theme_query(theme)
    results = await self.vector_store.search(
        query=theme_query,
        k=len(fresh_documents) + historical_limit,  # Fresh + historical
    )
    
    # Separate fresh vs historical for analysis
    fresh_urls = {str(d.url) for d in fresh_documents}
    fresh_results = [r for r in results if r.chunk.source_url in fresh_urls]
    historical_results = [r for r in results if r.chunk.source_url not in fresh_urls]
    
    return AugmentedContext(
        theme=theme,
        relevant_chunks=[r.chunk for r in results],
        fresh_count=len(fresh_results),
        historical_count=len(historical_results),
        # ... rest
    )
```

---

### Phase 4: Pipeline Restructure (Day 2)

**Goal**: Move context augmentation to correct position

**Files to modify**:
- `backend/app/services/insights/graph.py`

**New Pipeline**:
```python
# OLD (redundant):
graph.add_edge("label_sentiment_and_analyze", "augment_context")
graph.add_edge("augment_context", "theme_agents")

# NEW (value-added):
# Option A: Persist after analysis, augment in theme_agents
graph.add_edge("label_sentiment_and_analyze", "persist_to_rag")
graph.add_edge("persist_to_rag", "theme_agents")  # Theme agents query RAG directly

# Option B: Remove augment_context, integrate into theme_agents
graph.add_edge("label_sentiment_and_analyze", "theme_agents")
# Theme agents internally query persistent RAG for historical context
```

**Recommended**: Option B - cleaner, theme agents own their context retrieval

---

### Phase 5: Trend Analysis (Day 3 - Optional)

**Goal**: Enable historical trend comparison

**New Features**:
1. **Sentiment Trend**: Compare current theme sentiment to 7-day average
2. **Volume Trend**: Is this topic getting more/less coverage?
3. **Source Diversity**: Are we seeing new sources or same ones?

**Code Addition**:
```python
async def get_theme_trends(self, theme: str, days: int = 7) -> dict:
    """Get historical trends for a theme."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Query historical documents for this theme
    results = await self.vector_store.search(
        query=self._build_theme_query(theme),
        k=100,
        filter_metadata={"published_after": cutoff.isoformat()}
    )
    
    # Calculate trends
    sentiments = [r.chunk.metadata.get("sentiment") for r in results]
    return {
        "avg_sentiment": calculate_sentiment_score(sentiments),
        "volume": len(results),
        "unique_sources": len({r.chunk.source_url for r in results}),
    }
```

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/app/core/config.py` | Add | `QDRANT_PATH` setting |
| `backend/app/services/rag/vector_store.py` | Modify | Persistent storage, deduplication |
| `backend/app/services/agents/context_agent.py` | Modify | Historical context retrieval |
| `backend/app/services/insights/graph.py` | Modify | Pipeline restructure |
| `backend/app/schemas/rag.py` | Modify | Add `fresh_count`, `historical_count` |
| `.gitignore` | Add | `qdrant_data/` |

---

## Environment Variables

```env
# Add to backend/.env
QDRANT_PATH=./qdrant_data  # Local file storage (default)
# OR for production:
# QDRANT_URL=https://your-qdrant-cloud.com
# QDRANT_API_KEY=your-api-key
```

---

## Testing Plan

1. **Unit Tests**:
   - Deduplication works correctly
   - Historical retrieval returns past documents
   - Fresh vs historical separation is accurate

2. **Integration Tests**:
   - Run pipeline twice with same query
   - Second run should show historical context
   - No duplicate documents in store

3. **Manual Verification**:
   - Check `qdrant_data/` folder grows over time
   - Theme agents receive historical context
   - Insights mention historical trends

---

## Rollback Plan

If issues arise:
1. Set `QDRANT_PATH=:memory:` to revert to in-memory
2. Delete `qdrant_data/` folder to clear corrupted data
3. Original code preserved in git history

---

## Timeline

| Phase | Duration | Priority |
|-------|----------|----------|
| Phase 1: Persistent Storage | 2 hours | High |
| Phase 2: Deduplication | 1 hour | High |
| Phase 3: Historical Retrieval | 3 hours | High |
| Phase 4: Pipeline Restructure | 2 hours | High |
| Phase 5: Trend Analysis | 4 hours | Medium (Optional) |

**Total**: ~8-12 hours for core implementation

---

## Thesis Value

This enhancement demonstrates:
1. **RAG Architecture** - Proper retrieval-augmented generation
2. **Temporal Analysis** - Historical trend comparison
3. **Data Engineering** - Persistent storage, deduplication
4. **System Design** - Pipeline optimization, separation of concerns
