# Novelty Documentation Map

**Date**: February 5, 2026  
**Purpose**: Cross-reference where each novel contribution is documented

---

## Quick Answer: Where is Novelty Documented?

The novelty aspects of the **Hybrid Agentic Architecture (ReAct + Context Engineering)** are documented across **5 main files**:

| Novelty Aspect | Primary Doc | Supporting Docs |
|----------------|-------------|-----------------|
| **Architectural Inductive Bias** | THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md | HYBRID_AGENTIC_ARCHITECTURE.md |
| **Linearized Knowledge Graph** | THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md | HYBRID_AGENTIC_ARCHITECTURE.md |
| **Dual-Layer Context Engineering** | HYBRID_AGENTIC_ARCHITECTURE.md | THESIS_FINDINGS.md |
| **Neuro-Symbolic Architecture** | THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md | README.md |
| **Guided Agentic System** | HYBRID_AGENTIC_ARCHITECTURE.md | - |
| **Temporal-Aware Query Planning** | HYBRID_AGENTIC_ARCHITECTURE.md | THESIS_FINDINGS.md |

---

## Detailed Documentation Mapping

### 1. Architectural Inductive Bias

**Concept**: Using EMERGING_CONCERNS as architectural structure that guides LLM reasoning

**Where Documented**:

#### Primary: `docs/THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md`
- **Section**: Research Gap 3: Domain-Specific Contextual Grounding
- **Lines**: 66-70
- **Quote**: 
  > "The `QueryOrchestratorAgent` utilizes an **A Priori Expert Ontology** (functioning as architectural Inductive Bias) effectively acting as a **Linearized Knowledge Graph**."
  
  > "By hard-coding the `EMERGING_CONCERNS`, we introduce a necessary **Inductive Bias**—architecturally forcing the model to assume that generic terms like 'congestion' specifically refer to Baguio entities (Session Road, etc.)."

#### Supporting: `docs/HYBRID_AGENTIC_ARCHITECTURE.md`
- **Section**: Dynamic Context Engineering: EMERGING_CONCERNS
- **Lines**: 88-104
- **Quote**:
  > "**Scientific Term**: 'Linearized Knowledge Graph' or 'A Priori Expert Ontology'"
  
  > "**Why This Works**: Introduces **Inductive Bias** - architecturally forces the model to assume generic terms like 'congestion' specifically refer to Baguio entities (Session Road, etc.)"

---

### 2. Linearized Knowledge Graph

**Concept**: EMERGING_CONCERNS function as a knowledge graph flattened into tool-accessible format

**Where Documented**:

#### Primary: `docs/THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md`
- **Section**: Research Gap 3: Domain-Specific Contextual Grounding
- **Lines**: 67-68
- **Quote**:
  > "The `QueryOrchestratorAgent` utilizes an **A Priori Expert Ontology** (functioning as architectural Inductive Bias) effectively acting as a **Linearized Knowledge Graph**."

#### Supporting: `docs/HYBRID_AGENTIC_ARCHITECTURE.md`
- **Section**: Dynamic Context Engineering: EMERGING_CONCERNS
- **Lines**: 101
- **Quote**:
  > "**Scientific Term**: 'Linearized Knowledge Graph' or 'A Priori Expert Ontology'"

---

### 3. Dual-Layer Context Engineering (Static + Dynamic)

**Concept**: Combining pre-defined domain knowledge with time-aware seasonal expansion

**Where Documented**:

#### Primary: `docs/HYBRID_AGENTIC_ARCHITECTURE.md`
- **Section**: Architecture Components
- **Lines**: 44-145
- **Coverage**:
  - Dynamic Context Engineering (EMERGING_CONCERNS) - Lines 88-104
  - Dynamic Context Engineering (Seasonal Expansion) - Lines 106-145
  - Explicit "Dual-Layer" terminology - Lines 1, 10, 34

#### Supporting: `docs/THESIS_FINDINGS.md`
- **Section**: 2. QueryOrchestratorAgent: Context Engineering with Multi-Query Diversity
- **Lines**: 62-87
- **Quote**:
  > "**QueryOrchestratorAgent** uses ReAct reasoning with **context engineering** - pre-defined domain knowledge via EMERGING_CONCERNS and dynamic contextual expansion"

---

### 4. Neuro-Symbolic Architecture

**Concept**: Combining symbolic AI (rules/ontology) with neural AI (LLMs/embeddings)

**Where Documented**:

