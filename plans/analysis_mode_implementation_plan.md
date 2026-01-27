# Implementation Plan: Analysis Mode Fixes

## Objective

Fix the analysis mode implementation so that:
- **Sentiment Mode**: Runs full pipeline (nodes 1-7) with sentiment + theme routing ONLY (no credibility)
- **Credibility Mode**: Runs full pipeline (nodes 1-7) with credibility + theme routing ONLY (no sentiment)

## Current State

| Mode | Nodes Executed | Issue |
|------|----------------|-------|
| Full | [1, 2, 3, 4, 5, 6, 7] | ✅ Correct |
| Sentiment | [1, 2, 3, 4] | ❌ Stops at Node 4, runs both sentiment AND credibility |
| Credibility | N/A | ❌ Mode doesn't exist |

## Target State

| Mode | Nodes Executed | Sentiment | Credibility | Theme Router |
|------|----------------|-----------|-------------|--------------|
| Full | [1, 2, 3, 4, 5, 6, 7] | ✅ | ✅ | ✅ |
| Sentiment | [1, 2, 3, 4, 5, 6, 7] | ✅ | ❌ | ✅ |
| Credibility | [1, 2, 3, 4, 5, 6, 7] | ❌ | ✅ | ✅ |

---

## Implementation Tasks

### Task 1: Update Schema Definition
**File:** `backend/app/schemas/snapshot.py`

**Changes:**
1. Add `include_sentiment` and `include_credibility` boolean fields to `SnapshotRequest`
2. Update mode documentation to reflect all 3 modes: `full`, `sentiment`, `credibility`

**Code Changes:**
```python
class SnapshotRequest(BaseModel):
    platforms: list[str]
    time_window: str = "24h"
    focus_areas: list[str]
    include_alerts: bool = True
    mode: str = Field(default="full", description="Analysis mode: full, sentiment, or credibility")
    include_sentiment: bool = Field(default=True, description="Include sentiment analysis")
    include_credibility: bool = Field(default=True, description="Include credibility scoring")
```

---

### Task 2: Update Graph Mode Logic
**File:** `backend/app/services/insights/graph.py`

**Changes:**
1. Update mode detection logic (lines 97-128)
2. Add state flags for `include_sentiment` and `include_credibility`
3. Ensure both sentiment and credibility modes execute all nodes 1-7

**Code Changes:**
```python
mode = request.mode.lower()
if mode == "sentiment":
    # Full pipeline, no credibility
    execute_nodes = [1, 2, 3, 4, 5, 6, 7]
    state["include_credibility"] = False
    state["include_sentiment"] = True
elif mode == "credibility":
    # Full pipeline, no sentiment
    execute_nodes = [1, 2, 3, 4, 5, 6, 7]
    state["include_credibility"] = True
    state["include_sentiment"] = False
else:  # full
    # Full pipeline, both enabled
    execute_nodes = [1, 2, 3, 4, 5, 6, 7]
    state["include_credibility"] = True
    state["include_sentiment"] = True
```

---

### Task 3: Update Node 4 - Conditional Analysis
**File:** `backend/app/services/insights/nodes.py`

**Changes:**
1. Modify `label_sentiment_and_analyze()` function to read state flags
2. Conditionally execute sentiment and credibility analysis
3. Theme router always runs regardless of flags
4. Handle missing data gracefully when analysis is skipped

**Code Changes:**
```python
async def label_sentiment_and_analyze(state: SnapshotState) -> SnapshotState:
    request = state["request"]
    include_sentiment = state.get("include_sentiment", True)
    include_credibility = state.get("include_credibility", True)
    
    async def run_sentiment():
        if not include_sentiment:
            # Return docs with placeholder sentiment
            logger.info("[Node4] Sentiment skipped (sentiment mode disabled)")
            return [doc.model_copy(update={"sentiment": "neutral"}) for doc in docs]
        # ... existing sentiment logic
    
    async def run_credibility():
        if not include_credibility:
            # Return unscored docs
            logger.info("[Node4] Credibility skipped (credibility mode disabled)")
            return [doc.model_copy(update={
                "metadata": {**(doc.metadata or {}), "credibility_score": None}
            }) for doc in docs]
        # ... existing credibility logic
    
    async def run_theme_router():
        # Theme router ALWAYS runs
        # ... existing logic
        return theme_docs
    
    # Execute based on flags (theme ALWAYS runs)
    tasks = [run_theme_router()]
    if include_sentiment:
        tasks.append(run_sentiment())
    if include_credibility:
        tasks.append(run_credibility())
    
    results = await asyncio.gather(*tasks)
    
    # Reconstruct state
    theme_docs = results[0]
    sentiment_docs = None
    credibility_docs = None
    
    idx = 1
    if include_sentiment:
        sentiment_docs = results[idx]
        idx += 1
    if include_credibility:
        credibility_docs = results[idx]
    
    # Merge logic handles None cases
    enriched_docs = []
    for i in range(len(docs)):
        s_doc = sentiment_docs[i] if sentiment_docs else docs[i]
        c_doc = credibility_docs[i] if credibility_docs else docs[i]
        
        # Merge metadata
        merged_metadata = {**(c_doc.metadata or {}), **(s_doc.metadata or {})}
        
        enriched = c_doc.model_copy(update={
            "sentiment": s_doc.sentiment,
            "metadata": merged_metadata
        })
        enriched_docs.append(enriched)
    
    state["enriched"] = enriched_docs
    state["theme_documents"] = theme_docs
    return state
```

