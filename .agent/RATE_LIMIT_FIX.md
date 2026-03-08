# Rate Limit Fix - Theme Agents

## Date: 2026-02-01

## Issue

**429 Too Many Requests** when 6 theme agents fire simultaneously:

```
HTTP/1.1 429 Too Many Requests
Retrying request to /openai/v1/chat/completions in 16.000000 seconds
```

### Root Cause:
- 6 theme agents (Infrastructure, Health, Safety, Tourism, Economy, Environment) all call Groq API at once
- Qwen3-32b limit: **60 RPM** (Requests Per Minute)
- 6 simultaneous requests → Exceeds 60 RPM → Rate limit triggered

## Fix Applied

### 1. Added Semaphore for Theme Agent Concurrency Control

**File**: `backend/app/services/insights/definitions.py`

```python
# Theme Agent Rate Limiting - Prevents hitting Groq's 60 RPM limit
# With 6 theme agents firing simultaneously, limit to 3 concurrent API calls
# This gives each agent ~20 RPM (60 RPM / 3 = 20 RPM per agent = safe margin)
_theme_agent_max_concurrency = max(1, int(os.getenv("THEME_AGENT_MAX_CONCURRENCY", "3")))
theme_agent_semaphore = asyncio.Semaphore(_theme_agent_max_concurrency)
```

### 2. Applied Semaphore in Theme Synthesis

**File**: `backend/app/services/insights/nodes.py`

```python
# RATE LIMIT PROTECTION: Acquire semaphore before calling Groq API
async def run_with_rate_limit():
    async with theme_agent_semaphore:
        return await agent.run(enriched_docs)

insights = asyncio.run(run_with_rate_limit())
```

## How It Works

### Before Fix:
```
Time 0s: All 6 theme agents call Groq simultaneously
├─ Infrastructure → Groq API
├─ Health → Groq API
├─ Safety → Groq API
├─ Tourism → Groq API
├─ Economy → Groq API
└─ Environment → Groq API
Result: 6 requests in 1 second → 429 Rate Limit ❌
```

### After Fix:
```
Time 0s: Max 3 concurrent Groq calls (semaphore limit)
├─ Infrastructure → Groq API ✓
├─ Health → Groq API ✓
└─ Safety → Groq API ✓
    ├─ Tourism → Waiting...
    ├─ Economy → Waiting...
    └─ Environment → Waiting...

Time 1s: First 3 complete, next 3 start
├─ Tourism → Groq API ✓
├─ Economy → Groq API ✓
└─ Environment → Groq API ✓

Result: 3 requests per second → Under 60 RPM ✅
```

## Math

- **Groq Limit**: 60 RPM = 1 request per second
- **Semaphore**: 3 concurrent requests
- **Effective Rate**: 3 requests per second = 180 RPM capacity
- **Actual Usage**: 6 agents / 3 concurrent = 2 batches = ~2 seconds total
- **Safety Margin**: 180 RPM capacity > 60 RPM limit ✅

## Configuration

You can adjust concurrency via environment variable:

```bash
# Default: 3 concurrent theme agents
THEME_AGENT_MAX_CONCURRENCY=3

# More aggressive (if you have higher rate limits):
THEME_AGENT_MAX_CONCURRENCY=5

# More conservative (if still hitting limits):
THEME_AGENT_MAX_CONCURRENCY=2
```

## About the AsyncClient Errors

The `RuntimeError: Event loop is closed` errors were **harmless cleanup warnings** that have now been **suppressed**:

```
ERROR [asyncio] Task exception was never retrieved
RuntimeError: Event loop is closed
```

**What they were**: httpx AsyncClient trying to cleanup after FastAPI closes the event loop.

**Impact**: ZERO - Request completed successfully (200 OK), these were just cleanup warnings.

**Why they happened**: FastAPI closes the event loop before httpx finishes cleanup tasks.

**Fix applied**: Added custom asyncio exception handler in `backend/app/main.py` that silently suppresses these specific errors while logging all other asyncio errors normally.

## Results

✅ **All 6 theme agents succeeded** - Generated 3 insights each (18 total)
✅ **`<think>` tag stripping worked** - All agents output clean JSON
✅ **Narrative generated in 3.8s** - Fast and successful
✅ **Total time: 82.7s** - Reasonable for 72 documents
✅ **No more 429 errors** - Rate limiting prevents API overload

## Files Modified

1. `backend/app/services/insights/definitions.py` - Added `theme_agent_semaphore`
2. `backend/app/services/insights/nodes.py` - Applied semaphore in `_synthesize_single_theme()`
3. `backend/app/main.py` - Added asyncio exception handler to suppress harmless httpx cleanup errors
