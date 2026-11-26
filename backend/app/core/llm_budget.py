"""Shared LLM output budget.

Groq's free tier allows 8,000 tokens per minute per organisation, and that
ceiling is shared by every model on the tier. A single request asking for 8,000
output tokens can therefore never fit, and the 429 that follows surfaces as an
empty summary rather than an error.

These constants are the one place that budget is decided. Call sites import
them instead of repeating a literal, so the three pipeline stages cannot drift
apart again.
"""

from __future__ import annotations

# The per-minute token ceiling on the free tier. Kept here so the reasoning
# below is checkable against the number rather than a comment.
LLM_FREE_TIER_TPM: int = 8000

# Output tokens requested per call. Half the per-minute ceiling, so two calls
# can overlap without tripping the limit.
LLM_MAX_OUTPUT_TOKENS: int = 4000