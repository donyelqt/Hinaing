# Comparative Analysis Plan

> **Thesis Title (Option 1):** 7-Node Agentic Graphs: Multi-Signal Fusion for Verified Context-Aware Public Opinion Synthesis
>
> **Thesis Title (Option 2):** Hinaing: A Neuro-Symbolic Multi-Agent Framework for Epistemic Truth Discovery in Civic Social Listening
>
> **Thesis Title (Option 3):** Hinaing: A Context-Engineered Self-Learning Multi-Agent Agentic AI System with Ensemble Sentiment and 5-Signal Credibility for Public Opinion Analysis in Baguio City
>
> **Thesis Title (Unified):** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

> **Thesis Title:** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

This document outlines the experimental design for comparing system configurations to validate the thesis contributions.

**Thesis Title:** Multi-Agentic AI with Real-Time Intelligent Search and RAG for Context-Aware Public Opinion Analysis

---

## Overview

We will run the same test inputs through different system configurations to measure the impact of each component.

| Experiment | What We Compare | What It Proves |
|------------|-----------------|----------------|
| A | Ensemble vs Single Model | Ensemble sentiment is more accurate |
| B | With RAG vs Without RAG | RAG improves insight quality |
| C | ReAct vs Static Queries | Adaptive query planning improves retrieval |
| D | Multi-Agent vs Single Prompt | Multi-agent is faster and more reliable |

---

## Experiment A: Sentiment Model Comparison

### Objective
Prove that ensemble sentiment (RoBERTa + Gemini) outperforms individual models.

### Configurations

| Config | Description | Code Change |
|--------|-------------|-------------|
| A1 | RoBERTa Only | Use only `roberta.predict_batch_with_probs()` |
| A2 | Gemini Only | Use only `_gemini_analyze_all()` |
| A3 | Ensemble (Current) | Weighted voting (40% RoBERTa + 60% Gemini) |

### Metrics
- Accuracy
- Precision (per class)
- Recall (per class)
- F1 Score (per class)
- Specificity (per class)

### Test Data
- 100+ labeled civic sentiment samples
- Balanced: ~33 positive, ~34 negative, ~33 neutral
- Sources: news, Facebook, forums about Baguio City

### Expected Results (Not official)

| Config | Expected Accuracy | Rationale |
|--------|-------------------|-----------|
| A1 (RoBERTa) | ~70-75% | Good on social media, weak on formal news |
| A2 (Gemini) | ~72-78% | Good context understanding, inconsistent |
| A3 (Ensemble) | ~80-85% | Combines strengths of both |

### Implementation

```python
# backend/app/services/evaluation/sentiment_comparison.py

async def run_sentiment_comparison(test_data: list[dict]):
    results = {
        "roberta_only": [],
        "gemini_only": [],
        "ensemble": []
    }
    
    for item in test_data:
        doc = WebDocument(title=item["text"], snippet="", url="")
        
        # A1: RoBERTa only
        roberta_pred = roberta_model.predict_batch_with_probs([item["text"]])[0]
        results["roberta_only"].append(max(roberta_pred, key=roberta_pred.get))
        
        # A2: Gemini only
        gemini_pred = sentiment_agent._gemini_batch_with_probs([doc])[0]
        results["gemini_only"].append(max(gemini_pred, key=gemini_pred.get))
        
        # A3: Ensemble
        ensemble_result = sentiment_agent.analyze_batch([doc])
        results["ensemble"].append(ensemble_result[0].sentiment)
    
    return results
```

---

## Experiment B: RAG Impact Analysis

### Objective
Prove that RAG-augmented context improves theme insight quality.

### Configurations

| Config | Description | Code Change |
|--------|-------------|-------------|
| B1 | Without RAG | Skip `augment_context` node, pass empty contexts |
| B2 | With RAG (Current) | Full pipeline with RAG augmentation |

### Metrics
- Insight relevance score (1-5, human evaluation)
- Evidence quality (valid URLs, relevant sources)
- Context coverage (themes addressed)

### Test Scenarios
- 10 different snapshot requests
- Various focus areas (tourism, health, safety, etc.)
- Different time windows (24h, 7d)

### Expected Results

| Config | Expected Quality | Rationale |
|--------|------------------|-----------|
| B1 (No RAG) | 3.0-3.5/5 | Generic insights, less grounded |
| B2 (With RAG) | 4.0-4.5/5 | Specific, evidence-backed insights |

### Implementation

```python
# backend/app/services/evaluation/rag_comparison.py

async def run_rag_comparison(requests: list[SnapshotRequest]):
    results = []
    
    for request in requests:
        # B1: Without RAG
        snapshot_no_rag = await generate_snapshot(request, skip_rag=True)
        
        # B2: With RAG
        snapshot_with_rag = await generate_snapshot(request, skip_rag=False)
        
        results.append({
            "request": request.model_dump(),
            "no_rag": snapshot_no_rag.model_dump(),
            "with_rag": snapshot_with_rag.model_dump()
        })
    
    return results

# Add flag to graph.py
async def augment_context(state: SnapshotState) -> SnapshotState:
    if state.get("skip_rag"):
        state["augmented_contexts"] = {}
        return state
    # ... existing RAG logic
```

### Evaluation Rubric

| Score | Criteria |
|-------|----------|
| 5 | Highly relevant, specific to Baguio, actionable, well-evidenced |
| 4 | Relevant, mostly specific, good evidence |
| 3 | Somewhat relevant, generic, limited evidence |
| 2 | Marginally relevant, very generic |
| 1 | Irrelevant or incorrect |

---

