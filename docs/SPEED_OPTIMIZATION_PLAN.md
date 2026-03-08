# Speed Optimization Plan - Maximum Performance Within Constraints

## Current Bottlenecks (100 docs)

1. **Tavily Agent**: ~40s (Semaphore=3, rate limited)
2. **LLM Analysis**: ~5s (batch_size=20, 20 threads)
3. **Fact Check**: ~5s (Semaphore=10)
4. **Sentiment Agent**: ~12s (batch_size=30)

**Total Node 4 Time**: ~40s (bottleneck: Tavily)

---

## Optimization Strategy

### 🎯 Goal: Reduce from 40s → 15-20s

### Constraints:
- Hugging Face: 2 vCPU, 16GB RAM
- Tavily API: Rate limits (unknown exact limit)
- Google Fact Check API: Rate limits
- Gemini API: Rate limits

---

## 1. PRIORITY-BASED TAVILY VERIFICATION (Biggest Win)

**Problem**: Verifying all 100 docs takes 40s  
**Solution**: Only verify documents that need it

### Strategy A: Credibility-Based Sampling
```python
# Only verify LOW credibility documents (where it matters most)
if domain_score < 0.6 or cross_ref_score < 0.5:
    run_tavily = True
else:
    run_tavily = False  # Skip high-trust sources
```

**Impact**: 
- Verify ~30% of docs (30 instead of 100)
- Time: 40s → 12s (**28s saved**)

### Strategy B: Two-Tier Verification
```python
# Tier 1: Fast signals only (domain + cross-ref + LLM)
# Tier 2: Add Tavily only for suspicious content

if llm_misinfo_risk in ["high", "medium"]:
    run_tavily = True  # Verify suspicious content
elif credibility_score < 0.5:
    run_tavily = True  # Verify low-credibility
else:
    run_tavily = False  # Trust other signals
```

**Impact**:
- Verify ~20% of docs (20 instead of 100)
- Time: 40s → 8s (**32s saved**)

---

## 2. INCREASE TAVILY CONCURRENCY (Test API Limits)

**Current**: Semaphore(3) with 100ms delays  
**Proposed**: Semaphore(5) with 50ms delays

```python
# backend/app/services/agents/credibility_agent.py
async def _batch_tavily_verify(self, docs, domains, embeddings):
    semaphore = asyncio.Semaphore(5)  # ← Increase from 3
    
    async def verify_one(doc, domain, idx):
        async with semaphore:
            if idx > 0:
                await asyncio.sleep(0.05)  # ← Reduce from 0.1
```

**Impact**:
- 100 docs ÷ 5 concurrent × 2s = 40s → 24s (**16s saved**)
- Risk: May hit rate limits (need testing)

---

## 3. ADAPTIVE RATE LIMITING (Smart Throttling)

**Problem**: Fixed delays waste time when API is healthy  
**Solution**: Adjust delays based on success rate

```python
class AdaptiveRateLimiter:
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.current_delay = 0.1
    
    async def wait(self):
        success_rate = self.success_count / max(1, self.success_count + self.error_count)
        
        if success_rate > 0.95:
            self.current_delay = max(0.02, self.current_delay * 0.9)  # Speed up
        elif success_rate < 0.80:
            self.current_delay = min(0.5, self.current_delay * 1.5)  # Slow down
        
        await asyncio.sleep(self.current_delay)
```

**Impact**:
- Optimal speed without hitting rate limits
- Time: 40s → 25-30s (**10-15s saved**)

---

## 4. PARALLEL FACT CHECK + TAVILY (Remove Sequential Bottleneck)

**Current**: Both run in the same asyncio.gather, but share event loop  
**Optimization**: Already optimal (both are concurrent I/O)

**No change needed** - already running in parallel via asyncio.gather

---

## 5. INCREASE LLM BATCH SIZE (Fewer API Calls)

**Current**: batch_size=20 docs per Gemini call  
**Proposed**: batch_size=30 docs (match sentiment agent)

