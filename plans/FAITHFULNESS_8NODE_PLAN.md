# Faithfulness Implementation Plan: 8-Node Option (Separate Verification)

**Project:** AgenticHinaing - Contextual Faithfulness Enhancement  
**Version:** 1.0 (8-Node Option)  
**Date:** March 17, 2026   
**Status:** Alternative Option  

---

## 🎯 Quick Decision

**This is the 8-Node Option** - verification as a **separate, dedicated node** (Node 8).

**Alternative:** See `FAITHFULNESS_IMPLEMENTATION_PLAN.md` for the **7-Node Option** (integrated verification - RECOMMENDED).

| Factor | 7-Node (Recommended) | 8-Node (This Plan) |
|--------|-------------------|---------------------|
| **Verification Location** | Inside Node 7 (sub-agent) | **Node 8 (separate node)** |
| **Graph Changes** | ❌ None | ✅ **Required** |
| **Thesis Updates** | 8-12 pages | **15-20 pages** |
| **Implementation** | 4-7 days | **5-9 days** |
| **Recommendation** | ✅ **RECOMMENDED** | ⚠️ Only if >2 months deadline |

---

## 🏗️ Architecture

### **8-Node Pipeline**

```
Node 1 → Node 2 → Node 3* → Node 4 → Node 5 → Node 6 → Node 7* → Node 8*
(Query)  (Fetch)  (FADR)   (Analyze)(Write)  (Theme)  (CWA)     (PGCV)

* = Enhanced with faithfulness mechanisms
```

### **Node 8 Details**

```
┌────────────────────────────────────────────────────────┐
│  Node 8: Post-Generation Claim Verification (PGCV)     │
├────────────────────────────────────────────────────────┤
│  Input: summary, documents                             │
│  Process: Extract claims → Verify (NLI) → Score       │
│  Output: verification report                           │
└────────────────────────────────────────────────────────┘
```

---

## 📝 Implementation Phases

### **Phase 1: CWA** - Same as 7-Node (1-2 days)

### **Phase 2: PGCV** - ⚠️ DIFFERENT (3-4 days)

**Location:** Node 8 (Separate Node)

#### **Naming Convention: FaithfulnessAgent (NOT VerificationAgent)**

**Decision:** Use `FaithfulnessAgent` (metric-based naming)

**Why:**
- ✅ **Avoids confusion with CredibilityAgent** (which does multi-signal verification)
- ✅ **Clear distinction:** CredibilityAgent verifies sources, FaithfulnessAgent verifies claims
- ✅ **Matches thesis terminology** ("Contextual Faithfulness")
- ✅ **Unique in codebase** (no naming conflicts)
- ⚠️ Breaks 7/8 action-based pattern, but worth it for clarity

**Pattern Match:**
- `CredibilityAgent` → Assesses source credibility (multi-signal verification)
- `FaithfulnessAgent` → Measures claim faithfulness (NLI entailment)

**Thesis Framing:** "Faithfulness Agent (`FaithfulnessAgent`) - measures contextual faithfulness via NLI-based claim verification"

#### **Tasks**

- [ ] Task 2.1: Create ClaimExtractor (`backend/app/services/verification/claim_extractor.py`)
- [ ] Task 2.2: Create EntailmentChecker (`backend/app/services/verification/entailment_checker.py`)
- [ ] Task 2.3: Create **FaithfulnessAgent** (`backend/app/services/agents/faithfulness_agent.py`)
- [ ] **Task 2.4: Add Node 8 to Graph** ⚠️ GRAPH CHANGES REQUIRED
  - File: `backend/app/services/insights/graph.py`
  - Add: `graph.add_node("verify_narrative", verify_narrative)`
  - Add: `graph.add_edge("build_snapshot", "verify_narrative")`
  - Add: `graph.add_edge("verify_narrative", END)`
- [ ] **Task 2.5: Create Node 8 Handler** ⚠️ NEW NODE FUNCTION
  - File: `backend/app/services/insights/nodes.py`
  - New: `async def verify_narrative(state: SnapshotState)`
- [ ] Task 2.6: Add VerificationReport schema (`backend/app/schemas/snapshot.py`)
- [ ] **Task 2.7: Update SnapshotState** ⚠️ ADD FIELD
  - File: `backend/app/services/insights/definitions.py`
  - Add: `verification: VerificationReport | None`
- [ ] Task 2.8: Test with 20 snapshots

#### **Code Structure (8-Node)**

```python
# backend/app/services/insights/graph.py

# Add Node 8
graph.add_node("verify_narrative", verify_narrative)

# Rewire edges
graph.add_edge("build_snapshot", "verify_narrative")  # Node 7 → Node 8
graph.add_edge("verify_narrative", END)               # Node 8 → END
```

