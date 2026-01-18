# Evaluation Framework

> **Thesis Title (Option 1):** 7-Node Agentic Graphs: Multi-Signal Fusion for Verified Context-Aware Public Opinion Synthesis
>
> **Thesis Title (Option 2):** Hinaing: A Neuro-Symbolic Multi-Agent Framework for Epistemic Truth Discovery in Civic Social Listening
>
> **Thesis Title (Option 3):** Hinaing: A Context-Engineered Self-Learning Multi-Agent Agentic AI System with Ensemble Sentiment and 5-Signal Credibility for Public Opinion Analysis in Baguio City
>
> **Thesis Title (Unified):** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

> **Thesis Title:** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

This document describes the evaluation methodology for the thesis:
**"Multi-Agentic AI with Real-Time Intelligent Search and RAG for Context-Aware Public Opinion Analysis"**

---

## Research Questions Addressed

| RQ | Question | Evaluation Method |
|----|----------|-------------------|
| RQ3.1 | Task-Specific Metrics (Sentiment) | Accuracy, Precision, Recall, F1, Specificity |
| RQ3.2 | System-Level Metrics (Agentic AI) | AgentEval + Manual Assessment |

---

## RQ3.1: Task-Specific Metrics for Sentiment Analysis

### Metrics Definitions

| Metric | Formula | Description |
|--------|---------|-------------|
| **Accuracy** | (TP + TN) / Total | Overall correctness |
| **Precision** | TP / (TP + FP) | Of predicted positives, how many are correct |
| **Recall (Sensitivity)** | TP / (TP + FN) | Of actual positives, how many were found |
| **Specificity** | TN / (TN + FP) | Of actual negatives, how many were correctly identified |
| **F1 Score** | 2 × (P × R) / (P + R) | Harmonic mean of precision and recall |

### Evaluation Approach

#### 1. Labeled Test Dataset
A manually labeled dataset of civic content from Baguio City sources:
- Minimum 100 samples
- Balanced across positive, negative, neutral
- Sources: news articles, Facebook posts, forum discussions

#### 2. Model Comparison
Three configurations evaluated:
1. **RoBERTa Only** - `twitter-roberta-base-sentiment-latest`
2. **Gemini Only** - `gemini-2.0-flash-exp`
3. **Ensemble** - Weighted voting (40% RoBERTa + 60% Gemini)

#### 3. Expected Results Table

| Model | Accuracy | Precision | Recall | F1 | Specificity |
|-------|----------|-----------|--------|-----|-------------|
| RoBERTa Only | TBD | TBD | TBD | TBD | TBD |
| Gemini Only | TBD | TBD | TBD | TBD | TBD |
| **Ensemble** | TBD | TBD | TBD | TBD | TBD |

---

## RQ3.2: System-Level Metrics for Agentic AI

### Metrics Definitions

| Metric | Description | Evaluation Method |
|--------|-------------|-------------------|
| **Explainability** | System explains WHY decisions were made | AgentEval + Evidence inspection |
| **Transparency** | Users understand HOW the system works | AgentEval + Workflow visibility |
| **User Satisfaction** | End-users find the system useful | Survey (Likert scale 1-5) |
| **Fairness/Bias Mitigation** | System avoids systematic bias | Source diversity analysis |
| **Adaptability/Robustness** | System handles varying inputs gracefully | Stress testing + Failure recovery |

### Evaluation Criteria

#### Explainability (Score 1-5)
| Score | Criteria |
|-------|----------|
| 5 | Every insight has evidence URLs, sentiment shows both model predictions, ReAct logs full reasoning |
| 4 | Most insights have evidence, sentiment confidence shown |
| 3 | Some evidence provided, basic confidence scores |
| 2 | Minimal explanation, no reasoning trace |
| 1 | No explanation of decisions |

**Evidence in System:**
- `evidence` field in each `Insight` object
- `roberta_prediction`, `gemini_prediction` in sentiment metadata
- `intermediate_steps` logged in Query Orchestrator

#### Transparency (Score 1-5)
| Score | Criteria |
|-------|----------|
| 5 | Full workflow visible, all agent decisions traceable |
| 4 | Most workflow visible, key decisions logged |
| 3 | Partial visibility, some black boxes |
| 2 | Limited visibility into processing |
| 1 | Completely opaque system |

**Evidence in System:**
- LangGraph workflow with named nodes
- Per-agent latency logging in `graph.py`
- Sentiment metadata shows `model_agreement` status

#### User Satisfaction (Score 1-5)
| Score | Criteria |
|-------|----------|
| 5 | Highly useful, would recommend to others |
| 4 | Useful, meets most needs |
| 3 | Somewhat useful, has limitations |
| 2 | Limited usefulness |
| 1 | Not useful |

**Evaluation Method:**
- Survey civic leaders / target users
- Likert scale questionnaire
- Minimum 10 respondents

#### Fairness/Bias Mitigation (Score 1-5)
| Score | Criteria |
|-------|----------|
| 5 | Multi-source, ensemble reduces bias, balanced coverage |
| 4 | Multiple sources, some bias mitigation |
| 3 | Limited sources, single model |
| 2 | Single source, potential bias |
| 1 | Clear systematic bias |

