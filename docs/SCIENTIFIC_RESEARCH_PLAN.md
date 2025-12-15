# Scientific Research Transformation Plan
**Status**: Draft
**Facilitator**: Google Deepmind 100x CTO Agent

## 1. Executive Summary
The Hinaing system currently exists as a **defensible engineering prototype**. To transform it into a **scientific research instrument**, we must shift focus from "feature implementation" to "empirical validation". 

The core research contribution is the **7-Node Self-Learning Cognitive Architecture**, specifically its application to hyper-local civic situational awareness. This plan outlines the steps to rigorously prove its superiority over generalist LLM baselines.

## 2. Gap Analysis: System vs. Science

| Component | Current State (Engineering) | Required State (Science) | Gap |
|-----------|----------------------------|--------------------------|-----|
| **Data** | Live scraping (dynamic) | Static, versioned benchmarks (static) | **Critical**: Cannot reproduce results if data changes every minute. |
| **Validation** | "It looks good" / User feedback | Quantitative Metrics (F1-score, Precision @ k) | **Critical**: Need a "Gold Standard" dataset. |
| **Baselines** | Implicit comparison to ChatGPT | Explicit, automated side-by-side execution | **High**: Need scripts to run System vs. Vanilla GPT-4 vs. Vanilla Gemini. |
| **Latency** | "Feels fast enough" | "P95 latency = 4.2s (σ=0.5)" | **Medium**: Need structured telemetry logs. |
| **Reliability** | Error logs | Failure analysis & Ablation studies | **Medium**: Need to test "What if RAG fails?", "What if Memory is off?". |

## 3. High-Performance Research Roadmap

### Phase 1: Instrumentation & Telemetry (Days 1-2)
*Objective: Turn the system into a "Glass Box" where every millisecond and decision is recorded.*

1.  **Structured Event Logging**: Implement a `TelemetryService` that records:
    *   `trace_id`: Unique run ID.
    *   `agent_name`: Which agent is acting.
    *   `input_tokens`, `output_tokens`: Cost/Complexity tracking.
    *   `latency_ms`: Exact timing.
    *   `tool_usage`: Which tools were called.
2.  **Output Serialization**: Ensure every "Analysis Run" can be saved as a pure JSON artifact (input + full internal state + output).

### Phase 2: The "Baguio Civic Benchmark" (BCB-100) (Days 3-5)
*Objective: Create the Ruler we will measure against.*

1.  **Data Curation**:
    *   Freeze a dataset of 100 real Reddit/Facebook posts about Baguio.
    *   Categories: 20 Infrastructure, 20 Health, 20 Safety, 20 Tourism, 20 Economy.
2.  **Gold Labeling**:
    *   Manually annotate "Ideal Sentiment" (Positive/Negative/Neutral).
    *   Manually annotate "Key Insights" (What *should* the AI have caught?).
3.  **Artifact**: `backend/benchmarks/data/bcb_100.json`.

### Phase 3: The Experment Runner (Days 6-8)
*Objective: Automated Science.*

1.  **Creation of `benchmark.py`**: A script that:
    *   Loads `bcb_100.json`.
    *   Runs **Configuration A (Hinaing Full)**.
    *   Runs **Configuration B (Gemini 2.5 Raw)**.
    *   Runs **Configuration C (No RAG / No Memory)**.
2.  **Automated Scoring**:
    *   Compare System Output vs Gold Labels.
    *   Compute Precision, Recall, F1.
    *   Compute "Hallucination Rate" (facts in output not in source).

### Phase 4: The Ablation Study (Day 9)
*Objective: Prove *why* it works.*

1.  **Memory Test**: Run the benchmark twice.
    *   Hypothesis: Run 2 has higher accuracy/depth than Run 1 because of the cyclic memory loop.
    *   Metric: "Insight Novelty Score" or "Context Recall".
2.  **Diversity Test**: Run with `QueryOrchestrator` (Multi-Query) vs Single Query.
    *   Metric: Number of distinct sources retrieved.

## 4. Immediate Action Items

To proceed with "Precision and Accuracy", I propose we start with **Phase 1: Instrumentation**:

1. [x] Create `backend/app/core/telemetry.py` for structured scientific logging.
2. [x] Inject telemetry into `QueryOrchestrator` and `RetrievalAgent`.
3. [x] Fix missing `rag_chunks_stored` and `relevance` metrics in `graph.py` (Solved "0 RAG metrics" issue).
4. [ ] Create a script to freeze current Reddit data into an initial dataset.

