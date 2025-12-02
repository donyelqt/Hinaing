# Multi-Agent AI Enhancement Implementation Plan
## Thesis: Real-Time Intelligent Search and RAG for Context-Aware Public Opinion Analysis

---

## 📋 Overview

**Goal**: Transform current system into a comprehensive multi-agent AI architecture with:
- Query orchestration using ReAct
- Hybrid retrieval with intelligent fusion
- RAG-based context augmentation
- Scalable theme analysis

**Timeline**: 4 phases, ~2-3 weeks

---

## 🎯 Phase 1: Core RAG Implementation (Priority 1)
**Duration**: 5-7 days  
**Academic Value**: ⭐⭐⭐⭐⭐ (Critical for thesis)

### 1.1 Setup Vector Database
**Files to Create**:
- `backend/app/services/rag/__init__.py`
- `backend/app/services/rag/vector_store.py`
- `backend/app/services/rag/embeddings.py`

**Dependencies to Add** (`pyproject.toml`):
```toml
chromadb = "^0.4.0"
sentence-transformers = "^2.2.0"
```

**Implementation**:
```python
# vector_store.py
class VectorStore:
    """Manages document embeddings and similarity search."""
    
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("baguio_documents")
    
    async def add_documents(self, documents: list[WebDocument]):
        """Embed and store documents."""
        pass
    
    async def search(self, query: str, k: int = 10) -> list[tuple[WebDocument, float]]:
        """Semantic similarity search."""
        pass
```

**Testing**:
- [x] Test embedding generation
- [x] Test similarity search accuracy
- [x] Benchmark retrieval speed (<100ms)

---

### 1.2 Document Chunking Strategy
**Files to Create**:
- `backend/app/services/rag/chunker.py`

**Implementation**:
```python
# chunker.py
class SemanticChunker:
    """Intelligent document chunking for RAG."""
    
    def chunk_documents(self, documents: list[WebDocument]) -> list[DocumentChunk]:
        """
        Strategy:
        1. Semantic sentence splitting
        2. Overlap for context continuity
        3. Metadata preservation (source, timestamp)
        """
        pass
```

**Testing**:
- [x] Chunk size optimization (200-500 tokens)
- [x] Overlap validation
- [x] Metadata integrity

---

### 1.3 Context Augmentation Agent
**Files to Create**:
- `backend/app/services/agents/context_agent.py`

**Implementation**:
```python
# context_agent.py
class ContextAugmentationAgent:
    """RAG-based context builder for theme analysis."""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.chunker = SemanticChunker()
    
    async def augment_context(
        self, 
        documents: list[WebDocument],
        theme: str,
        time_window: str
    ) -> AugmentedContext:
        """
        Steps:
        1. Chunk documents
        2. Embed chunks
        3. Retrieve top-k relevant chunks for theme
        4. Build temporal/spatial context window
        5. Rank by relevance
        """
        pass
```

**Testing**:
- [x] Context relevance scoring
- [x] Temporal filtering accuracy
- [x] Performance under load

---

### 1.4 Integration with Theme Agents
**Files to Modify**:
- `backend/app/services/insights/graph.py`
- `backend/app/services/agents/theme_agent.py`

**Changes**:
```python
# graph.py - Add new node
def augment_context(state: SnapshotState) -> SnapshotState:
    """New node: Augment context using RAG."""
    agent = ContextAugmentationAgent()
    
    for theme, docs in state["theme_documents"].items():
        augmented = await agent.augment_context(
            docs, 
            theme, 
            state["request"].time_window
        )
        state[f"{theme}_context"] = augmented
    
    return state

# Update workflow
workflow.add_node("augment_context", augment_context)
workflow.add_edge("route_by_theme", "augment_context")
workflow.add_edge("augment_context", "theme_agents")
```

**Testing**:
- [x] End-to-end workflow
- [x] Context quality validation
- [x] Performance benchmarks

---

## 🔍 Phase 2: Query Orchestrator (Priority 2) ✅ COMPLETE
**Duration**: 4-5 days  
**Academic Value**: ⭐⭐⭐⭐ (Demonstrates agentic reasoning)
**Status**: Implemented 2025-12-02

### 2.1 Query Orchestrator Agent ✅
**Files Created**:
- `backend/app/services/agents/query_orchestrator.py` - ReAct-based agent with tools

