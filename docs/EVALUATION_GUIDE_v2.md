# Evaluation Methodology v2.0

## Overview

This document outlines the evaluation framework for validating the Multi-Agentic AI system with real-time intelligent search and RAG for context-aware public opinion analysis.

## 1. Research Questions

| RQ | Question |
|----|----------|
| RQ1 | How accurate is the ensemble sentiment analysis compared to single-model approaches in multi-agent system? |
| RQ2 | Does RAG-based context augmentation improve insight quality? |
| RQ3 | How does multi-agent orchestration affect system performance and output coherence? |
| RQ4 | Is the system useful for civic decision-makers in Baguio City? |

## 2. Evaluation Metrics

### 2.1 Sentiment Analysis Accuracy

| Metric | Formula | Target |
|--------|---------|--------|
| Accuracy | (TP + TN) / Total | ≥ 85% |
| Precision | TP / (TP + FP) | ≥ 80% per class |
| Recall | TP / (TP + FN) | ≥ 80% per class |
| F1-Score | 2 × (P × R) / (P + R) | ≥ 80% |
| Cohen's Kappa | Agreement beyond chance | ≥ 0.7 |

### 2.2 RAG Quality Metrics

| Metric | Description | Measurement |
|--------|-------------|-------------|
| Relevance Score | Cosine similarity of retrieved chunks | Average ≥ 0.6 |
| Context Precision | % of retrieved chunks actually relevant | ≥ 70% |
| Context Recall | % of relevant chunks retrieved | ≥ 60% |
| Groundedness | Insights traceable to source documents | ≥ 90% |

### 2.3 System Performance

| Metric | Description | Target |
|--------|-------------|--------|
| End-to-End Latency | Request to response time | < 60 seconds |
| Per-Agent Latency | Individual agent execution time | Logged per stage |
| Throughput | Requests per minute | ≥ 5 RPM |
| Error Rate | Failed requests / total | < 5% |

### 2.4 User Satisfaction (SUS)

System Usability Scale questionnaire for civic stakeholders:
- 10 questions, 5-point Likert scale
- Target SUS score: ≥ 70 (acceptable)

## 3. Baseline Comparisons

### 3.1 Sentiment Analysis Baselines

| Configuration | Description |
|---------------|-------------|
| **Baseline A** | RoBERTa only (no Gemini) |
| **Baseline B** | Gemini only (no RoBERTa) |
| **Baseline C** | VADER rule-based |
| **Proposed** | Ensemble (40% RoBERTa + 60% Gemini) |

### 3.2 RAG Ablation Study

| Configuration | Description |
|---------------|-------------|
| **No RAG** | Theme agents receive raw documents only |
| **Basic RAG** | Fixed chunking (no semantic) |
| **Full RAG** | Semantic chunking + embeddings + vector search |

### 3.3 Agent Architecture Comparison

| Configuration | Description |
|---------------|-------------|
| **Single Agent** | One LLM handles all tasks |
| **Pipeline (no agents)** | Sequential functions, no agent reasoning |
| **Multi-Agent** | Full LangGraph orchestration with specialized agents |

## 4. Dataset Requirements

### 4.1 Ground Truth Dataset

Create a labeled dataset of Baguio City civic posts:

| Field | Description |
|-------|-------------|
| text | Original post/article content |
| source | Platform (Facebook, Web, Reddit) |
| sentiment_label | negative / neutral / positive |
| theme_label | infrastructure / health / safety / tourism / economy / environment |
| annotator_id | Human annotator identifier |
| timestamp | Date of post |

**Target size**: 500-1000 labeled samples
**Inter-annotator agreement**: Cohen's Kappa ≥ 0.7

### 4.2 Annotation Guidelines

```
SENTIMENT LABELS:
- Negative: Complaints, concerns, criticism, problems, dissatisfaction
- Neutral: Factual reporting, announcements, questions without opinion
- Positive: Praise, appreciation, success stories, optimism

THEME LABELS:
- Infrastructure: Roads, traffic, water, power, construction
- Health: Hospitals, diseases, medical services, wellness
- Safety: Crime, accidents, emergencies, disasters
- Tourism: Hotels, festivals, visitors, attractions
- Economy: Markets, businesses, prices, employment
- Environment: Pollution, waste, weather, nature
```

## 5. Experimental Design

### 5.1 Experiment 1: Sentiment Accuracy

**Objective**: Compare ensemble vs single-model sentiment accuracy