```python
# backend/app/services/agents/credibility_agent.py
class LLMCredibilityAnalyzer:
    def __init__(self):
        self.batch_size = 30  # ← Increase from 20
```

**Impact**:
- 100 docs: 5 batches → 4 batches
- Time: 5s → 4s (**1s saved**)
- Risk: Larger prompts may hit token limits

---

## 6. SKIP FACT CHECK FOR HIGH-TRUST DOMAINS (Selective Verification)

**Problem**: Fact-checking gov.ph and major news is redundant  
**Solution**: Skip fact check for tier-1 domains

```python
# backend/app/services/agents/credibility_agent.py
SKIP_FACT_CHECK_DOMAINS = {
    "gov.ph", "pia.gov.ph", "pna.gov.ph",  # Government
    "inquirer.net", "philstar.com", "gmanetwork.com",  # Major news
}

async def _batch_fact_check(self, docs):
    # Filter out high-trust domains
    docs_to_check = [
        d for d in docs 
        if _extract_domain(str(d.url)) not in SKIP_FACT_CHECK_DOMAINS
    ]
```

**Impact**:
- Check ~60% of docs (60 instead of 100)
- Time: 5s → 3s (**2s saved**)

---

## 7. INCREASE SENTIMENT BATCH SIZE (Fewer Iterations)

**Current**: batch_size=30 docs  
**Proposed**: batch_size=50 docs (if memory allows)

```python
# backend/app/services/agents/sentiment_agent.py
class SentimentAgent:
    def __init__(self):
        self.batch_size = 50  # ← Increase from 30
```

**Impact**:
- 100 docs: 4 batches → 2 batches
- Time: 12s → 8s (**4s saved**)
- Risk: May OOM on 16GB RAM (need testing)

---

## 8. CACHE EMBEDDINGS (Avoid Recomputation)

**Problem**: Computing embeddings for 100 docs takes ~100ms  
**Solution**: Cache embeddings for documents we've seen before

```python
# backend/app/services/rag/embeddings.py
from functools import lru_cache

class EmbeddingService:
    def __init__(self):
        self._cache = {}  # url -> embedding
    
    def embed_with_cache(self, text: str, doc_url: str) -> list[float]:
        if doc_url in self._cache:
            return self._cache[doc_url]
        
        embedding = self.embed(text)
        self._cache[doc_url] = embedding
        return embedding
```

**Impact**:
- First run: 100ms
- Subsequent runs: <10ms (**90ms saved per run**)

---

## 9. EARLY TERMINATION FOR LOW-PRIORITY DOCS (Quality-Speed Tradeoff)

**Problem**: Processing all 100 docs equally  
**Solution**: Process top 50 docs fully, remaining 50 with fast signals only

```python
# backend/app/services/agents/credibility_agent.py
async def run(self, documents: list[WebDocument]) -> list[WebDocument]:
    # Sort by relevance
    sorted_docs = sorted(documents, key=lambda d: d.metadata.get("_score", 0), reverse=True)
    
    high_priority = sorted_docs[:50]   # Full analysis
    low_priority = sorted_docs[50:]    # Fast signals only
    
    # Full analysis for high-priority
    high_enriched = await self._full_analysis(high_priority)
    
    # Fast analysis for low-priority (skip Tavily + Fact Check)
    low_enriched = await self._fast_analysis(low_priority)
    
    return high_enriched + low_enriched
```

**Impact**:
- Process 50 docs fully, 50 docs fast
- Time: 40s → 22s (**18s saved**)

---

## 10. PARALLEL EMBEDDING COMPUTATION (GPU Acceleration)

**Current**: Sequential embedding computation  
**Proposed**: Batch embedding with larger batch_size

```python
# backend/app/services/agents/credibility_agent.py
embeddings = embedding_service.embed_batch(doc_texts, batch_size=32)  # ← Increase from 16
```