```python
# backend/app/services/insights/nodes.py

async def verify_narrative(state: SnapshotState) -> SnapshotState:
    """Node 8: Verify claims in generated narrative."""
    summary = state.get("summary", "")
    
    from ..agents.faithfulness_agent import FaithfulnessAgent
    verifier = FaithfulnessAgent()
    verification = await verifier.verify(summary, state["enriched"])
    
    state["verification"] = verification
    return state
```

---

### **Phase 3: FADR** - Same as 7-Node (1 day)

### **Phase 4: RAGAS** - Same as 7-Node (1 day)

---

## 📊 8-Node vs. 7-Node Comparison

| Factor | 7-Node | 8-Node |
|--------|--------|--------|
| **Implementation Time** | 4-7 days | **5-9 days** |
| **Files Modified** | 6 files | **8 files** |
| **Graph Changes** | ❌ None | ✅ **Required** |
| **Thesis Updates** | 8-12 pages | **15-20 pages** |
| **Diagram Updates** | ❌ None | ✅ **All diagrams** |
| **Modularity** | Good | **Better** |
| **Performance** | **Faster** | Slower (inter-node) |
| **Flexibility** | Verification always runs | **Can skip verification** |
| **Scalability** | Coupled scaling | **Independent scaling** |
| **Defense Simplicity** | **"Still 7 nodes"** | "Why 8 nodes?" |

---

## 🎯 8-Node: Thesis Updates Required

### **Full Updates (Required)**

- [ ] **Chapter 3:** Complete architecture rewrite
  - Update Figure 3.1 (7 nodes → 8 nodes)
  - Add Section 3.10: Node 8 (Claim Verification)
  - Update all pipeline diagrams
  - Update state transition diagram

- [ ] **Chapter 4:** Add Section 4.6 (Faithfulness Results)

- [ ] **Abstract:** Rewrite to mention 8 nodes

- [ ] **Conclusion:** Update contributions

- [ ] **All Diagrams:** Update node count everywhere

**Total Pages:** 15-20 pages  
**Writing Time:** 3-5 days

---

## 🏆 When to Choose 8-Node

### **Choose 8-Node If:**

- ✅ Thesis deadline is >2 months away
- ✅ You need to skip verification in some modes (fast vs. thorough)
- ✅ You plan to reuse verification in other pipelines
- ✅ Maximum modularity is critical
- ✅ You don't mind updating all architecture diagrams
- ✅ You have adviser approval for architecture change

### **DON'T Choose 8-Node If:**

- ❌ Thesis deadline is <1 month away
- ❌ You want minimal documentation updates
- ❌ You want to follow existing Node 4 pattern
- ❌ Performance is a priority
- ❌ You want architectural consistency (all docs say 7 nodes)

---

## 🎓 8-Node Thesis Defense Script

**Panelist:** "Why did you add Node 8 instead of integrating into Node 7?"

**You:**
> "We chose a separate verification node for three reasons:
>
> 1. **Separation of Concerns:** Generation and verification are distinct responsibilities.
>
> 2. **Flexibility:** We can skip verification in fast modes or enable it for thorough analysis.
>
> 3. **Testability:** Having verification as a separate node makes it easier to test independently.
>
> **Trade-off:** We accept slight latency overhead (~0.1-0.2s) for better modularity."

---

## ⚠️ 8-Node Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Thesis Inconsistency** | High (all docs say 7 nodes) | Update all diagrams + text |
| **Panelist Questions** | Medium ("Why change from 7 to 8?") | Prepare justification script |
| **Implementation Complexity** | Medium (graph wiring) | Follow Node 4 pattern |
| **Documentation Overhead** | High (15-20 pages) | Start writing early |

---

## ✅ 8-Node Benefits

| Benefit | Impact |
|---------|--------|
| **Maximum Modularity** | Verification is fully independent |
| **Independent Scaling** | Can scale Node 7 and Node 8 separately |
| **Runtime Flexibility** | Can skip verification in some modes |
| **Clean Separation** | Generation vs. verification clearly separated |
| **Better Testability** | Node 8 can be tested in complete isolation |

---

## 📅 Timeline Summary

| Phase | Duration | Dependencies | Priority |
|-------|----------|--------------|----------|
| **Phase 1: CWA** | 1-2 days | None | ⭐⭐⭐ HIGH |
| **Phase 2: PGCV** | 3-4 days | Phase 1 | ⭐⭐⭐ HIGH |
| **Phase 3: FADR** | 1 day | None | ⭐⭐ MEDIUM |
| **Phase 4: RAGAS** | 1 day | Phases 1-3 | ⭐ LOW |

**Total Timeline:** 5-9 days (vs. 4-7 days for 7-Node)

---

## 🚀 Getting Started (8-Node)

### **Prerequisites**

