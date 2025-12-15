# Hinaing: 7-Node Cognitive Architecture (13-Agent System)

**Document Status**: Official Defense Reference
**System Type**: Multi-Agentic System for Hyper-Local Situational Awareness

---

## 1. Executive Summary for Defense
Hinaing is not a simple "wrapper" around an LLM. It is a **7-Node Cognitive Architecture** comprised of **13 Specialized Agents** working in concert. The system employs a novel **Cyclic Learning Graph** where the output of one analysis cycle becomes the input memory for the next, enabling the system to "learn" about Baguio City's civic issues over time.

---

## 2. The 13-Agent Breakdown

The system represents a **Distributed Cognition** approach, where complex analytical tasks are decomposed and assigned to specialized autonomous agents.

### Tier 1: The Executive Agents (Pipeline Management)
*These agents handle planning, data retrieval, and synthesis.*

| Agent | Responsibility | Complexity |
|-------|----------------|------------|
| **1. QueryOrchestratorAgent** | **The Planner**. Uses ReAct logic to decompose high-level directives (e.g., "Analyze Baguio") into diverse, specific search strategies strategies (e.g., "Baguio medical shortage", "Session road traffic"). | **High** (ReAct) |
| **2. RetrievalAgent** | **The Researcher**. A tool-enabled agent that interfaces with external APIs (Social Media, Web) in parallel batches to fetch raw data. | Medium (Async) |
| **3. ContextAugmentationAgent** | **The Memory**. Manages the RAG pipeline. Novel contribution: It performs **Dual-Directional Memory** operations—*Recall* (fetching past learnings) and *Consolidation* (writing new learnings). | **High** (Vector/RAG) |
| **4. CoordinatorAgent** | **The Manager**. Synthesizes conflicting data points from all other agents into a coherent final narrative and structural dashboard. | Medium (Synthesis) |

### Tier 2: The Specialist Agents (Analysis & Verification)
*These agents apply specific analytical frameworks to the raw data.*

| Agent | Responsibility | Complexity |
|-------|----------------|------------|
| **5. SentimentAgent** | **The Analyst**. A Hybrid Ensemble Agent. It combines a local **RoBERTa** model (for speed/consistency) with **Gemini Connect** (for nuance) to grade public emotion with higher accuracy than single models. | **High** (Ensemble) |
| **6. CredibilityAgent** | **The Judge**. A "Safety" agent that cross-references 5 distinct signals (Domain Trust, Fact Check API, Semantic Consistency, etc.) to detect misinformation before it reaches the consensus layer. | **High** (Multi-Signal) |
| **7. ThemeRouterAgent** | **The Distributor**. A "Sorting Hat" classification agent that analyzes semantic content to route documents to the appropriate domain expert(s) below. | Medium (Classification) |

### Tier 3: The Domain Experts (Parallel Workers)
*These 6 agents run simultaneously to provide deep, sector-specific expertise.*

| Agent | Domain | Focus Area |
|-------|--------|------------|
| **8. Infrastructure Agent** | **Public Works** | Roads, Water Supply, Power Grid, Transport |
| **9. Health Agent** | **Public Health** | Disease Outbreaks (Dengue), Hospital Capacity, Sanitation |
| **10. Safety Agent** | **Civil Defense** | Crime Rates, Disaster Risk (Landslides), Emergency Response |
| **11. Tourism Agent** | **Economy/Visitor** | Tourist Influx, Event Management (Panagbenga), Traffic Impact |
| **12. Economy Agent** | **Livelihood** | Market Vendor Issues, Cost of Living, Employment |
| **13. Environment Agent** | **Ecology** | Waste Management, Pollution, Green Spaces |

---

## 3. Core Scientific Contributions (The "Novelty")

When asked "What is new here?", cite these three architectural innovations:

### A. Distributed Cognition & Parallelism
Unlike standard chatbots that process requests linearly, Hinaing splits the problem. The **Infrastructure Agent** and **Health Agent** run on parallel threads. This reduces hallucinations because each agent is "grounded" in its specific domain context (e.g., The Health Agent ignores traffic data, effectively reducing noise).

### B. Cyclic Learning Graph (Node 3 & Node 5)
Standard RAG systems are static—they read from a database. Hinaing implements a **Read-Write Memory Loop**:
1.  **Node 3 (Recall)**: Fetches relevant history *before* analysis.
2.  **Node 5 (Consolidation)**: Writes the *new* analysis back into memory.
*Result*: The system gets smarter with every run. Run #10 has access to the insights of Runs #1-9.

### C. Ensemble Credibility Verification
We do not rely on the LLM's internal safety filters alone. We implemented an external **5-Signal Verification Protocol** (Fact Check API + Domain Whitelist + Semantic Cross-Reference) managed by the **CredibilityAgent**. This treats "Truth" as a consensus of independent signals, not just probability.

---

## 4. Visualizing the Architecture

```text
USER REQUEST
   │
   ▼
[1] QueryOrchestrator (ReAct Planning)
   │
   ▼
[2] RetrievalAgent (Social & Web Search) ───► [3] ContextAugmentation (Memory Recall)
   │                                                 ▲
   ▼                                                 │
[4] UNIFIED ANALYSIS LAYER                           │
    ├── [5] SentimentAgent (RoBERTa + Gemini)        │
    ├── [6] CredibilityAgent (5-Signal Check)        │
    └── [7] ThemeRouterAgent (Classification)        │
   │                                                 │
   ▼                                                 │
[8-13] PARALLEL DOMAIN EXPERTS                       │
    ├── Infrastructure                               │
    ├── Health                                       │
    ├── Safety                                       │ (Insight
    ├── Tourism                                      │  Loop)
    ├── Economy                                      │
    └── Environment                                  │
   │                                                 │
   ▼                                                 │
[5] ContextAugmentation (Memory Consolidation) ──────┘
   │
   ▼
[4] CoordinatorAgent (Final Synthesis)
   │
   ▼
DASHBOARD OUTPUT
```
