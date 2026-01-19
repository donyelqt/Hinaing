# Sub-Agent Architecture Analysis for Performance Optimization

> **Thesis Title:** Hinaing: A 7-node Agentic Graphs Framework for Epistemic Truth Discovery in Civic Social Listening
>
> **Analysis Date:** 2026-01-16
> **Purpose:** Identify nodes that can benefit from sub-agent decomposition to speed up processing

---

## Executive Summary

After analyzing the 7-node architecture, several nodes have potential for sub-agent decomposition to improve parallelism and reduce latency. The most promising candidates are:

| Priority | Node | Current Bottleneck | Proposed Sub-Agents | Expected Speedup | Status |
|----------|------|-------------------|---------------------|------------------|--------|
| **✓ DONE** | Node 4: CredibilityAgent | 5 signals processed sequentially | 5 true sub-agents (Worker Pattern) | 3-5x | **Implemented** |
| **✓ DONE** | Node 6: Theme Agents | Function calls (not agents) | 6 true sub-agents (Worker Pattern) | N/A | **Implemented** |

---

## Detailed Analysis by Node

### Node 1: QueryOrchestratorAgent (ReAct Planning)

**Current Implementation:**
```
4 sequential tool calls:
1. analyze_focus_areas → KEYWORD_CLUSTERS
2. generate_query → static_queries  
3. expand_contextual_queries → contextual_queries
4. evaluate_query → coverage_assessment
```

**Proposed Sub-Agent Decomposition:**

```
QueryOrchestratorAgent (Coordinator)
├── Sub-Agent 1: FocusAnalyzer (analyze_focus_areas)
├── Sub-Agent 2: QueryGenerator (generate_query)
├── Sub-Agent 3: ContextExpander (expand_contextual_queries)
└── Sub-Agent 4: DiversityEvaluator (evaluate_query)
```

**Parallelization Strategy:**
- All 4 sub-agents can run **concurrently** since they read from KEYWORD_CLUSTERS
- `analyze_focus_areas` must complete first to unlock KEYWORD_CLUSTERS
- Other 3 can run in parallel after KEYWORD_CLUSTERS is available

**Expected Speedup:** 1.5-2x (amortized across query generation)

**Feasibility:** MEDIUM - Requires refactoring ReAct loop to fan-out/fan-in pattern

---

### Node 2: RetrievalAgent (Multi-Source Ingestion)

**Current Implementation:**
```
LangSearch API (Web) ──┐
Facebook (Apify)     ──┼─→ Diversity Merge (Round-Robin)
Reddit (PRAW)        ──┘
```

**Assessment:** Already optimized via `asyncio.gather`

**Proposed Changes:** None needed - parallelization is already implemented

---

### Node 3: ContextAugmentationAgent (Memory Recall)

**Current Implementation:**
```
Query Embedding → Vector Search → Top-K Results → Merge with External Docs
```

**Proposed Sub-Agent Decomposition:**

```
ContextAugmentationAgent (Coordinator)
├── Sub-Agent 1: EmbedQuery (BGE embedding for query)
└── Sub-Agent 2: VectorSearch (Qdrant cosine similarity)
    └── Can be further decomposed by focus_area (parallel per theme)
```

**Parallelization Strategy:**
- EmbedQuery and VectorSearch can overlap
- Vector search per focus_area can run in parallel

**Expected Speedup:** 1.5x

**Feasibility:** MEDIUM - Requires concurrent vector searches

---

### Node 4: Unified Analysis (HIGHEST PRIORITY)

#### 4a. CredibilityAgent - 5-Signal Parallelization

**Current Implementation:**
```
5 signals processed sequentially:
1. Domain Trust Scoring
2. Semantic Cross-Reference  
3. Google Fact Check API
4. LLM Pattern Recognition
5. Tavily Web Verification
```

**Proposed Sub-Agent Decomposition:**

```
CredibilityAgent (Coordinator)
├── Sub-Agent 1: DomainTrustScorer (25%)
├── Sub-Agent 2: SemanticCrossReferencer (20%)
├── Sub-Agent 3: FactCheckQuerier (15%)
├── Sub-Agent 4: LLMAnalyzer (20%)
└── Sub-Agent 5: TavilyVerifier (20%)
```

**Parallelization Strategy:**
- All 5 signals are **independent** - can run concurrently
- Final score is weighted average of all results