**Evidence in System:**
- Multi-platform retrieval (web + Facebook)
- Ensemble voting reduces single-model bias
- 6 theme categories ensure balanced coverage

#### Adaptability/Robustness (Score 1-5)
| Score | Criteria |
|-------|----------|
| 5 | Adapts to all inputs, graceful failure recovery |
| 4 | Adapts to most inputs, handles common failures |
| 3 | Some adaptation, basic error handling |
| 2 | Limited adaptation, fragile |
| 1 | Rigid, fails on edge cases |

**Evidence in System:**
- ReAct query planning adapts to focus areas
- Fallback plan generation when ReAct fails
- Per-agent failure isolation
- Graceful degradation (empty results vs crash)

---

## AgentEval Implementation

### What is AgentEval?
AgentEval is a framework for evaluating agentic AI systems using LLM-as-a-judge. It provides:
1. **CriticAgent** - Generates evaluation criteria
2. **QuantifierAgent** - Scores outputs against criteria

### Evaluation Process

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  System Output  │ ──▶ │  AgentEval LLM  │ ──▶ │  Scores (1-5)   │
│  (Snapshot)     │     │  (Evaluator)    │     │  + Justification│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Evaluation Prompt Template

```
You are evaluating an AI system for civic public opinion analysis.

CRITERION: {criterion_name}
DEFINITION: {criterion_definition}

INDICATORS TO LOOK FOR:
{indicators_list}

SYSTEM OUTPUT:
{snapshot_json}

INSTRUCTIONS:
1. Score from 1-5 based on the criteria above
2. Provide specific evidence from the output
3. Explain your reasoning

OUTPUT FORMAT:
Score: [1-5]
Evidence: [specific examples from output]
Justification: [why this score]
```

---

## Test Dataset Requirements

### Sentiment Test Data
```json
{
  "samples": [
    {
      "id": "001",
      "text": "Baguio City traffic congestion worsens during peak hours",
      "source": "news",
      "ground_truth": "negative",
      "theme": "infrastructure"
    },
    {
      "id": "002", 
      "text": "Panagbenga 2025 attracts record number of tourists",
      "source": "facebook",
      "ground_truth": "positive",
      "theme": "tourism"
    }
  ],
  "metadata": {
    "total_samples": 100,
    "distribution": {
      "positive": 33,
      "negative": 34,
      "neutral": 33
    },
    "sources": ["news", "facebook", "forum"],
    "labelers": 3,
    "inter_annotator_agreement": 0.85
  }
}
```

### Labeling Guidelines
1. **Positive**: Appreciation, success, improvement, good news
2. **Negative**: Complaints, problems, incidents, criticism
3. **Neutral**: Factual announcements, balanced reporting, informational

### Inter-Annotator Agreement
- Minimum 3 labelers per sample
- Use majority voting for final label
- Report Cohen's Kappa or Fleiss' Kappa

---

## Evaluation Scripts

### Location
```
backend/
├── app/
│   └── services/
│       └── evaluation/
│           ├── __init__.py
│           ├── sentiment_eval.py    # RQ3.1 metrics
│           ├── agent_eval.py        # RQ3.2 AgentEval
│           └── run_evaluation.py    # Main evaluation runner
└── tests/
    └── evaluation/
        └── test_data.json           # Labeled test dataset
```

### Running Evaluation
```bash
# Run sentiment metrics evaluation
poetry run python -m app.services.evaluation.run_evaluation --type sentiment

# Run AgentEval system metrics
poetry run python -m app.services.evaluation.run_evaluation --type system

# Run full evaluation
poetry run python -m app.services.evaluation.run_evaluation --type all
```

---

## Expected Outputs

### Sentiment Evaluation Report
```json
{
  "model_comparison": {
    "roberta_only": {
      "accuracy": 0.72,
      "macro_f1": 0.70,
      "per_class": {...}
    },
    "gemini_only": {
      "accuracy": 0.75,
      "macro_f1": 0.73,
      "per_class": {...}
    },
    "ensemble": {
      "accuracy": 0.82,
      "macro_f1": 0.80,
      "per_class": {...}
    }
  },
  "conclusion": "Ensemble outperforms individual models by X%"
}
```

### System Evaluation Report
```json
{
  "system_metrics": {
    "explainability": {"score": 4.2, "justification": "..."},
    "transparency": {"score": 4.0, "justification": "..."},
    "user_satisfaction": {"score": 4.1, "justification": "..."},
    "fairness": {"score": 3.8, "justification": "..."},
    "adaptability": {"score": 4.3, "justification": "..."}
  },
  "overall_score": 4.08,
  "strengths": ["..."],
  "areas_for_improvement": ["..."]
}
```

---

## Timeline

| Week | Task |
|------|------|
| 1 | Create labeled test dataset (100+ samples) |
| 2 | Implement evaluation scripts |
| 3 | Run sentiment metrics evaluation |
| 4 | Run AgentEval system evaluation |
| 5 | Analyze results, write findings |

---

## References

1. **AgentEval**: Microsoft AutoGen framework for agent evaluation
2. **sklearn.metrics**: Standard ML evaluation metrics
3. **LLM-as-Judge**: Using language models for evaluation (Zheng et al., 2023)
4. **Inter-Annotator Agreement**: Cohen's Kappa, Fleiss' Kappa

---

**Last Updated**: December 4, 2025