**Method**:
1. Run all baselines on ground truth dataset
2. Calculate accuracy, precision, recall, F1 per class
3. Statistical significance test (McNemar's test)

**Expected Output** (Not Official): 
```
| Model          | Accuracy | F1-Neg | F1-Neu | F1-Pos |
|----------------|----------|--------|--------|--------|
| VADER          | 0.65     | 0.60   | 0.55   | 0.70   |
| RoBERTa Only   | 0.78     | 0.75   | 0.72   | 0.82   |
| Gemini Only    | 0.82     | 0.80   | 0.78   | 0.85   |
| Ensemble       | 0.87     | 0.85   | 0.82   | 0.89   |
```

### 5.2 Experiment 2: RAG Impact

**Objective**: Measure insight quality with/without RAG

**Method**:
1. Generate insights for same documents with RAG on/off
2. Human evaluation of insight quality (1-5 scale):
   - Relevance: Does insight match the theme?
   - Specificity: Is insight actionable?
   - Groundedness: Can insight be traced to sources?
3. Compare average scores

**Expected Output**:
```
| Configuration | Relevance | Specificity | Groundedness |
|---------------|-----------|-------------|--------------|
| No RAG        | 3.2       | 2.8         | 2.5          |
| Basic RAG     | 3.8       | 3.5         | 3.8          |
| Full RAG      | 4.3       | 4.1         | 4.5          |
```

### 5.3 Experiment 3: Performance Benchmarking

**Objective**: Measure system latency and throughput

**Method**:
1. Run 50 snapshot requests with varying focus areas
2. Log per-agent latency from telemetry
3. Calculate mean, median, p95 latency

**Expected Output**:
```
| Stage                  | Mean (ms) | P95 (ms) |
|------------------------|-----------|----------|
| Query Orchestrator     | 3500      | 5000     |
| Retrieval Agent        | 2000      | 3500     |
| Sentiment Agent        | 4000      | 6000     |
| Analyze Enriched       | 1500      | 2500     |
| Context Augmentation   | 800       | 1200     |
| Theme Agents           | 5000      | 8000     |
| Build Snapshot         | 2000      | 3500     |
| **Total**              | 18800     | 29700    |
```

### 5.4 Experiment 4: User Study

**Objective**: Evaluate system usability with civic stakeholders

**Participants**: 10-15 Baguio City government employees or civic leaders

**Method**:
1. Brief demo of the system (10 min)
2. Hands-on task: Generate 3 sentiment snapshots (15 min)
3. Complete SUS questionnaire
4. Semi-structured interview (10 min)

**Interview Questions**:
1. How useful are the sentiment insights for your work?
2. Do you trust the system's analysis? Why/why not?
3. What features would you add or change?
4. Would you use this system regularly?

## 6. Statistical Analysis

### 6.1 Significance Tests

| Comparison | Test | Threshold |
|------------|------|-----------|
| Sentiment accuracy | McNemar's test | p < 0.05 |
| RAG quality scores | Wilcoxon signed-rank | p < 0.05 |
| Latency differences | Mann-Whitney U | p < 0.05 |

### 6.2 Effect Size

Report Cohen's d for continuous metrics:
- Small: d = 0.2
- Medium: d = 0.5
- Large: d = 0.8

## 7. Threats to Validity

### 7.1 Internal Validity

| Threat | Mitigation |
|--------|------------|
| Annotator bias | Multiple annotators, inter-rater agreement |
| Data leakage | Separate train/test splits if fine-tuning |
| Order effects | Randomize experiment order |

### 7.2 External Validity

| Threat | Mitigation |
|--------|------------|
| Domain specificity | Acknowledge Baguio City focus, discuss generalizability |
| Temporal bias | Include data from multiple time periods |
| Platform bias | Balance sources (Facebook, Web, Reddit) |

### 7.3 Construct Validity

| Threat | Mitigation |
|--------|------------|
| Metric selection | Use established metrics (F1, SUS) |
| Ground truth quality | Annotation guidelines, agreement thresholds |

## 8. Deliverables

| Deliverable | Description |
|-------------|-------------|
| Labeled Dataset | 500+ annotated civic posts |
| Confusion Matrices | Per-model sentiment classification |
| Latency Logs | Per-agent timing data |
| SUS Results | User satisfaction scores |
| Statistical Report | Significance tests, effect sizes |

## 9. Timeline

| Week | Activity |
|------|----------|
| 1-2 | Dataset collection and annotation |
| 3 | Baseline implementation and testing |
| 4 | Run experiments 1-3 |
| 5 | User study recruitment and execution |
| 6 | Statistical analysis and report writing |

## 10. Ethical Considerations

- **Informed Consent**: User study participants sign consent forms
- **Data Privacy**: Anonymize personal information in civic posts
- **Transparency**: Disclose AI-generated nature of insights
- **Bias Awareness**: Acknowledge potential biases in training data and models