#### Primary: `docs/THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md`
- **Section**: Technical Innovation Summary
- **Lines**: 106-113
- **Quote**:
  > "The Hinaing system represents a novel integration of **Symbolic AI** (expert systems/rules) and **Neural AI** (LLMs/Embeddings):"
  
  > "**Neuro-Symbolic Cognitive Architecture (Context-Engineered Multi-Agent System)**: Combining rigid expert rules (Symbolic Safety) with flexible LLM reasoning (Neural Nuance). The **7-node pipeline itself is Context Engineering** (Structural Inductive Bias)."

#### Supporting: `docs/README.md`
- **Section**: Novel Contributions
- **Lines**: 98-102
- **Quote**:
  > "**Neuro-Symbolic Cognitive Architecture (Context-Engineered Multi-Agent System)** – Combines rigid expert rules (Symbolic Safety) with flexible LLM reasoning (Neural Nuance)."

#### Also Mentioned In:
- All thesis title options (Option 2 explicitly uses "Neuro-Symbolic")
- `docs/THESIS_FINDINGS.md` - Title options

---

### 5. Guided Agentic System

**Concept**: Agentic reasoning guided by domain-specific context (not pure autonomous)

**Where Documented**:

#### Primary: `docs/HYBRID_AGENTIC_ARCHITECTURE.md`
- **Section**: Why Hybrid? The Best of Both Worlds
- **Lines**: 18-34
- **Quote**:
  > "**Hybrid (ReAct + Context Engineering) ✅**  
  > **Solution**: Guided Agentic System with Domain-Specific Context"

- **Section**: Academic Classification
- **Lines**: 219-222
- **Quote**:
  > "**Technical Term**: 'Guided Agentic System with Domain-Specific Context Engineering'"

#### Not Explicitly Documented Elsewhere:
- This is the **NEW terminology** introduced in `HYBRID_AGENTIC_ARCHITECTURE.md`
- Other docs use "ReAct" or "Agentic" but don't use "Guided Agentic System"

---

### 6. Temporal-Aware Query Planning

**Concept**: Dynamic seasonal/time-based query expansion (Panagbenga, typhoon season, etc.)

**Where Documented**:

#### Primary: `docs/HYBRID_AGENTIC_ARCHITECTURE.md`
- **Section**: Dynamic Context Engineering: Seasonal/Temporal Expansion
- **Lines**: 106-145
- **Quote**:
  > "The `expand_contextual_queries` tool adds **time-aware queries** based on current date"
  
  > "**Purpose**: Add queries that static clusters would miss (seasonal events, holidays, weather patterns)"

#### Supporting: `docs/THESIS_FINDINGS.md`
- **Section**: 2. QueryOrchestratorAgent: Context Engineering with Multi-Query Diversity
- **Lines**: 82-87
- **Table showing tools**:
  | Tool | Type | Purpose |
  |------|------|---------|
  | `expand_contextual_queries` | Dynamic Context Engineering | Adds seasonal/time-aware queries (Christmas, Panagbenga, typhoon) |

---

### 7. Context Engineering as Scientific Contribution

**Concept**: Context engineering > prompt engineering for low-resource domains

**Where Documented**:

#### Primary: `docs/THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md`
- **Section**: Research Gap 3: Domain-Specific Contextual Grounding
- **Lines**: 71-73
- **Quote**:
  > "**Scientific Contribution:** Demonstrating that **Context Engineering** (the systematic architectural construction of the agent's environment) is superior to standard **Prompt Engineering** for low-resource, high-nuance domains."

#### Supporting: `docs/ARCHITECTURE.md`
- **Section**: Overview
- **Lines**: 11-13
- **Quote**:
  > "**Context Engineering**: The entire architecture is a form of context engineering. Rather than relying on a single LLM prompt, we design the pipeline structure, agent specializations (18 agents), emerging concerns (EMERGING_CONCERNS), theme definitions (THEME_GROUPS), credibility signals (5-signal framework), and domain trust tiers to inject Baguio-specific civic knowledge at every node."

---

## Summary Table: Documentation Coverage

| Novelty Aspect | THESIS_RESEARCH_GAPS | THESIS_FINDINGS | HYBRID_AGENTIC | README | ARCHITECTURE |
|----------------|---------------------|-----------------|----------------|--------|--------------|
| **Architectural Inductive Bias** | ✅ Primary | ❌ | ✅ Supporting | ❌ | ❌ |
| **Linearized Knowledge Graph** | ✅ Primary | ❌ | ✅ Supporting | ❌ | ❌ |
| **Dual-Layer Context Engineering** | ❌ | ✅ Supporting | ✅ Primary | ❌ | ❌ |
| **Neuro-Symbolic Architecture** | ✅ Primary | ✅ Titles | ❌ | ✅ Supporting | ❌ |
| **Guided Agentic System** | ❌ | ❌ | ✅ Primary (NEW) | ❌ | ❌ |
| **Temporal-Aware Query Planning** | ❌ | ✅ Supporting | ✅ Primary | ❌ | ❌ |
| **Context > Prompt Engineering** | ✅ Primary | ❌ | ❌ | ❌ | ✅ Supporting |