**Expected Speedup:** 3-5x (depending on API latency)

**Feasibility:** HIGH - Signals are already independent, just need parallel execution

**Code Reference:**
```python
# Current: Sequential
domain_score = await check_domain_trust(doc)
semantic_score = await check_semantic(doc)
fact_check = await query_fact_check(doc)
llm_pattern = await analyze_llm_pattern(doc)
tavily_verify = await verify_tavily(doc)

# Proposed: Parallel
scores = await asyncio.gather(
    check_domain_trust(doc),
    check_semantic(doc),
    query_fact_check(doc),
    analyze_llm_pattern(doc),
    verify_tavily(doc)
)
```

#### 4b. ThemeRouterAgent - 6-Bucket Parallelization

**Current Implementation:**
```
Compute 6 theme embeddings → Route each document to best theme
```

**Proposed Sub-Agent Decomposition:**

```
ThemeRouterAgent (Coordinator)
├── Sub-Agent 1: InfrastructureRouter
├── Sub-Agent 2: HealthRouter
├── Sub-Agent 3: SafetyRouter
├── Sub-Agent 4: TourismRouter
├── Sub-Agent 5: EconomyRouter
└── Sub-Agent 6: EnvironmentRouter
```

**Parallelization Strategy:**
- Theme embeddings are pre-computed (cached)
- Each document can be routed to all 6 themes **in parallel**
- Best theme selected via max(cosine_similarity)

**Expected Speedup:** 2-3x

**Feasibility:** HIGH - embeddings are already cached

**Code Reference:**
```python
# Current: Sequential per document
for doc in documents:
    best_theme = None
    best_score = 0
    for theme in themes:
        score = cosine_similarity(doc_embedding, theme_embedding)
        if score > best_score:
            best_score = score
            best_theme = theme
    routed_docs[best_theme].append(doc)

# Proposed: Parallel per document
for doc in documents:
    scores = await asyncio.gather(
        cosine_similarity(doc, infrastructure_emb),
        cosine_similarity(doc, health_emb),
        cosine_similarity(doc, safety_emb),
        # ... all 6 themes
    )
    best_theme = themes[max_index(scores)]
```

---

### Node 5: ContextAugmentationAgent (Memory Consolidation)

**Current Implementation:**
```
Enriched Docs → Semantic Chunk (400 chars) → Embed → Store to Qdrant
```

**Proposed Sub-Agent Decomposition:**

```
ConsolidationAgent (Coordinator)
├── Sub-Agent 1: ChunkGenerator (SemanticChunker)
├── Sub-Agent 2: EmbeddingService (BGE)
└── Sub-Agent 3: VectorStorage (Qdrant upsert)
```

**Parallelization Strategy:**
- Chunk → Embed can overlap with previous storage
- Batch operations can parallelize across document chunks

**Expected Speedup:** 1.3x

**Feasibility:** LOW - I/O bound operations, diminishing returns

---

### Node 6: Domain Theme Agents (IMPLEMENTED - True Sub-Agents)

**What was changed:**
- Converted from function-based processing to **TRUE SUB-AGENTS** using Worker Pattern
- Each theme has its own class with `run()` method (autonomous behavior)
- Factory pattern for conditional sub-agent spawning

**Implementation (Worker Pattern):**
```python
# backend/app/services/agents/theme_agent.py

@dataclass
class BaseThemeAgent:
    """Base class for all theme-specific sub-agents."""
    theme_label: str
    theme_focus: str
    
    def _build_context(self, documents: list[dict]) -> str: ...
    def _build_prompt(self, theme_label: str, focus: str, context: str, doc_count: int) -> str: ...
    def _parse_response(self, output: str, theme_label: str) -> list[dict]: ...
    
    async def run(self, documents: list[dict]) -> list[dict]:
        """Execute the sub-agent's autonomous reasoning."""
        # Full LLM workflow: build context → generate prompt → call Gemini → parse response
        ...

@dataclass
class InfrastructureAgent(BaseThemeAgent):
    """Sub-agent for Infrastructure domain insights."""
    theme_label: str = "Infrastructure"
    theme_focus: str = "Focus ONLY on infrastructure topics..."

@dataclass
class HealthAgent(BaseThemeAgent): ...
@dataclass
class SafetyAgent(BaseThemeAgent): ...
@dataclass
class TourismAgent(BaseThemeAgent): ...
@dataclass
class EconomyAgent(BaseThemeAgent): ...
@dataclass
class EnvironmentAgent(BaseThemeAgent): ...

def get_theme_agent(theme_key: str) -> BaseThemeAgent:
    """Factory function for conditional sub-agent spawning."""
    agents = {
        "infrastructure": InfrastructureAgent,
        "health": HealthAgent,
        "safety": SafetyAgent,
        "tourism": TourismAgent,
        "economy": EconomyAgent,
        "environment": EnvironmentAgent,
    }
    return agents.get(theme_key.lower(), GenericAgent)()
```

