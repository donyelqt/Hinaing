# Bug Fix: Unbalanced Insight Generation (Health vs Economy)

## Problem Statement
The system was only returning health-related insights even when the query included both `health` and `economy` focus areas. All 3 insights were about gastroenteritis/healthcare, with no economy/tourism coverage.

## Root Cause Analysis

### What Was Working ✅
1. **Document Retrieval**: Successfully fetched 24 documents
2. **Theme Routing**: Correctly routed documents to all 3 themes:
   - `Health & Safety` - 24 docs
   - `Infrastructure & Environment` - 6 docs  
   - `Tourism & Economy` - 24 docs
3. **Theme Agents**: All 3 theme agents completed successfully and generated balanced insights
4. **RAG Augmentation**: Context augmentation worked for all themes

### The Bug ❌
Located in `graph.py` lines 603-644 (`build_snapshot` function):

**Issue 1: Insight Priority Logic**
```python
# BEFORE (buggy)
if insights_payload:  # Gemini insights
    # Use Gemini insights (unbalanced)
else:
    theme_fallbacks = state.get("theme_insights")
    if theme_fallbacks:
        # Only use theme insights as fallback
```

**Why it failed:**
- When Gemini is available, it receives ALL 24 documents mixed together
- Gemini analyzes documents without theme separation
- With 18/24 documents about health, Gemini naturally focused on the dominant topic
- The well-balanced theme insights were ignored

**Issue 2: Weak Gemini Prompt**
The prompt didn't enforce balanced coverage across focus areas:
```python
# BEFORE
"Produce a JSON object with keys summary (<=2 sentences) and insights (array of up to 3 items)."
```

No instruction to ensure at least one insight per focus area.

## The Fix ✅

### Change 1: Prioritize Theme Insights (`graph.py`)
```python
# AFTER (fixed)
if theme_fallbacks:
    # Primary: Use theme insights (already balanced by theme routing)
    insights.extend(theme_fallbacks[:3])
elif insights_payload:
    # Secondary: Use Gemini insights if no theme insights
    # (fallback for edge cases)
else:
    # Last resort: Generate from focus areas
```

**Rationale:**
- Theme insights are generated per-theme, ensuring balanced coverage
- Each theme agent only sees documents relevant to its theme
- Natural defense against topic dominance

### Change 2: Enhanced Gemini Prompt (`gemini.py`)
```python
# AFTER (improved)
f" IMPORTANT: Generate at least one insight for EACH focus area ({focus})."
" Ensure balanced coverage - do not focus only on the most common topic."
```

**Rationale:**
- If Gemini is used, it now has explicit instructions to balance coverage
- Defense-in-depth: both prompt and logic prevent imbalance

### Change 3: Strict Theme Filtering (`graph.py`)
Added logic to `augment_context` and `theme_agents` to strictly filter themes based on `focus_areas`.

### Change 4: Structural Alignment with Frontend (`graph.py`)
Refactored `THEME_GROUPS` to split the 3 broad themes into 6 distinct categories matching the frontend choices:
- `infrastructure`
- `health` (Health & Wellness)
- `safety` (Public Safety)
- `tourism` (Tourism & Events)
- `economy` (Business & Economy)
- `environment`

**Rationale:**
- Ensures precise mapping between user selection and backend processing
- Prevents cross-contamination (e.g., crime news appearing in health insights)
- Allows for more targeted keyword matching

## Expected Behavior After Fix

Given 24 docs (18 health, 6 economy) and focus `['infrastructure', 'economy']`:

**Before:** 
- Health & Safety (Unrequested) ❌
- Tourism & Economy ✓
- Infrastructure & Environment ✓

**After:**
- Business & Economy ✓
- Infrastructure ✓
- (No Health, Safety, Tourism, or Environment insights) ✅

## Testing Recommendations

1. **Verify balanced output:**
   ```bash
   # Run the API and check insights
   curl -X POST http://localhost:8000/insights/snapshot \
     -H "Content-Type: application/json" \
     -d '{
       "platforms": ["web"],
       "focus_areas": ["health", "economy"],
       "time_window": "1w"
     }' | jq '.actionable_insights[].category'
   ```
   
   Should show mix of categories, not just "Health & Safety"

2. **Check logs:**
   Look for: `[snapshot] Using X theme-generated insights`
   Should no longer see insights being overridden

3. **Edge case - no theme insights:**
   If theme agents fail, Gemini insights still work as backup

## Files Modified

1. `backend/app/services/insights/graph.py`
   - Lines 592-644: Reversed priority (theme insights → Gemini → fallback)
   - Lines 176-184: Added theme filtering to `augment_context`
   - Lines 499-508: Added theme filtering to `theme_agents`
   - Lines 67-114: Refactored `THEME_GROUPS` to 6 categories
   - Line 514: Increased `max_workers` to 6

2. `backend/app/services/nlp/gemini.py`
   - Lines 136-147: Enhanced prompt with balance requirements

## Complexity Assessment

**Complexity: 8/10**

Why this was subtle:
- The bug was in control flow logic, not individual components
- All components worked correctly in isolation
- Required understanding the full pipeline to diagnose
- The fix required changing priorities AND enforcing strict filtering

## Additional Notes

- The theme routing algorithm (`route_documents_by_theme`) uses both focus matching and keyword matching, which is why health docs can appear in multiple themes
- Documents can belong to multiple themes (e.g., "hospital construction" → both health and infrastructure)
- The RAG augmentation further enriches each theme with relevant chunks, improving insight quality
- **New Behavior**: If a user selects specific focus areas, ONLY those themes will generate insights. If no focus areas are selected, ALL themes are candidates.
- **Compatibility**: Verified that `ContextAugmentationAgent` in `context_agent.py` already uses theme labels ("Health & Wellness", "Public Safety", etc.) that match the new `THEME_GROUPS` structure, ensuring seamless RAG integration.
- **Hot-Reload Resilience**: Modified `graph.py` to use `agent_tools.THEME_GROUPS` as the single source of truth. This prevents "split-brain" issues during server reloads where the router (using shared state) and the graph logic (using local state) might temporarily diverge, causing "0 themes" errors.
- **Increased Coverage**: Increased the number of documents analyzed per theme from 5 to 25. This ensures that the AI considers a broader range of sources when generating insights, rather than just the top few.
- **Code Cleanup**: Removed a duplicate, outdated definition of `THEME_GROUPS` in `graph.py` that was causing the local module state to be overwritten with old keys, which was the root cause of the split-brain behavior.