---

### Task 4: Update Progress Callbacks (Optional)
**File:** `backend/app/services/insights/graph.py`

**Changes:**
1. Update progress stage messages to reflect mode-specific analysis

**Code Changes:**
```python
if mode == "sentiment":
    progress_stages = [
        ("query_orchestrator", "📡 Query Orchestrator: Generating search queries...", 0.1),
        ("retrieval", "🔍 Retrieval Agent: Fetching documents...", 0.2),
        ("recall", "🧠 Internal Retrieval: Recalling memory...", 0.3),
        ("analyze", "⚡ Analyzing: Sentiment + Theme Routing...", 0.5),
        ("memory", "💾 Memory: Consolidating new knowledge...", 0.7),
        ("themes", "🎯 Theme Agents: Generating insights...", 0.9),
        ("snapshot", "📊 Building Snapshot Response...", 1.0),
    ]
elif mode == "credibility":
    progress_stages = [
        ("query_orchestrator", "📡 Query Orchestrator: Generating search queries...", 0.1),
        ("retrieval", "🔍 Retrieval Agent: Fetching documents...", 0.2),
        ("recall", "🧠 Internal Retrieval: Recalling memory...", 0.3),
        ("analyze", "⚡ Analyzing: Credibility + Theme Routing...", 0.5),
        ("memory", "💾 Memory: Consolidating new knowledge...", 0.7),
        ("themes", "🎯 Theme Agents: Generating insights...", 0.9),
        ("snapshot", "📊 Building Snapshot Response...", 1.0),
    ]
else:  # full
    progress_stages = [
        ("query_orchestrator", "📡 Query Orchestrator: Generating search queries...", 0.1),
        ("retrieval", "🔍 Retrieval Agent: Fetching documents...", 0.2),
        ("recall", "🧠 Internal Retrieval: Recalling memory...", 0.3),
        ("analyze", "⚡ Analyzing: Sentiment + Credibility + Theme...", 0.5),
        ("memory", "💾 Memory: Consolidating new knowledge...", 0.7),
        ("themes", "🎯 Theme Agents: Generating insights...", 0.9),
        ("snapshot", "📊 Building Snapshot Response...", 1.0),
    ]
```

---

### Task 5: Update Frontend Integration (If Needed)
**Files:** `frontend/src/features/sentiment/components/sentiment-generator-page.tsx`

**Changes:**
1. Ensure mode selector includes `credibility` option
2. Pass correct mode parameter in API requests

---

## Testing Plan

### Unit Tests
1. Test mode detection in `graph.py`
2. Test Node 4 conditional execution
3. Test metadata merging with None values

### Integration Tests
1. Test `mode=full` returns both sentiment and credibility
2. Test `mode=sentiment` returns sentiment but no credibility score
3. Test `mode=credibility` returns credibility but neutral sentiment
4. Test all modes execute full pipeline (nodes 1-7)

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/schemas/snapshot.py` | Add `include_sentiment`, `include_credibility` fields |
| `backend/app/services/insights/graph.py` | Update mode logic, add state flags, update progress stages |
| `backend/app/services/insights/nodes.py` | Modify Node 4 to conditionally execute analysis |
| `frontend/src/features/sentiment/...` | Add credibility mode option (if needed) |

---

## Estimated Effort

| Task | Complexity | Time Estimate |
|------|------------|---------------|
| Task 1: Schema Update | Low | 10 minutes |
| Task 2: Graph Mode Logic | Low | 15 minutes |
| Task 3: Node 4 Conditional | Medium | 30 minutes |
| Task 4: Progress Callbacks | Low | 10 minutes |
| Task 5: Frontend | Low | 15 minutes |
| **Total** | - | **~1.5 hours** |

---

## Validation Checklist

- [ ] Sentiment mode runs all 7 nodes
- [ ] Sentiment mode includes sentiment analysis
- [ ] Sentiment mode excludes credibility scoring
- [ ] Sentiment mode includes theme routing
- [ ] Credibility mode runs all 7 nodes
- [ ] Credibility mode excludes sentiment analysis
- [ ] Credibility mode includes credibility scoring
- [ ] Credibility mode includes theme routing
- [ ] Full mode unchanged (both analysis types)
- [ ] All tests pass