- [ ] Python 3.11+ environment
- [ ] Poetry installed
- [ ] Groq API key configured
- [ ] Qdrant connection configured
- [ ] **Adviser approval for 8-node architecture change** ⚠️

### **First Implementation Step**

Start with **Phase 1, Task 1.1** (Same as 7-Node):

```bash
# Open file
code backend/app/services/nlp/gemini.py

# Find: _build_prompt() method
# Add citation requirements
```

---

## 📞 Support & Resources

**See Also:**
- `FAITHFULNESS_IMPLEMENTATION_PLAN.md` (7-Node Option - RECOMMENDED)
- `docs/CONTEXTUAL_FAITHFULNESS_ANALYSIS.md` (Technical Analysis)
- `docs/BRUTALLY_HONEST_FAITHFULNESS_ANALYSIS.md` (Honest Assessment)

---

## ✅ 8-Node Checklist Summary

### **Phase 1: CWA (1-2 days)**

- [ ] Task 1.1: Modify Node 7 prompt
- [ ] Task 1.2: Prepare document metadata
- [ ] Task 1.3: Add citation validation
- [ ] Task 1.4: Test with 10 snapshots

### **Phase 2: PGCV (3-4 days) ⚠️ 8-NODE SPECIFIC**

- [ ] Task 2.1: Create ClaimExtractor
- [ ] Task 2.2: Create EntailmentChecker
- [ ] Task 2.3: Create VerificationAgent
- [ ] **Task 2.4: Add Node 8 to graph** ⚠️ GRAPH CHANGES
- [ ] **Task 2.5: Create verify_narrative()** ⚠️ NEW NODE HANDLER
- [ ] **Task 2.6: Update SnapshotState** ⚠️ ADD VERIFICATION FIELD
- [ ] Task 2.7: Add VerificationReport schema
- [ ] Task 2.8: Test with 20 snapshots

### **Phase 3: FADR (1 day)**

- [ ] Task 3.1: Add faithfulness scoring function
- [ ] Task 3.2: Integrate into search method
- [ ] Task 3.3: Test ranking quality

### **Phase 4: RAGAS (1 day)**

- [ ] Task 4.1: Create test dataset
- [ ] Task 4.2: Run baseline evaluation
- [ ] Task 4.3: Run post-improvement evaluation
- [ ] Task 4.4: Correlate scores

### **Documentation (3-5 days) ⚠️ MORE THAN 7-NODE**

- [ ] Update ALL architecture diagrams (7 → 8 nodes)
- [ ] Add Chapter 3 section for Node 8
- [ ] Update state transition diagrams
- [ ] Update pipeline visualizations
- [ ] Write Chapter 4 faithfulness results
- [ ] Update abstract and conclusion

---

## 🎯 Success Criteria (8-Node)

**Implementation Complete When:**

1. ✅ All 4 phases completed
2. ✅ RAGAS faithfulness score ≥ 0.90
3. ✅ Citation rate ≥ 80%
4. ✅ Verification latency < 1s
5. ✅ All tests passing
6. ✅ **All thesis diagrams updated (7 → 8 nodes)**
7. ✅ **Adviser approved architecture change**
8. ✅ Documentation complete
9. ✅ Thesis defense ready

---

## 📚 Architecture Patterns Reference

### **Your Existing Patterns**

| Pattern | Node | Execution | Use Case |
|---------|------|-----------|----------|
| **Sequential Pipeline** | Node 1→2→3→4→5→6→7 | Sequential (inter-node) | Main pipeline flow |
| **Unified Analysis** | Node 4 | Parallel (`asyncio.gather`) | Independent tasks |
| **Theme Agents** | Node 6 | Parallel (per theme) | Specialized domains |

### **8-Node Pattern**

| Pattern | Location | Execution | Use Case |
|---------|----------|-----------|----------|
| **Separate Verification Node** | Node 8 | Sequential (new node) | Independent verification step |

### **Naming Convention**

| Agent | Naming Pattern | Example | Purpose |
|-------|---------------|---------|---------|
| **Action-Based** (6/8 agents) | `{Action}Agent` | SentimentAgent, RetrievalAgent | Clear action |
| **Metric-Based** (2/8 agents) | `{Metric}Agent` | CredibilityAgent, **FaithfulnessAgent** | Clear metric |

**Decision:** Use `FaithfulnessAgent` (metric-based, avoids confusion with CredibilityAgent)

**Why:**
- `CredibilityAgent` → Verifies **source credibility** (multi-signal: domain + cross-ref + fact-check + LLM + Tavily)
- `FaithfulnessAgent` → Verifies **claim faithfulness** (NLI entailment checking)
- Different metrics → Different agent names → Clear distinction

---

**This is the 8-Node Option. For the 7-Node Option (RECOMMENDED), see `FAITHFULNESS_IMPLEMENTATION_PLAN.md`.** 🚀
