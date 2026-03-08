# Sentiment Alignment Fix

## Problem
The overall sentiment summary text was misaligned with the sentiment breakdown percentages:
- **Summary text**: "positive and negative developments"
- **Dashboard**: 0% Negative, 83% Neutral, 17% Positive

This created user confusion - the text mentioned "negative developments" but the chart showed 0% negative.

## Root Cause
**Semantic mismatch** between two different analysis layers:

1. **Sentiment Agent** (Document-level)
   - Classifies individual documents as positive/neutral/negative
   - Factual reporting about negative topics → classified as "neutral"
   - Example: Article about vendor displacement → "neutral" (just reporting facts)

2. **Coordinator Agent** (Theme-level)
   - Writes summary based on content themes
   - Understands negative implications of topics
   - Example: Vendor displacement → "negative development" (understands impact)

3. **Dashboard** (Aggregation)
   - Shows percentages from document sentiments
   - If all docs are "neutral" → 0% negative shown

## Solution Applied

### 1. Pass Sentiment Distribution to Coordinator
Modified the data flow to include sentiment breakdown:

```python
# nodes.py - Calculate sentiment distribution
scores = {
    "negative": counts.get("negative", 0) / total,
    "neutral": counts.get("neutral", 0) / total,
    "positive": counts.get("positive", 0) / total,
}

# Pass to coordinator
summary_text, insights_payload = await coordinator_agent.run(
    window=request.time_window,
    focus_areas=request.focus_areas,
    documents=[doc.model_dump() for doc in docs],
    theme_insights=[i.model_dump() for i in state.get("theme_insights", [])],
    sentiment_distribution=scores,  # NEW: Pass sentiment breakdown
)
```

### 2. Update Coordinator Prompt
Added sentiment distribution context to the prompt:

```
=== SENTIMENT DISTRIBUTION ===
Negative: 0% | Neutral: 83% | Positive: 17%
IMPORTANT: Your concluding paragraph MUST align with this distribution.
- If negative is 0%, DO NOT say 'negative developments' - say 'concerns' or 'challenges' instead
- If neutral is high (>70%), emphasize 'mixed' or 'balanced' sentiment
- Match the tone to the actual sentiment breakdown above
```

### 3. Updated Formatting Requirements
Changed from:
> "Add a concluding paragraph that synthesizes the overall sentiment and key takeaways"

To:
> "Add a concluding paragraph that ACCURATELY reflects the sentiment distribution above"

## Expected Behavior

### Before Fix
- Summary: "positive and negative developments"
- Dashboard: 0% Negative ❌ **MISMATCH**

### After Fix
- Summary: "mixed sentiment with concerns and positive developments"
- Dashboard: 0% Negative, 83% Neutral, 17% Positive ✅ **ALIGNED**

## Example Corrections

| Sentiment Distribution | Old Summary | New Summary |
|------------------------|-------------|-------------|
| 0% Neg, 83% Neu, 17% Pos | "negative developments" | "concerns" or "challenges" |
| 10% Neg, 70% Neu, 20% Pos | "overall positive" | "mixed sentiment" |
| 40% Neg, 40% Neu, 20% Pos | "balanced" | "predominantly negative concerns" |

## Files Modified
1. `backend/app/services/agents/coordinator_agent.py` - Added sentiment_distribution parameter
2. `backend/app/services/insights/nodes.py` - Pass scores to coordinator
3. `backend/app/services/nlp/gemini.py` - Updated prompt with sentiment context

## Testing
Run a query and verify:
1. Check logs for sentiment distribution: `"sentiment_dist": {"positive": 0.17, "neutral": 0.83, "negative": 0.0}`
2. Read the concluding paragraph - should NOT mention "negative developments" if negative is 0%
3. Verify alignment between summary tone and dashboard percentages