**AOSE Compliance:**
- ✓ **Autonomy**: Each agent has its own `run()` method
- ✓ **State**: Class attributes (theme_label, theme_focus)
- ✓ **Identity**: Distinct class instances
- ✓ **Goal Delegation**: Factory creates agents for specific themes

**Integration in Node 6:**
```python
# backend/app/services/insights/nodes.py

def _synthesize_single_theme(theme_key: str, docs: list[WebDocument], contexts: Any) -> list[Insight]:
    """Spawn TRUE SUB-AGENT for theme processing."""
    from ..agents.theme_agent import get_theme_agent
    
    # Spawn sub-agent via factory
    agent = get_theme_agent(theme_key)
    logger.info(f"[ThemeAgent] Spawned {type(agent).__name__} for '{label}'")
    
    # Run autonomous reasoning
    insights = asyncio.run(agent.run(enriched_docs))
    
    # Convert to Insight objects
    ...
```

**Assessment:** Worker Pattern sub-agents IMPLEMENTED for thesis defense credibility

---

### Node 4c: CredibilityAgent - 5-Signal True Sub-Agents (IMPLEMENTED)

**What was changed:**
- Converted from sequential function calls to **TRUE SUB-AGENTS** using Worker Pattern
- Each credibility signal is now an independent class with `score()` method (autonomous behavior)
- No shared base class (each signal measures orthogonal dimensions with unique algorithms)
- Parallel execution via asyncio.gather for maximum throughput

**Implementation (Independent Worker Pattern):**
```python
# backend/app/services/agents/credibility_agent.py

@dataclass  
class DomainTrustAgent:
    """Sub-agent for domain reputation scoring."""
    domain_trust_scores: Dict[str, float]
    
    async def score(self, doc: WebDocument) -> float:
        """Score based on domain reputation (gov.ph = 0.95, social = 0.45)."""
        url = doc.url.lower()
        for domain, score in self.domain_trust_scores.items():
            if domain in url:
                return score
        return 0.5  # Default for unknown domains


@dataclass
class CrossReferenceAgent:
    """Sub-agent for semantic cross-reference verification."""
    embedding_service: EmbeddingService
    
    async def score(self, doc: WebDocument, all_docs: list[WebDocument]) -> float:
        """Score based on cosine similarity with corroborating documents."""
        if len(all_docs) < 2:
            return 0.5
        
        doc_emb = await self.embedding_service.embed(doc.content[:500])
        similarities = []
        
        for other in all_docs:
            if other.id != doc.id:
                other_emb = await self.embedding_service.embed(other.content[:500])
                sim = cosine_similarity(doc_emb, other_emb)
                similarities.append(sim)
        
        return float(np.mean(similarities)) if similarities else 0.5


@dataclass
class FactCheckAgent:
    """Sub-agent for Google Fact Check API verification."""
    fact_check_api_key: str
    
    async def score(self, doc: WebDocument) -> float:
        """Query Google Fact Check API for claim verification."""
        # API call to Google Fact Check API
        claims = extract_claims(doc.content)
        for claim in claims:
            result = await self._query_fact_check(claim)
            if result and result.claim_review_rating:
                return result.claim_review_rating / 5.0
        return 0.5  # No fact-checks found


@dataclass
class LLMAnalysisAgent:
    """Sub-agent for LLM-based content quality analysis."""
    llm: ChatGoogleGenerativeAI
    
    async def score(self, doc: WebDocument) -> float:
        """Analyze content for misinformation patterns via Gemini."""
        prompt = f"""Analyze this text for credibility indicators.
        
        Text: {doc.content[:1000]}
        
        Return a score 0.0-1.0 based on:
        - Clickbait language
        - Conspiracy framing
        - False certainty
        - Social proof manipulation
        - Balanced vs sensational language
        
        Score: """
        
        response = await self.llm.generate(prompt)
        return float(response.strip())


@dataclass
class TavilyAgent:
    """Sub-agent for web cross-reference verification."""
    tavily_api_key: str
    
    async def score(self, doc: WebDocument) -> float:
        """Verify claims against real-time web search."""
        claims = extract_claims(doc.content[:500])
        if not claims:
            return 0.5
        
        # Search for corroborating evidence
        results = await self._tavily_search(claims[0])
        
        # Score based on number of authoritative sources
        authoritative = sum(1 for r in results if self._is_authoritative(r.url))
        return min(1.0, 0.3 + (authoritative * 0.15))


# Note: Unlike Theme Agents, Credibility sub-agents have NO shared base class
# Each measures an ORTHOGONAL dimension with completely different algorithms:
# - DomainTrust: Lookup table
# - CrossReference: BGE embeddings + cosine similarity
# - FactCheck: Google Fact Check API
# - LLMAnalysis: Gemini pattern recognition  
# - Tavily: Web search + source authority
#
# Shared code would OVER-ENGINEER orthogonal concerns.
```