**Impact**:
- 100 docs: 7 batches → 4 batches
- Time: 100ms → 60ms (**40ms saved**)

---

## Implementation Priority

### Phase 1: Quick Wins (No Risk)
1. ✅ **Priority-Based Tavily** (Strategy B) - **32s saved**
2. ✅ **Skip Fact Check for High-Trust** - **2s saved**
3. ✅ **Increase LLM Batch Size** - **1s saved**
4. ✅ **Increase Embedding Batch Size** - **40ms saved**

**Total Phase 1 Savings**: ~35s  
**New Time**: 40s → 5s

### Phase 2: Test & Validate (Low Risk)
5. ⚠️ **Increase Tavily Concurrency** - **16s saved** (test rate limits)
6. ⚠️ **Increase Sentiment Batch Size** - **4s saved** (test memory)
7. ⚠️ **Adaptive Rate Limiting** - **10-15s saved** (implement carefully)

**Total Phase 2 Savings**: ~30s  
**New Time**: 5s → 3s (if Phase 1 not applied) or maintain 5s with better reliability

### Phase 3: Advanced (Medium Risk)
8. ⚠️ **Early Termination** - **18s saved** (quality tradeoff)
9. ⚠️ **Embedding Cache** - **90ms saved per run** (memory overhead)

---

## Recommended Configuration

### Conservative (Safe for Production)
```python
# Tavily
TAVILY_SEMAPHORE = 3
TAVILY_DELAY = 0.1
TAVILY_PRIORITY_THRESHOLD = 0.5  # Only verify if credibility < 0.5

# Fact Check
SKIP_FACT_CHECK_DOMAINS = {"gov.ph", "pia.gov.ph", ...}

# LLM
LLM_BATCH_SIZE = 25  # Moderate increase

# Sentiment
SENTIMENT_BATCH_SIZE = 30  # Keep current

# Embeddings
EMBEDDING_BATCH_SIZE = 24  # Moderate increase
```

**Expected Time**: 40s → 12-15s (**25-28s saved**)

### Aggressive (Maximum Speed)
```python
# Tavily
TAVILY_SEMAPHORE = 5
TAVILY_DELAY = 0.05
TAVILY_PRIORITY_THRESHOLD = 0.6  # Verify fewer docs
TAVILY_MISINFO_ONLY = True  # Only verify if LLM flags misinfo

# Fact Check
SKIP_FACT_CHECK_DOMAINS = {"gov.ph", "pia.gov.ph", ...}
FACT_CHECK_SEMAPHORE = 15  # Increase from 10

# LLM
LLM_BATCH_SIZE = 30

# Sentiment
SENTIMENT_BATCH_SIZE = 50

# Embeddings
EMBEDDING_BATCH_SIZE = 32
```

**Expected Time**: 40s → 5-8s (**32-35s saved**)

---

## Testing Plan

1. **Baseline**: Run with current config, measure time
2. **Phase 1**: Apply conservative optimizations, measure
3. **Load Test**: Test with 200 docs to verify scaling
4. **Rate Limit Test**: Gradually increase Tavily concurrency until errors
5. **Memory Test**: Monitor RAM usage with larger batches
6. **Quality Test**: Compare credibility scores before/after optimizations

---

## Monitoring Metrics

```python
# Add to metrics collector
metrics.record_optimization_metrics(
    tavily_skipped=skipped_count,
    tavily_verified=verified_count,
    fact_check_skipped=fc_skipped,
    avg_tavily_delay=avg_delay,
    rate_limit_errors=error_count,
)
```

---

## Expected Results

| Configuration | Time | Speedup | Risk |
|---------------|------|---------|------|
| Current | 40s | 1x | None |
| Conservative | 12-15s | 2.7-3.3x | Low |
| Aggressive | 5-8s | 5-8x | Medium |
| With Early Termination | 3-5s | 8-13x | High (quality loss) |

---

**Recommendation**: Start with **Conservative** config, monitor for 1 week, then gradually move to **Aggressive** if no issues.