## Experiment C: Query Planning Comparison

### Objective
Prove that ReAct-based query planning improves retrieval quality over static queries.

### Configurations

| Config | Description | Code Change |
|--------|-------------|-------------|
| C1 | Static Queries | Use `_fallback_plan()` directly |
| C2 | ReAct Planning (Current) | Full ReAct reasoning loop |

### Metrics
- Query relevance score (1-5)
- Document retrieval precision
- Coverage of focus areas

### Test Scenarios
- 10 different focus area combinations
- Various time windows

### Expected Results

| Config | Expected Relevance | Rationale |
|--------|-------------------|-----------|
| C1 (Static) | 3.5/5 | Generic queries, may miss nuances |
| C2 (ReAct) | 4.2/5 | Adaptive, considers context |

### Implementation

```python
# backend/app/services/evaluation/query_comparison.py

def run_query_comparison(requests: list[SnapshotRequest]):
    results = []
    
    for request in requests:
        # C1: Static (fallback) queries
        static_plan = orchestrator._fallback_plan(
            request.focus_areas or ["public services"],
            request.time_window or "24h"
        )
        
        # C2: ReAct queries
        react_plan = orchestrator.run(request)
        
        results.append({
            "request": request.model_dump(),
            "static_queries": [q.query for q in static_plan.queries],
            "react_queries": [q.query for q in react_plan.queries],
            "react_strategy": react_plan.strategy
        })
    
    return results
```

---

## Experiment D: Architecture Comparison

### Objective
Prove that multi-agent architecture provides benefits over single-prompt approach.

### Configurations

| Config | Description | Approach |
|--------|-------------|----------|
| D1 | Single Prompt | One LLM call with all instructions |
| D2 | Multi-Agent (Current) | 7 specialized agents |

### Metrics
- Total latency
- Failure rate
- Output quality

### Expected Results

| Config | Latency | Failure Rate | Quality |
|--------|---------|--------------|---------|
| D1 (Single) | ~45-60s | Higher (all-or-nothing) | 3.5/5 |
| D2 (Multi) | ~30-40s | Lower (isolated failures) | 4.2/5 |

### Implementation

```python
# backend/app/services/evaluation/architecture_comparison.py

async def run_single_prompt_baseline(request: SnapshotRequest):
    """Single prompt approach for comparison."""
    prompt = f"""
    You are a civic intelligence system for Baguio City.
    
    Task: Analyze public opinion for the following:
    - Focus areas: {request.focus_areas}
    - Time window: {request.time_window}
    
    Steps:
    1. Generate search queries
    2. Analyze sentiment of results
    3. Check source credibility
    4. Route by theme
    5. Generate insights
    
    Return JSON with overall_sentiment, actionable_insights, alerts.
    """
    
    # Single LLM call
    response = await gemini_client.generate(prompt)
    return parse_response(response)
```

---

## Execution Timeline

| Day | Task | Output |
|-----|------|--------|
| 1 | Create labeled test dataset (100 samples) | `test_data.json` |
| 2 | Implement Experiment A (sentiment comparison) | Accuracy/F1 table |
| 3 | Implement Experiment B (RAG comparison) | Quality scores |
| 4 | Implement Experiment C (query comparison) | Relevance scores |
| 5 | Implement Experiment D (architecture comparison) | Latency/quality table |
| 6 | Analyze results, create visualizations | Charts, tables |
| 7 | Write findings section | Thesis chapter draft |

---

## Required Test Data

### Sentiment Test Dataset
```json
{
  "samples": [
    {"id": "001", "text": "...", "ground_truth": "positive"},
    {"id": "002", "text": "...", "ground_truth": "negative"},
    ...
  ]
}
```

### Snapshot Test Requests
```json
{
  "requests": [
    {
      "focus_areas": ["tourism"],
      "time_window": "24h",
      "platforms": ["web", "facebook"]
    },
    {
      "focus_areas": ["health", "safety"],
      "time_window": "7d",
      "platforms": ["web"]
    },
    ...
  ]
}
```

---

## Output Format

### Results Table (Example)

| Experiment | Config | Metric | Value |
|------------|--------|--------|-------|
| A | RoBERTa Only | Accuracy | 0.72 |
| A | Gemini Only | Accuracy | 0.75 |
| A | Ensemble | Accuracy | 0.82 |
| B | Without RAG | Quality | 3.2/5 |
| B | With RAG | Quality | 4.3/5 |
| C | Static Queries | Relevance | 3.5/5 |
| C | ReAct Queries | Relevance | 4.1/5 |
| D | Single Prompt | Latency | 52s |
| D | Multi-Agent | Latency | 35s |

### Visualization
- Bar charts comparing configurations
- Confusion matrices for sentiment
- Latency distribution plots

---

## Files to Create

```
backend/
├── app/
│   └── services/
│       └── evaluation/
│           ├── __init__.py
│           ├── sentiment_comparison.py   # Experiment A
│           ├── rag_comparison.py         # Experiment B
│           ├── query_comparison.py       # Experiment C
│           ├── architecture_comparison.py # Experiment D
│           └── run_all.py                # Main runner
└── tests/
    └── evaluation/
        ├── test_data.json                # Labeled sentiment data
        └── test_requests.json            # Snapshot requests
```

---

## Success Criteria

| Experiment | Success If |
|------------|------------|
| A | Ensemble accuracy > both individual models |
| B | With RAG quality score > Without RAG by ≥0.5 |
| C | ReAct relevance > Static by ≥0.3 |
| D | Multi-agent latency ≤ Single prompt AND quality higher |

---

**Last Updated:** December 4, 2025
