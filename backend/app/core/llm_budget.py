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

# Output tokens for a theme synthesis call. Six of these run concurrently, so
# each one stays at half the per-minute ceiling.
LLM_MAX_OUTPUT_TOKENS: int = 4000

# Output tokens for the narrative call. It runs after the theme calls finish,
# so it may claim more of the window. Six paragraphs with inline citations do
# not fit in 4000 once reasoning tokens are counted.
LLM_NARRATIVE_MAX_OUTPUT_TOKENS: int = 6000

# Output tokens for claim extraction. It runs in node 7, after the six theme
# calls have finished, so it can claim more of the minute. 4000 truncated a
# reasoning model's JSON array mid-string.
LLM_CLAIM_MAX_OUTPUT_TOKENS: int = 6000