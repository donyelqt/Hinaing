# Semantic Relevance Threshold Fix

## Problem
Mallification-related documents were being filtered out due to overly strict semantic relevance threshold (0.40), resulting in 0 documents returned for "mallification protest" queries.

### Example Filtered Documents
- **Japanese article** about SM Baguio: scored **0.23** (filtered at 0.40 threshold)
- **Filipino content** about mallification: scored **0.36** (filtered at 0.40 threshold)

### Root Cause
LangSearch's semantic reranker struggles with:
1. **Multilingual content** (Japanese, Filipino articles)
2. **Different terminology** (e.g., "SM expansion" vs "mallification")
3. **Cross-lingual semantic matching** (English query → Japanese/Filipino content)

## Solution Applied

### Threshold Adjustment
Lowered semantic relevance thresholds to accommodate multilingual content:

| Query Type | Old Threshold | New Threshold | Rationale |
|------------|---------------|---------------|-----------|
| Orchestrator | 0.40 → **0.25** | **0.25** | Captures Filipino articles (score 0.36), conservative filter |
| Baseline | 0.30 → **0.20** | **0.20** | Broader search, more permissive |

### Why 0.25?
- Filipino mallification content scored **0.36** (well above threshold) ✅
- Japanese content scored **0.23** (borderline, may be filtered) ⚠️
- Provides good balance between precision and recall
- More conservative than 0.22, filters out very low-relevance content

### Additional Improvements
1. **Added logging** for sample relevance scores after reranking
2. **Double reranking** against orchestrator query for accuracy
3. **Documented** multilingual scoring behavior in code comments

## Expected Behavior
- Mallification documents in **Filipino** (0.36) → ✅ **PASS** (above 0.25)
- Mallification documents in **Japanese** (0.23) → ⚠️ **BORDERLINE** (below 0.25)
- Completely irrelevant documents (< 0.20) → ❌ **FILTERED**

## Testing
Run a query with `focus_area=economy` and check logs for:
```
[search] Sample relevance scores after rerank: [0.36, 0.28, ...]
[search] Filtered X low-relevance docs (Y/Z kept, threshold: 0.25)
```

Filipino mallification documents should now appear in results.

## Files Modified
- `backend/app/services/insights/agent_tools.py` (threshold: 0.40 → 0.25)