**AOSE Compliance:**
- ✓ **Autonomy**: Each agent has its own `score()` method with independent logic
- ✓ **State**: Class attributes specific to each agent's algorithm
- ✓ **Identity**: Distinct class instances (no shared base class needed)
- ✓ **Goal Delegation**: Each agent pursues its specific credibility dimension

**Parallel Execution in CredibilityAgent:**
```python
# backend/app/services/agents/credibility_agent.py

async def verify_document(doc: WebDocument, all_docs: list[WebDocument]) -> dict:
    """Coordinate all 5 sub-agents in parallel."""
    
    # Spawn all sub-agents concurrently
    domain_score, crossref_score, factcheck_score, llm_score, tavily_score = await asyncio.gather(
        domain_trust_agent.score(doc),
        crossref_agent.score(doc, all_docs),
        factcheck_agent.score(doc),
        llm_agent.score(doc),
        tavily_agent.score(doc)
    )
    
    # Compute weighted ensemble
    credibility_score = (
        0.25 * domain_score +
        0.20 * crossref_score +
        0.15 * factcheck_score +
        0.20 * llm_score +
        0.20 * tavily_score
    )
    
    return {
        "credibility_score": credibility_score,
        "domain_trust": domain_score,
        "cross_reference": crossref_score,
        "fact_check": factcheck_score,
        "llm_analysis": llm_score,
        "tavily": tavily_score
    }
```

**Assessment:** Worker Pattern sub-agents IMPLEMENTED for thesis defense credibility

---

### Node 7: CoordinatorAgent (Narrative Synthesis)

**Current Implementation:**
```
Single LLM call: Gemini 2.5 Flash Lite
Input: window, focus_areas, documents, theme_insights
Output: summary_text, insights_payload
```

**Proposed Sub-Agent Decomposition:**

```
CoordinatorAgent (Coordinator)
├── Sub-Agent 1: InsightIntegrator (merge theme insights)
├── Sub-Agent 2: SummaryGenerator (generate narrative)
└── Sub-Agent 3: ResponseFormatter (format final JSON)
```

**Parallelization Strategy:**
- Insight integration and summary generation can overlap
- Final formatting is cheap (no parallelization benefit)

**Expected Speedup:** 1.2x

**Feasibility:** LOW - single LLM call dominates latency

---

## Recommended Implementation Priority

### Phase 1: High-Impact, Low-Effort Changes

1. **CredibilityAgent 5-Signal Parallelization** (IMPLEMENTED)
   - Impact: 3-5x speedup on Node 4
   - Status: True sub-agents with Worker Pattern implemented
   - See: "Node 4b: CredibilityAgent - 5-Signal True Sub-Agents (IMPLEMENTED)"

2. **ThemeRouterAgent Document-Level Parallelization** (MEDIUM PRIORITY)
   - Impact: 2-3x speedup on Node 4 routing
   - Effort: Low - vectorized operations
   - Risk: Low - mathematical operations are deterministic

### Phase 2: Medium-Impact, Medium-Effort Changes

3. **QueryOrchestratorTool Parallelization** (MEDIUM PRIORITY)
   - Impact: 1.5-2x speedup on Node 1
   - Effort: Medium - refactor ReAct loop
   - Risk: Medium - changes core reasoning flow