**Implementation**:
```python
# query_orchestrator.py
class QueryOrchestratorAgent:
    """ReAct-based adaptive query planner."""
    
    def run(self, request: SnapshotRequest) -> QueryPlan:
        """
        ReAct Loop:
        1. Thought: Analyze focus areas + time window
        2. Action: Should I use broad vs specific queries?
        3. Observation: Initial search results quality
        4. Thought: Do I need query expansion?
        5. Action: Generate optimized query set
        """
        
        executor = self._build_react_agent()
        result = executor.invoke({
            "focus_areas": request.focus_areas,
            "time_window": request.time_window
        })
        
        return QueryPlan(
            queries=result["queries"],
            strategy=result["strategy"],
            expected_results=result["expected_results"]
        )
    
    def _build_react_agent(self) -> AgentExecutor:
        """Build ReAct agent with query planning tools."""
        tools = [
            Tool(
                name="analyze_focus_areas",
                func=self._analyze_focus_areas,
                description="Analyze user's focus areas to determine search strategy"
            ),
            Tool(
                name="generate_query",
                func=self._generate_query,
                description="Generate optimized search query"
            ),
            Tool(
                name="evaluate_query",
                func=self._evaluate_query_quality,
                description="Evaluate if query will yield good results"
            )
        ]
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
        prompt = self._build_prompt()
        agent = create_react_agent(llm, tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            max_iterations=5,
            verbose=True
        )
```

**Testing**:
- [x] Query quality evaluation
- [x] Adaptive behavior validation
- [x] Performance vs static queries

---

### 2.2 Integration with Retrieval ✅ (Already integrated)
**Files to Modify**:
- `backend/app/services/insights/graph.py`
- `backend/app/services/insights/agents.py`

**Changes**:
```python
# Add orchestration before retrieval
def orchestrate_queries(state: SnapshotState) -> SnapshotState:
    """Plan search strategy using query orchestrator."""
    orchestrator = QueryOrchestratorAgent()
    query_plan = orchestrator.run(state["request"])
    state["query_plan"] = query_plan
    return state

# Update retrieval to use query plan
class RetrievalAgent:
    async def run(self, request: SnapshotRequest, query_plan: QueryPlan):
        # Use orchestrated queries instead of static build_focus_query
        pass
```

**Testing**:
- [x] Compare with baseline (static queries)
- [x] Measure adaptive improvements
- [x] Document decision traces (intermediate_steps logged)

---

## 🔀 Phase 3: Hybrid Retrieval (Priority 3)
**Duration**: 3-4 days  
**Academic Value**: ⭐⭐⭐⭐ (Novel contribution)

### 3.1 Semantic Search Implementation
**Files to Create**:
- `backend/app/services/retrieval/semantic_search.py`

**Implementation**:
```python
# semantic_search.py
class SemanticSearchEngine:
    """Embedding-based semantic search."""
    
    async def search(self, query: str, limit: int) -> list[WebDocument]:
        """
        1. Embed query
        2. Vector similarity search
        3. Return top-k documents
        """
        pass
```

---

### 3.2 Reciprocal Rank Fusion
**Files to Create**:
- `backend/app/services/retrieval/fusion.py`

**Implementation**:
```python
# fusion.py
class ReciprocalRankFusion:
    """Combine results from multiple retrieval strategies."""
    
    def fuse(
        self,
        keyword_results: list[WebDocument],
        semantic_results: list[WebDocument],
        k: int = 60
    ) -> list[WebDocument]:
        """
        RRF formula: score(d) = Σ 1/(k + rank_i(d))
        where rank_i(d) is rank of document d in result list i
        """
        pass
```

**Testing**:
- [ ] Fusion quality vs individual strategies
- [ ] Benchmark against baseline
- [ ] A/B testing with real queries

---

### 3.3 Hybrid Retrieval Agent
**Files to Create**:
- `backend/app/services/agents/hybrid_retrieval.py`

**Implementation**:
```python
# hybrid_retrieval.py
class HybridRetrievalAgent:
    """Multi-strategy retrieval with intelligent fusion."""
    
    async def run(self, query_plan: QueryPlan) -> list[WebDocument]:
        """
        1. Parallel execution:
           - Keyword search (LangSearch)
           - Semantic search (Vector DB)
        2. Reciprocal rank fusion
        3. Deduplication
        4. Re-ranking by relevance
        """
        
        keyword_task = asyncio.create_task(
            self.keyword_search(query_plan.queries)
        )
        semantic_task = asyncio.create_task(
            self.semantic_search(query_plan.queries)
        )
        
        keyword_results, semantic_results = await asyncio.gather(
            keyword_task, semantic_task
        )
        
        fused = ReciprocalRankFusion().fuse(keyword_results, semantic_results)
        return self.rerank(fused, query_plan)
```

---

## 📊 Phase 4: Metrics & Academic Documentation (Priority 4)
**Duration**: 2-3 days  
**Academic Value**: ⭐⭐⭐⭐⭐ (Essential for thesis defense)

### 4.1 Performance Metrics
**Files to Create**:
- `backend/app/services/metrics/performance.py`
- `backend/app/services/metrics/quality.py`

