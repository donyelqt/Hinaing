# Self-Learning Architecture Implementation Plan

> **Thesis Title (Option 1):** 7-Node Agentic Graphs: Multi-Signal Fusion for Verified Context-Aware Public Opinion Synthesis
>
> **Thesis Title (Option 2):** Hinaing: A Neuro-Symbolic Multi-Agent Framework for Epistemic Truth Discovery in Civic Social Listening
>
> **Thesis Title (Option 3):** Hinaing: A Context-Engineered Self-Learning Multi-Agent Agentic AI System with Ensemble Sentiment and 5-Signal Credibility for Public Opinion Analysis in Baguio City
>
> **Thesis Title (Unified):** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

> **Thesis Title:** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening

## Overview
Transitions the Hinaing system from a linear "Monitor" architecture to a **7-Node Self-Learning (Circular) Architecture**. This enables the system to treat historical RAG data as a "first-class citizen" in analysis while continuously accumulating new knowledge from every snapshot execution.

## Architecture Refactoring (7 Nodes)

### Current vs. Target State
| Node | Current Role | Target Role | Action |
|------|--------------|-------------|--------|
| **Node 1** | Query Orchestrator | Query Orchestrator | Keep |
| **Node 2** | Retrieval Agent (External) | Retrieval Agent (External) | Keep |
| **Node 3** | Parallel Analysis | **Internal Retrieval (Memory Recall)** | **NEW** |
| **Node 4** | Context (RAG) | **Unified Analysis (Parallel)** | **Move & Rename** |
| **Node 5** | Theme Agents | **Memory Consolidation (Ingest)** | **Refactor** |
| **Node 6** | Build Snapshot | **Theme Agents** | **Move** |
| **Node 7** | (None) | **Build Snapshot (Narrative)** | **Add** |

---

## Phase 1: Service Layer Refactoring

### 1. Update `ContextAugmentationAgent` (`backend/app/services/agents/context_agent.py`)
Split the current `augment_context` method into two distinct operations:
*   **`retrieve_knowledge(focus_areas)`**:
    *   Takes specific focus keywords.
    *   Queries `VectorStore` for relevance.
    *   Returns `List[WebDocument]` (converted from Chunks).
    *   *Goal:* Provide historical data for the Analysis Node.
*   **`consolidate_memory(documents)`**:
    *   Takes processed/classified documents.
    *   Chunks and Embeds them.
    *   Saves to `VectorStore`.
    *   *Goal:* Learn from the current session.

### 2. Update `SnapshotState` (`backend/app/services/insights/graph.py`)
Add new state keys to track internal vs. external data:
```python
class SnapshotState(TypedDict):
    # ... existing keys
    internal_documents: list[WebDocument]  # From Vector DB
    external_documents: list[WebDocument]  # From Web/Social
    # 'documents' will now be Union[internal, external]
```

---

## Phase 2: LangGraph Workflow Implementation

### 3. Create Node 3: `retrieve_internal_knowledge`
*   **Input:** `state["request"].focus_areas`
*   **Logic:**
    *   Call `ContextAugmentationAgent.retrieve_knowledge`.
    *   Map `DocumentChunk` objects back to `WebDocument` with `metadata={"source": "internal_memory"}`.
    *   Update `state["internal_documents"]`.

### 4. Update Node 4: `label_sentiment_and_analyze`
*   **Input:** `state["external_documents"]` + `state["internal_documents"]`
*   **Logic:**
    *   Merge both lists into `state["documents"]`.
    *   Run Sentiment, Credibility, and Theme Router on the **combined** list.
    *   *Benefit:* Historical RAG data now gets fresh sentiment scores.

### 5. Create Node 5: `consolidate_memory`
*   **Input:** `state["documents"]` (Fresh only? Or all?)
    *   *Decision:* Only ingest `state["external_documents"]` to avoid duplication loops.
*   **Logic:**
    *   Call `ContextAugmentationAgent.consolidate_memory`.
    *   Stores fresh news into Qdrant for future recall.

### 6. Wire the Graph (`backend/app/services/insights/graph.py`)
Refactor the `StateGraph` definition:
```python
graph.add_edge("fetch_documents", "retrieve_internal_knowledge")
graph.add_edge("retrieve_internal_knowledge", "label_sentiment_and_analyze")
graph.add_edge("label_sentiment_and_analyze", "consolidate_memory")
graph.add_edge("consolidate_memory", "theme_agents")
```

---

## Phase 3: Defense & Verification

### 7. "Self-Learning" Verification Test
1.  **Run 1 (Teach):** Generate snapshot for "Baguio Water Crisis".
    *   System retrieves fresh news about water.
    *   System saves to Vector DB.
2.  **Run 2 (Recall):** Generate snapshot for "Water" (5 mins later).
    *   System retrieves "Water" data from Vector DB (Node 3).
    *   Resulting Analysis includes "Internal Memory" sources with sentiment scores.
3.  **Metrics Check:**
    *   Ensure latency doesn't spike due to double retrieval.
    *   Ensure Sentiment Stats include the Internal docs.

## Schema Changes
No database schema changes required. `WebDocument` Pydantic model is sufficient to hold both external and internal data.