4. **Memory Recall Parallelization** (MEDIUM PRIORITY)
   - Impact: 1.5x speedup on Node 3
   - Effort: Medium - concurrent vector searches
   - Risk: Low - independent operations

### Phase 3: Low-Impact, Low-Priority Changes

5. **Memory Consolidation Optimization**
6. **CoordinatorAgent Pipeline**

---

## Implementation Examples

### Example 1: CredibilityAgent 5-Signal Parallelization

```python
# backend/app/services/agents/credibility_agent.py

async def verify_document_parallel(doc: WebDocument) -> WebDocument:
    """Verify document using all 5 signals in parallel."""
    
    # Run all 5 signals concurrently
    domain_trust, semantic_score, fact_check, llm_pattern, tavily = await asyncio.gather(
        self._check_domain_trust(doc),
        self._check_semantic_cross_reference(doc),
        self._query_fact_check_api(doc),
        self._analyze_llm_patterns(doc),
        self._verify_tavily(doc)
    )
    
    # Compute weighted ensemble
    credibility_score = (
        0.25 * domain_trust +
        0.20 * semantic_score +
        0.15 * fact_check +
        0.20 * llm_pattern +
        0.20 * tavily
    )
    
    return doc.model_copy(update={
        "credibility_score": credibility_score,
        "metadata": {
            **doc.metadata,
            "domain_trust": domain_trust,
            "semantic_score": semantic_score,
            "fact_check": fact_check,
            "llm_pattern": llm_pattern,
            "tavily": tavily
        }
    })
```

### Example 2: ThemeRouterAgent Parallel Document Routing

```python
# backend/app/services/agents/theme_router_agent.py

async def route_documents_parallel(self, documents: list[WebDocument]) -> dict[str, list[WebDocument]]:
    """Route documents to themes using parallel similarity computation."""
    
    # Pre-compute theme embeddings (cached)
    theme_embeddings = self._compute_theme_embeddings()
    
    # Batch embed all documents
    doc_texts = [f"{doc.title}. {doc.snippet[:200]}" for doc in documents]
    doc_embeddings = await self.embedding_service.embed_batch(doc_texts)
    
    # Route each document to best theme (parallel similarity computation)
    async def route_single_doc(doc_idx: int) -> tuple[int, str]:
        doc_emb = doc_embeddings[doc_idx]
        best_theme = None
        best_score = 0
        
        for theme_key, theme_emb in theme_embeddings.items():
            score = self._cosine_similarity(doc_emb, theme_emb)
            if score > best_score:
                best_score = score
                best_theme = theme_key
        
        return doc_idx, best_theme
    
    # Run all document routing in parallel
    routes = await asyncio.gather(*[
        route_single_doc(i) for i in range(len(documents))
    ])
    
    # Build theme buckets
    theme_docs = {key: [] for key in theme_embeddings.keys()}
    for doc_idx, theme_key in routes:
        theme_docs[theme_key].append(documents[doc_idx])
    
    return theme_docs
```

---

## Performance Impact Summary

| Node | Current Latency | With Sub-Agents | Speedup | Total Pipeline Impact |
|------|-----------------|-----------------|---------|----------------------|
| Node 1 | ~2s | ~1.2s | 1.5x | -0.8s |
| Node 2 | ~5s | ~5s | 1x | 0s |
| Node 3 | ~1s | ~0.7s | 1.5x | -0.3s |
| Node 4 | ~10s | ~3s | 3.3x | -7s |
| Node 5 | ~2s | ~1.5s | 1.3x | -0.5s |
| Node 6 | ~8s | ~8s | 1x | 0s |
| Node 7 | ~2s | ~1.7s | 1.2x | -0.3s |
| **TOTAL** | **~30s** | **~21s** | **1.4x** | **-9s** |

**Projected End-to-End Latency: 30s → 21s (30% improvement)**

---

## Conclusion

The highest-impact optimization is **parallelizing the 5 credibility signals** in Node 4. This alone can reduce Node 4 latency from ~10s to ~3s, providing a 7-second improvement in the overall pipeline.

The secondary optimization is **parallel document routing** in ThemeRouterAgent, which can provide an additional 2-3x speedup on theme classification.

These changes maintain the existing architecture while adding sub-agent parallelism where it matters most: **I/O-bound API calls** (credibility signals) and **embarrassingly parallel computations** (theme similarity scoring).