---

## What Was Missing Before `HYBRID_AGENTIC_ARCHITECTURE.md`?

### Previously Undocumented:
1. ❌ **"Guided Agentic System"** terminology - NEW
2. ❌ **Explicit "Dual-Layer"** terminology - NEW
3. ❌ **Why Hybrid > Pure Agentic** - NEW
4. ❌ **Why Hybrid > Pure Hardcoded** - NEW
5. ❌ **Execution flow showing ReAct + Context** - NEW
6. ❌ **Defense strategy for "is this really agentic?"** - NEW

### Previously Scattered:
1. ⚠️ **Architectural Inductive Bias** - Only in THESIS_RESEARCH_GAPS
2. ⚠️ **Linearized Knowledge Graph** - Only in THESIS_RESEARCH_GAPS
3. ⚠️ **Temporal-Aware Queries** - Only in THESIS_FINDINGS (brief mention)

---

## Recommended Reading Order for Thesis Defense

### For Understanding Novelty:
1. **`docs/HYBRID_AGENTIC_ARCHITECTURE.md`** ⭐ - Start here (comprehensive, defense-ready)
2. **`docs/THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md`** - Deep dive on scientific contributions
3. **`docs/THESIS_FINDINGS.md`** - Empirical validation and agent details
4. **`docs/README.md`** - High-level overview

### For Implementation Details:
1. **`backend/app/services/agents/query_orchestrator.py`** - Code implementation
2. **`docs/ARCHITECTURE.md`** - Full system architecture

---

## Cross-References by Research Question

### "What makes your system novel?"
**Answer**: Hybrid Agentic Architecture (ReAct + Dual-Layer Context Engineering)  
**Read**: 
1. `docs/HYBRID_AGENTIC_ARCHITECTURE.md` (Lines 1-50)
2. `docs/THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md` (Lines 106-113)

### "Why not just use pure ReAct?"
**Answer**: Pure ReAct lacks domain knowledge (contextual blindness)  
**Read**: 
1. `docs/HYBRID_AGENTIC_ARCHITECTURE.md` (Lines 18-34)
2. `docs/THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md` (Lines 61-73)

### "What is architectural inductive bias?"
**Answer**: EMERGING_CONCERNS as structural guidance for LLM reasoning  
**Read**: 
1. `docs/THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md` (Lines 66-70)
2. `docs/HYBRID_AGENTIC_ARCHITECTURE.md` (Lines 88-104)

### "What is dual-layer context engineering?"
**Answer**: Static (EMERGING_CONCERNS) + Dynamic (seasonal expansion)  
**Read**: 
1. `docs/HYBRID_AGENTIC_ARCHITECTURE.md` (Lines 44-145)
2. `docs/THESIS_FINDINGS.md` (Lines 62-87)

### "Is this really agentic if you use hardcoded keywords?"
**Answer**: Yes - keywords are tools, agent decides how to use them  
**Read**: 
1. `docs/HYBRID_AGENTIC_ARCHITECTURE.md` (Lines 195-217, 260-280)

---

## Files That DON'T Document Novelty

These files focus on other aspects (not novelty):

- `docs/ROADMAP.md` - Implementation status
- `docs/DEFENSE_GUIDE.md` - Defense preparation
- `docs/EVALUATION_GUIDE.md` - Evaluation methodology
- `docs/SCIENTIFIC_RESEARCH_PLAN.md` - Research methodology
- `docs/GROQ_*.md` - Migration documentation
- `docs/SPEED_*.md` - Performance optimization

---

## Conclusion

### Before `HYBRID_AGENTIC_ARCHITECTURE.md`:
- Novelty was **scattered** across 3-4 files
- No **explicit "Guided Agentic System"** terminology
- No **defense strategy** for "is this really agentic?"
- No **comparison table** (Pure Agentic vs Pure Hardcoded vs Hybrid)

### After `HYBRID_AGENTIC_ARCHITECTURE.md`:
- ✅ **Centralized** novelty documentation
- ✅ **Explicit terminology** (Guided Agentic System, Dual-Layer)
- ✅ **Defense-ready** with Q&A section
- ✅ **Comparison tables** showing why hybrid is better

### Recommendation:
Use `HYBRID_AGENTIC_ARCHITECTURE.md` as your **primary reference** for thesis defense, with `THESIS_RESEARCH_GAPS_AND_SOLUTIONS.md` as supporting evidence for scientific contributions.

---

**Last Updated**: February 5, 2026  
**Status**: Complete documentation mapping  
**Purpose**: Quick reference for thesis defense preparation