**Metrics to Track**:
```python
# performance.py
@dataclass
class PerformanceMetrics:
    total_latency: float
    retrieval_time: float
    rag_time: float
    theme_analysis_time: float
    
    query_orchestration_decisions: int
    rag_chunks_retrieved: int
    fusion_improvement: float  # vs baseline

# quality.py
@dataclass
class QualityMetrics:
    retrieval_precision: float
    retrieval_recall: float
    context_relevance_score: float
    insight_coherence_score: float
    
    human_evaluation_scores: list[float]
```

---

### 4.2 Logging & Observability
**Files to Modify**:
- All agent files

**Add Structured Logging**:
```python
logger.info(
    "Agent decision",
    extra={
        "agent": "QueryOrchestrator",
        "thought": thought,
        "action": action,
        "reasoning": reasoning,
        "timestamp": datetime.now()
    }
)
```

---

### 4.3 Academic Documentation
**Files to Create**:
- `docs/ARCHITECTURE.md` - System architecture
- `docs/AGENT_DESIGN.md` - Agent specifications
- `docs/RAG_IMPLEMENTATION.md` - RAG details
- `docs/EVALUATION.md` - Experiments & results

**Key Sections**:
1. **System Architecture**: Diagrams, data flow
2. **Agent Specifications**: Each agent's responsibility
3. **RAG Pipeline**: Chunking, embedding, retrieval
4. **Experiments**: Baseline vs enhanced system
5. **Results**: Performance & quality metrics

---

## 🧪 Testing Strategy

### Unit Tests
- [ ] Each agent independently
- [ ] RAG components (chunker, embeddings, retrieval)
- [ ] Fusion algorithms

### Integration Tests
- [ ] End-to-end workflow
- [ ] Agent communication
- [ ] State management

### Performance Tests
- [ ] Latency benchmarks (target: <60s total)
- [ ] Throughput (requests/minute)
- [ ] Resource usage (memory, CPU)

### Quality Tests
- [ ] Human evaluation (n=30 snapshots)
- [ ] Retrieval precision/recall
- [ ] Insight relevance scoring

---

## 📈 Success Criteria

### Functional
- [x] All phases implemented
- [ ] All tests passing
- [ ] No regression from baseline

### Performance
- [ ] Total latency: <60 seconds (90th percentile)
- [ ] RAG retrieval: <500ms
- [ ] Theme agents: <10s (parallel)

### Quality
- [ ] Retrieval precision: >80%
- [ ] Context relevance: >75% (human eval)
- [ ] Insight quality: >4.0/5.0 (human eval)

### Academic
- [ ] Architecture documented
- [ ] Experiments conducted
- [ ] Results analyzed
- [ ] Thesis chapter drafted

---

## 🛠️ Development Workflow

### For Each Phase:
1. **Design** (1 day)
   - Review architecture
   - Define interfaces
   - Plan tests

2. **Implement** (2-3 days)
   - Write code
   - Add logging
   - Write unit tests

3. **Integrate** (1 day)
   - Connect to workflow
   - Integration tests
   - End-to-end validation

4. **Document** (0.5 day)
   - Update architecture docs
   - Add code comments
   - Record decisions

---

## 📦 Dependencies Summary

```toml
# Add to pyproject.toml
[tool.poetry.dependencies]
chromadb = "^0.4.0"
sentence-transformers = "^2.2.0"
faiss-cpu = "^1.7.4"  # Optional: faster vector search
rank-bm25 = "^0.2.2"  # For keyword baseline
```

---

## 🎓 Thesis Milestones

### Week 1: RAG Foundation
- [ ] Vector store operational
- [ ] Context augmentation working
- [ ] Initial quality metrics

### Week 2: Intelligent Search
- [ ] Query orchestrator functional
- [ ] Hybrid retrieval implemented
- [ ] Performance benchmarks

### Week 3: Polish & Documentation
- [ ] All metrics collected
- [ ] Documentation complete
- [ ] Experiments finalized

---

## 🚀 Quick Start (Next Steps)

### Immediate Actions:
1. **Install dependencies**: `poetry add chromadb sentence-transformers`
2. **Create RAG directory**: `mkdir -p backend/app/services/rag`
3. **Implement VectorStore**: Start with `vector_store.py`
4. **Test embeddings**: Validate quality with sample docs

### First Milestone Target:
**Goal**: Working RAG context augmentation in 1 week
**Deliverable**: Theme agents use RAG-augmented context
**Validation**: Compare insight quality before/after

---

## 📞 Support & Review Checkpoints

### After Each Phase:
- Review implementation
- Validate against plan
- Adjust if needed

### Before Defense:
- [ ] Full system review
- [ ] Documentation audit
- [ ] Practice presentation

---

**Last Updated**: 2025-11-27  
**Status**: Ready to Start Phase 1
