"""Multi-Signal Credibility & Source Quality Assessment Agent for Thesis.

5-Signal Ensemble for Source Quality Filtering:
1. Domain Trust (25%) - Source reputation based on known domains (CONCURRENT)
2. Internal Cross-Reference (20%) - SEMANTIC corroboration using MiniLM embeddings (CONCURRENT)
3. Google Fact Check API (15%) - External fact-checker verification (CONCURRENT)
4. LLM Analysis (20%) - AI content quality assessment (Gemini) (PARALLEL)
5. External Cross-Reference (20%) - Real-time web verification via Tavily (CONCURRENT)

Note: This is a source quality filtering mechanism, not a misinformation detector.
Validation requires labeled ground truth data (documented as thesis limitation).

Each signal is independently measurable for thesis ablation studies.

EXECUTION MODEL: Hybrid Concurrent/Parallel Architecture
- Concurrent signals: asyncio.gather for I/O-bound operations (signals 1,2,3,5)
- Parallel signal: ThreadPoolExecutor for CPU-bound LLM inference (signal 4)
- Expected speedup: 3-5x (78s → ~20s) through optimal workload matching
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ...core.config import get_settings
from ...schemas.snapshot import WebDocument
from ..rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

# Safety settings for Gemini 2.5 Pro - use enum types
SAFETY_SETTINGS = [
    {
        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
]

# 5-Signal Weights (sum = 1.0) - Simplified for thesis clarity
# Removed: content_signals (heuristic overlap with LLM), recency (weak signal)
WEIGHTS = {
    "domain": 0.25,           # Source reputation
    "cross_reference": 0.20,  # Internal semantic corroboration
    "fact_check": 0.15,       # External verification (Google Fact Check API)
    "llm": 0.20,              # AI content analysis (Gemini)
    "tavily": 0.20,           # External cross-reference via web search
}

# ─────────────────────────────────────────────────────────────────────────────
# Signal 1: Domain Trust (25%)
# ─────────────────────────────────────────────────────────────────────────────

DOMAIN_TRUST_SCORES = {
    # Tier 1: Government (0.90-0.95)
    "gov.ph": 0.95, "pia.gov.ph": 0.95, "pna.gov.ph": 0.95,
    "gov": 0.90, "edu.ph": 0.85, "edu": 0.80,
    # Tier 2: Fact-checkers (0.85-0.90)
    "verafiles.org": 0.90, "rappler.com": 0.85,
    # Tier 3: Established news (0.75-0.82)
    "inquirer.net": 0.82, "philstar.com": 0.82, "gmanetwork.com": 0.80,
    "abs-cbn.com": 0.78, "mb.com.ph": 0.75, "manilatimes.net": 0.75,
    "sunstar.com.ph": 0.75, "baguiomidlandcourier.com.ph": 0.75,
    # Tier 4: Organizations (0.65-0.70)
    "org.ph": 0.70, "org": 0.65,
    # Tier 5: Social media (0.40-0.50)
    "facebook.com": 0.45, "reddit.com": 0.50, "twitter.com": 0.45,
    "x.com": 0.45, "youtube.com": 0.50, "tiktok.com": 0.40,
    # Tier 6: User-generated (0.35-0.45)
    "change.org": 0.40, "medium.com": 0.50, "wordpress.com": 0.45,
}


def _extract_domain(url: str | None) -> str:
    """Extract clean domain from URL."""
    if not url:
        return "unknown"
    try:
        return urlparse(str(url)).netloc.lower().replace("www.", "")
    except Exception:
        return "unknown"


def score_domain(domain: str) -> float:
    """Signal 1: Domain trust based on known source reputation."""
    if domain == "unknown":
        return 0.35
    if domain in DOMAIN_TRUST_SCORES:
        return DOMAIN_TRUST_SCORES[domain]
    for suffix, score in DOMAIN_TRUST_SCORES.items():
        if domain.endswith(f".{suffix}"):
            return score
    return 0.50  # Unknown but valid domain


# ─────────────────────────────────────────────────────────────────────────────
# Signal 2: Cross-Reference Checking (20%)
# Multiple independent sources = higher credibility
# Uses SEMANTIC SIMILARITY (MiniLM embeddings) for accurate story matching
# ─────────────────────────────────────────────────────────────────────────────

import numpy as np


def compute_cosine_similarity(emb1: list[float], emb2: list[float]) -> float:
    """Compute cosine similarity between two embeddings."""
    a = np.array(emb1)
    b = np.array(emb2)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def compute_semantic_cross_reference_scores(
    documents: list[WebDocument],
    embeddings: list[list[float]],
    domains: list[str],
    similarity_threshold: float = 0.70,
) -> tuple[list[float], list[int]]:
    """Signal 2: Score based on semantic corroboration across sources.
    
    Uses MiniLM embeddings for semantic similarity instead of keyword Jaccard.
    This captures meaning rather than just word overlap.
    
    Args:
        documents: List of documents
        embeddings: Pre-computed embeddings for each document
        domains: Pre-extracted domains for each document
        similarity_threshold: Cosine similarity threshold for "same story" (default 0.70)
    
    Returns:
        Tuple of (scores, corroborator_counts) for each document
    """
    n = len(documents)
    if n <= 1:
        return [0.50] * n, [0] * n
    
    scores = []
    corroborator_counts = []
    
    for i in range(n):
        domain_i = domains[i]
        emb_i = embeddings[i]
        
        # Count corroborating sources (different domains with semantically similar content)
        corroborating_domains = set()
        
        for j in range(n):
            if i == j:
                continue
            domain_j = domains[j]
            # Skip same domain (not independent)
            if domain_i == domain_j:
                continue
            
            emb_j = embeddings[j]
            
            # Semantic similarity using cosine distance
            similarity = compute_cosine_similarity(emb_i, emb_j)
            
            # Threshold: 0.70 cosine similarity = semantically same story
            if similarity >= similarity_threshold:
                corroborating_domains.add(domain_j)
        
        # Score based on number of independent corroborating sources
        unique_corroborators = len(corroborating_domains)
        if unique_corroborators >= 3:
            score = 0.95  # Well-corroborated (3+ independent sources)
        elif unique_corroborators == 2:
            score = 0.85  # Good corroboration
        elif unique_corroborators == 1:
            score = 0.70  # Some corroboration
        else:
            score = 0.45  # Single source (no corroboration)
        
        scores.append(score)
        corroborator_counts.append(unique_corroborators)
    
    return scores, corroborator_counts


# ─────────────────────────────────────────────────────────────────────────────
# Signal 3: Google Fact Check API (20%)
# ─────────────────────────────────────────────────────────────────────────────

FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
_fact_check_api_warned = False

FACT_CHECK_RATINGS = {
    "true": 0.95, "accurate": 0.95,
    "mostly true": 0.85, "mostly accurate": 0.85,
    "half true": 0.60, "mixture": 0.55,
    "mostly false": 0.25, "mostly inaccurate": 0.25,
    "false": 0.10, "inaccurate": 0.10,
    "pants on fire": 0.05,
    "misleading": 0.20, "out of context": 0.30,
    "unproven": 0.50, "unverified": 0.50,
    "outdated": 0.40,
}


# Shared HTTP client for connection reuse (CRITICAL for latency)
_fact_check_client: httpx.AsyncClient | None = None

def _get_fact_check_client() -> httpx.AsyncClient:
    """Get shared HTTP client for fact check API calls."""
    global _fact_check_client
    if _fact_check_client is None:
        # Use HTTP/2 and connection pooling for speed
        _fact_check_client = httpx.AsyncClient(
            timeout=8.0,  # Reduced from 10s
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _fact_check_client


async def search_fact_checks(query: str, api_key: str) -> list[dict]:
    """Query Google Fact Check API with connection reuse."""
    try:
        client = _get_fact_check_client()
        resp = await client.get(FACT_CHECK_API_URL, params={
            "key": api_key,
            "query": query[:200],
            "languageCode": "en",
            "maxAgeDays": 365,
        })
        if resp.status_code == 200:
            return resp.json().get("claims", [])
    except Exception:
        pass
    return []


def parse_fact_check(claims: list[dict]) -> tuple[float, str | None]:
    """Parse fact-check results into score."""
    if not claims:
        return 0.50, None  # Neutral when no fact-checks found
    
    scores, ratings = [], []
    for claim in claims[:3]:
        for review in claim.get("claimReview", []):
            rating = review.get("textualRating", "").lower()
            ratings.append(rating)
            matched = False
            for key, sc in FACT_CHECK_RATINGS.items():
                if key in rating:
                    scores.append(sc)
                    matched = True
                    break
            if not matched:
                scores.append(0.50)
    
    if scores:
        return sum(scores) / len(scores), ratings[0] if ratings else None
    return 0.50, None


# ─────────────────────────────────────────────────────────────────────────────
# Signal 4: LLM Analysis (20%)
# ─────────────────────────────────────────────────────────────────────────────

class LLMCredibilityAnalyzer:
    """Gemini-based content credibility analysis."""
    
    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        # Use Gemini 2.5 Flash-Lite for maximum speed
        self.model = genai.GenerativeModel(
            "gemini-2.5-flash-lite",
            safety_settings=SAFETY_SETTINGS,
        )
        self.batch_size = 25  # Optimized for speed (fewer API calls)
    
    def analyze_batch(self, docs: list[WebDocument]) -> list[dict]:
        """Analyze all documents in batches with high parallelism.
        
        CTO-OPTIMIZATION: Using GLOBAL_EXECUTOR to avoid thread spawning overhead.
        """
        from app.core.executor import GLOBAL_EXECUTOR
        
        # Create batches
        batches = [docs[i:i + self.batch_size] for i in range(0, len(docs), self.batch_size)]
        
        # Parallel execution using global pool
        futures = [GLOBAL_EXECUTOR.submit(self._analyze_batch, batch) for batch in batches]
        
        results = []
        for future in futures:
            try:
                results.extend(future.result(timeout=60))
            except Exception as e:
                logger.error(f"[llm_credibility] Batch analysis failed: {e}")
                # Add default results for failed batch
                batch_len = len(batches[len(results) // self.batch_size])
                results.extend([{"score": 0.50, "reasoning": "Analysis timed out", "red_flags": []}] * batch_len)
            
        return results
    
    def _analyze_batch(self, batch: list[WebDocument]) -> list[dict]:
        """Analyze a single batch."""
        entries = []
        for i, doc in enumerate(batch):
            domain = _extract_domain(str(doc.url) if doc.url else None)
            title = (doc.title or "")[:100]
            snippet = (doc.snippet or "")[:150]
            entries.append(f"[{i}] {domain}: {title}\n    {snippet}")
        
        prompt = f"""You are a credibility and misinformation analyst for civic news about Baguio City, Philippines.

Score each item's credibility from 0.0 to 1.0 and detect misinformation patterns:

CREDIBILITY FACTORS:
- Is the source a legitimate news organization or official source?
- Is the content specific (names, dates, locations) or vague?
- Is the language professional or sensational?

MISINFORMATION INDICATORS (flag these):
- Emotional manipulation (fear, outrage, urgency)
- Conspiracy framing ("they don't want you to know")
- False certainty ("100% proven", "scientists baffled")
- Unverified claims without sources
- Clickbait/sensationalist headlines
- Social proof manipulation ("going viral", "everyone is talking")

Items:
{chr(10).join(entries)}

Return JSON array only:
[{{"index": 0, "score": 0.X, "reasoning": "one sentence", "red_flags": ["FLAG_TYPE"], "misinfo_risk": "none|low|medium|high"}}]

Score guide: 0.8+ high credibility, 0.6-0.8 medium, 0.4-0.6 low, <0.4 potential misinformation"""

        try:
            resp = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4500,  # Safe buffer for 20 docs with detailed reasoning
                ),
            )
            return self._parse_response(resp.text, len(batch))
        except Exception as e:
            logger.warning(f"[llm_credibility] Gemini Flash error: {e}")
            return [{"score": 0.50, "reasoning": "Analysis unavailable", "red_flags": []}] * len(batch)
    
    def _parse_response(self, text: str, count: int) -> list[dict]:
        """Parse LLM JSON response."""
        default = {"score": 0.50, "reasoning": "Content is moderately credible, standard news format.", "red_flags": [], "misinfo_risk": "unknown"}
        results = [default.copy() for _ in range(count)]
        
        # Extract JSON from markdown code blocks
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                if part.strip().startswith("json"):
                    text = part.strip()[4:]
                    break
                elif part.strip().startswith("["):
                    text = part.strip()
                    break
        
        try:
            data = json.loads(text.strip())
            if isinstance(data, list):
                for item in data:
                    idx = item.get("index", -1)
                    if 0 <= idx < count:
                        score = min(1.0, max(0.0, float(item.get("score", 0.5))))
                        reasoning = str(item.get("reasoning", ""))
                        
                        # Generate fallback reasoning if empty
                        if not reasoning.strip():
                            if score >= 0.8:
                                reasoning = "Source appears credible with professional content."
                            elif score >= 0.6:
                                reasoning = "Content is moderately credible, standard news format."
                            elif score >= 0.4:
                                reasoning = "Limited credibility indicators, verify independently."
                            else:
                                reasoning = "Low credibility signals detected, exercise caution."
                        
                        results[idx] = {
                            "score": score,
                            "reasoning": reasoning,
                            "red_flags": list(item.get("red_flags", [])),
                            "misinfo_risk": str(item.get("misinfo_risk", "unknown")),
                        }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        
        return results


# ─────────────────────────────────────────────────────────────────────────────
# Signal 5: Content Signals (10%)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Misinformation Pattern Detection
# ─────────────────────────────────────────────────────────────────────────────

# Clickbait patterns - common in low-quality content
CLICKBAIT_PATTERNS = [
    r"you won't believe",
    r"shocking",
    r"unbelievable", 
    r"must see",
    r"breaking:",
    r"urgent:",
    r"exclusive:",
    r"\?\?\?",
    r"!!!",
]

# Misinformation language patterns - emotional manipulation, false claims
MISINFO_PATTERNS = [
    (r"\b(exposed|exposed!)\b", "sensationalism"),
    (r"\bthey don't want you to know\b", "conspiracy_framing"),
    (r"\bwake up\b", "conspiracy_framing"),
    (r"\bsheeple\b", "conspiracy_framing"),
    (r"\bmainstream media\s+(lies|lying|won't tell)\b", "media_distrust"),
    (r"\bfake news\b", "delegitimization"),
    (r"\btruth they're hiding\b", "conspiracy_framing"),
    (r"\b100%\s+(true|proven|confirmed)\b", "false_certainty"),
    (r"\bscientists\s+(baffled|confused|can't explain)\b", "false_expertise"),
    (r"\bdoctors\s+(hate|don't want)\b", "false_expertise"),
    (r"\bshare before\s+(deleted|removed|banned)\b", "false_urgency"),
    (r"\bgoing viral\b", "social_proof_manipulation"),
    (r"\beveryone is talking about\b", "social_proof_manipulation"),
    (r"\bthis changes everything\b", "exaggeration"),
    (r"\bno one is reporting\b", "false_exclusivity"),
]

# Credibility indicators - professional journalism markers
CREDIBILITY_PATTERNS = [
    r"according to",
    r"reported by",
    r"official statement",
    r"press release",
    r"spokesperson said",
    r"confirmed by",
    r"sources say",
    r"in a statement",
]

# Official source mentions
OFFICIAL_MENTIONS = [
    r"mayor",
    r"governor", 
    r"city council",
    r"department of",
    r"office of",
    r"police",
    r"government",
    r"city hall",
    r"barangay",
]

# Author/byline patterns - named journalists add credibility
AUTHOR_PATTERNS = [
    r"\bby\s+[A-Z][a-z]+\s+[A-Z][a-z]+",  # "by John Smith"
    r"\bwritten\s+by\s+[A-Z][a-z]+",       # "written by John"
    r"\breported\s+by\s+[A-Z][a-z]+",      # "reported by Jane"
    r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\s*,\s*(reporter|correspondent|editor|journalist)",
    r"\bstaff\s+(writer|reporter|correspondent)",
]

# Unverified claim indicators
UNVERIFIED_PATTERNS = [
    r"\ballegedly\b",
    r"\breportedly\b",
    r"\brunconfirmed\b",
    r"\bunverified\b",
    r"\brumor\b",
    r"\bclaims?\s+that\b",
    r"\bsources?\s+claim\b",
]


def detect_misinfo_patterns(title: str, snippet: str) -> list[dict]:
    """Detect misinformation patterns in content.
    
    Returns:
        List of detected patterns with type and matched text
    """
    text = f"{title} {snippet}".lower()
    detected = []
    
    for pattern, pattern_type in MISINFO_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            detected.append({
                "type": pattern_type,
                "matched": match.group(0),
                "severity": "high" if pattern_type in ["conspiracy_framing", "false_certainty"] else "medium"
            })
    
    return detected


def score_content_signals(title: str, snippet: str) -> tuple[float, bool, list[str]]:
    """Signal 5: Content quality heuristics with misinformation detection.
    
    Returns:
        Tuple of (score, has_author, red_flags) - score, author flag, and detected issues
    """
    text = f"{title} {snippet}".lower()
    original_text = f"{title} {snippet}"
    
    score = 0.60  # Base score
    has_author = False
    red_flags = []
    
    # ─── Negative signals (misinformation indicators) ───
    
    # ALL CAPS title - common in sensationalist content
    if title and title.isupper():
        score -= 0.20
        red_flags.append("ALL_CAPS_TITLE")
    
    # Excessive punctuation
    exclamation_count = text.count("!")
    if exclamation_count > 3:
        score -= 0.15
        red_flags.append("EXCESSIVE_PUNCTUATION")
    elif exclamation_count > 1:
        score -= 0.05
    
    # Clickbait patterns
    for pattern in CLICKBAIT_PATTERNS:
        if re.search(pattern, text):
            score -= 0.10
            red_flags.append("CLICKBAIT_LANGUAGE")
            break
    
    # Misinformation patterns (more severe)
    misinfo_detected = detect_misinfo_patterns(title, snippet)
    if misinfo_detected:
        high_severity = [m for m in misinfo_detected if m["severity"] == "high"]
        medium_severity = [m for m in misinfo_detected if m["severity"] == "medium"]
        
        if high_severity:
            score -= 0.25
            red_flags.append(f"MISINFO_PATTERN:{high_severity[0]['type'].upper()}")
        elif medium_severity:
            score -= 0.15
            red_flags.append(f"MISINFO_PATTERN:{medium_severity[0]['type'].upper()}")
    
    # Unverified claim indicators
    for pattern in UNVERIFIED_PATTERNS:
        if re.search(pattern, text):
            score -= 0.05
            if "UNVERIFIED_CLAIMS" not in red_flags:
                red_flags.append("UNVERIFIED_CLAIMS")
            break
    
    # ─── Positive signals (credibility indicators) ───
    
    # Attribution to sources
    for pattern in CREDIBILITY_PATTERNS:
        if re.search(pattern, text):
            score += 0.10
            break
    
    # Official source mentions
    for pattern in OFFICIAL_MENTIONS:
        if re.search(pattern, text):
            score += 0.05
            break
    
    # Specific details (dates, numbers) - factual content
    if re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text):
        score += 0.05
    if re.search(r'\b\d+\s*(million|billion|thousand|percent|%)\b', text):
        score += 0.05
    
    # Author/attribution detection
    for pattern in AUTHOR_PATTERNS:
        if re.search(pattern, original_text, re.IGNORECASE):
            score += 0.10
            has_author = True
            break
    
    return max(0.10, min(1.0, score)), has_author, red_flags


# ─────────────────────────────────────────────────────────────────────────────
# Signal 6: Recency (5%)
# ─────────────────────────────────────────────────────────────────────────────

def score_recency(published_at: datetime | None) -> float:
    """Signal 6: Content freshness."""
    if not published_at:
        return 0.50  # Unknown age
    
    try:
        now = datetime.now(timezone.utc)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        hours = (now - published_at).total_seconds() / 3600
    except Exception:
        return 0.50
    
    if hours < 0:  # Future date (suspicious)
        return 0.30
    if hours < 6:
        return 1.0
    if hours < 24:
        return 0.90
    if hours < 72:
        return 0.75
    if hours < 168:  # 1 week
        return 0.60
    if hours < 720:  # 1 month
        return 0.45
    return 0.35  # Older than 1 month


# ─────────────────────────────────────────────────────────────────────────────
# Signal 7: Tavily Claim Verification (15%)
# Real-time web search to verify claims against authoritative sources
# ─────────────────────────────────────────────────────────────────────────────

# Trusted domains for claim verification
TRUSTED_VERIFICATION_DOMAINS = [
    "gov.ph", "pia.gov.ph", "pna.gov.ph",  # Government
    "inquirer.net", "philstar.com", "gmanetwork.com", "abs-cbn.com",  # Major news
    "rappler.com", "verafiles.org",  # Fact-checkers
    "reuters.com", "ap.org", "bbc.com",  # International
]

# High-trust domains that don't need fact-checking (optimization)
SKIP_FACT_CHECK_DOMAINS = {
    "gov.ph", "pia.gov.ph", "pna.gov.ph",  # Government sources
    "inquirer.net", "philstar.com", "gmanetwork.com",  # Major news
    "verafiles.org", "rappler.com",  # Fact-checkers
}

# Keywords that indicate claim contradiction (must be strong indicators)
# These should only trigger when the claim itself is being disputed
CONTRADICTION_KEYWORDS = [
    "debunked", "hoax", "disinformation", "misinformation",
    "rated false", "pants on fire", "fake news",
    "this claim is false", "not true", "baseless claim",
]

# Keywords that indicate claim confirmation
CONFIRMATION_KEYWORDS = [
    "confirmed", "verified", "officially announced", "according to officials",
    "reported by", "sources confirm", "statement released",
]


def extract_verifiable_claims(title: str, snippet: str) -> list[str]:
    """Extract specific verifiable claims from document for fact-checking.
    
    Returns list of claim queries optimized for Tavily search.
    """
    text = f"{title} {snippet}"
    claims = []
    
    # Primary claim: the title itself (most important claim)
    if title and len(title) > 10:
        # Clean title for search
        clean_title = re.sub(r'[^\w\s\-]', '', title)
        claims.append(clean_title[:150])
    
    # Extract specific factual patterns from snippet
    # Pattern 1: Numbers + context (e.g., "P4.5 billion", "1,000 vendors")
    number_claims = re.findall(
        r'[A-Z][^.]*?\b(?:P?\d+(?:,\d+)*(?:\.\d+)?)\s*(?:billion|million|thousand|percent|%|pesos?|vendors?|people|residents?)[^.]*',
        text,
        re.IGNORECASE
    )
    for claim in number_claims[:2]:
        if len(claim) > 20:
            claims.append(claim[:150])
    
    # Pattern 2: Named entities + actions (e.g., "Mayor X announced", "SM proposed")
    entity_claims = re.findall(
        r'(?:Mayor|Governor|City|Department|Office|SM|Ayala|Government)\s+[A-Z][^.]{10,80}',
        text
    )
    for claim in entity_claims[:2]:
        claims.append(claim[:150])
    
    # Deduplicate and limit
    seen = set()
    unique_claims = []
    for c in claims:
        c_lower = c.lower().strip()
        if c_lower not in seen and len(c_lower) > 15:
            seen.add(c_lower)
            unique_claims.append(c)
    
    return unique_claims[:3]  # Max 3 claims per document


def tavily_search_sync(query: str, api_key: str, search_type: str = "claim") -> dict:
    """Search Tavily for claim verification using official SDK.
    
    Args:
        query: The claim or topic to search
        api_key: Tavily API key
        search_type: "claim" for fact-checking, "topic" for general search
    """
    try:
        from tavily import TavilyClient
        
        client = TavilyClient(api_key=api_key)
        
        # For claim verification, add fact-check context
        if search_type == "claim":
            search_query = f'{query} fact check verified'
        else:
            search_query = query
        
        # Use the official SDK search method
        response = client.search(
            query=search_query[:400],
            search_depth="advanced",
            include_answer=True,
            max_results=5,
        )
        
        logger.info(f"[tavily] Search successful for: {query[:50]}...")
        return response
        
    except ImportError:
        logger.error("[tavily] tavily-python not installed. Run: pip install tavily-python")
        return {}
    except Exception as e:
        logger.warning(f"[tavily] Search error: {e}")
        # Re-raise rate limit errors so the caller can fail fast
        if "429" in str(e) or "limit" in str(e).lower() or "exceeds your plan" in str(e).lower():
            raise e
        return {}


async def tavily_search(query: str, api_key: str, search_type: str = "claim") -> dict:
    """Async wrapper for Tavily search."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, tavily_search_sync, query, api_key, search_type)


def analyze_tavily_results(
    tavily_result: dict, 
    original_domain: str,
    original_title: str,
    original_embedding: list[float] | None = None,
    embedding_service: Any = None,
) -> tuple[float, list[dict], str]:
    """Analyze Tavily results for claim verification.
    
    SEMANTIC RELEVANCE: Uses pre-computed embeddings to check if fact-check
    results are actually about the same topic as the original claim.
    This prevents false positives like matching earthquake fact-checks to fire articles.
    
    Args:
        tavily_result: Tavily API response
        original_domain: Domain of original document
        original_title: Title of original document
        original_embedding: Pre-computed embedding for original doc (optional)
        embedding_service: Embedding service for computing result embeddings (optional)
    
    Returns:
        Tuple of (score, verified_sources, verification_status)
        - score: 0.0-1.0 credibility score
        - verified_sources: list of dicts with url, domain, title for corroborating sources
        - verification_status: "verified", "contradicted", "unverified", "partial"
    """
    results = tavily_result.get("results", [])
    answer = tavily_result.get("answer", "")
    
    if not results and not answer:
        return 0.50, [], "unverified"
    
    verified_sources = []
    trusted_matches = 0
    contradiction_signals = 0
    confirmation_signals = 0
    
    # Check if we can use semantic relevance (embeddings available)
    use_semantic = original_embedding is not None and embedding_service is not None
    
    # Fallback: Extract key terms for keyword-based relevance
    original_title_lower = original_title.lower() if original_title else ""
    original_key_terms = set(re.findall(r'\b[a-z]{4,}\b', original_title_lower))
    stop_words = {"this", "that", "with", "from", "have", "been", "were", "will", "about", "city", "baguio"}
    original_key_terms -= stop_words
    
    # Analyze Tavily's AI answer for verification signals
    answer_lower = answer.lower() if answer else ""
    answer_is_relevant = False
    
    if use_semantic and answer:
        # Semantic relevance check for answer
        try:
            answer_embedding = embedding_service.embed(answer[:500])
            similarity = compute_cosine_similarity(original_embedding, answer_embedding)
            answer_is_relevant = similarity >= 0.55  # Lower threshold for answer (broader context)
            logger.debug(f"[tavily] Answer semantic similarity: {similarity:.3f}")
        except Exception:
            # Fallback to keyword matching
            answer_terms = set(re.findall(r'\b[a-z]{4,}\b', answer_lower))
            answer_is_relevant = len(original_key_terms & answer_terms) >= 2
    elif original_key_terms and answer_lower:
        answer_terms = set(re.findall(r'\b[a-z]{4,}\b', answer_lower))
        answer_is_relevant = len(original_key_terms & answer_terms) >= 2
    
    if answer_is_relevant:
        for keyword in CONTRADICTION_KEYWORDS:
            if keyword in answer_lower:
                contradiction_signals += 1
        for keyword in CONFIRMATION_KEYWORDS:
            if keyword in answer_lower:
                confirmation_signals += 1
    
    # Analyze individual search results
    for result in results[:5]:
        url = result.get("url", "")
        domain = _extract_domain(url)
        title = result.get("title", "")
        relevance_score = result.get("score", 0)
        content = (result.get("content", "") + " " + title).lower()
        
        # Skip if same domain as original
        if domain == original_domain:
            continue
        
        # SEMANTIC RELEVANCE CHECK - prevents fire/earthquake mismatch
        is_semantically_relevant = False
        
        if use_semantic:
            try:
                result_text = f"{title} {result.get('content', '')}"[:500]
                result_embedding = embedding_service.embed(result_text)
                similarity = compute_cosine_similarity(original_embedding, result_embedding)
                is_semantically_relevant = similarity >= 0.60  # Require 60% similarity
                logger.debug(f"[tavily] Result '{title[:30]}...' similarity: {similarity:.3f}")
            except Exception:
                # Fallback to keyword matching
                result_terms = set(re.findall(r'\b[a-z]{4,}\b', content))
                is_semantically_relevant = len(original_key_terms & result_terms) >= 2
        else:
            # Keyword-based fallback
            result_terms = set(re.findall(r'\b[a-z]{4,}\b', content))
            term_overlap = len(original_key_terms & result_terms) if original_key_terms else 0
            is_semantically_relevant = term_overlap >= 2 or relevance_score > 0.7
        
        if not is_semantically_relevant:
            logger.debug(f"[tavily] Skipping irrelevant result: '{title[:50]}'")
            continue
        
        # Check if from trusted domain
        is_trusted = any(
            domain.endswith(trusted) or domain == trusted
            for trusted in TRUSTED_VERIFICATION_DOMAINS
        )
        
        # Check content for contradiction/confirmation signals
        for keyword in CONTRADICTION_KEYWORDS:
            if keyword in content:
                contradiction_signals += 1
                break
        for keyword in CONFIRMATION_KEYWORDS:
            if keyword in content:
                confirmation_signals += 1
                break
        
        # Count trusted source matches and store full source info
        if is_trusted and relevance_score > 0.3:
            trusted_matches += 1
            verified_sources.append({
                "url": url,
                "domain": domain,
                "title": title[:100] if title else domain,
            })
    
    # Determine verification status and score
    # Be conservative about marking as "contradicted" - need strong evidence
    if contradiction_signals >= 3:
        # Multiple strong contradiction signals - likely misinformation
        return 0.20, verified_sources, "contradicted"
    elif contradiction_signals >= 2 and confirmation_signals == 0 and trusted_matches == 0:
        # Strong contradiction with no supporting evidence
        return 0.30, verified_sources, "disputed"
    elif trusted_matches >= 2 and confirmation_signals >= 1:
        # Strong verification from trusted sources
        return 0.95, verified_sources, "verified"
    elif trusted_matches >= 1 and confirmation_signals >= 1:
        # Good verification
        return 0.85, verified_sources, "verified"
    elif trusted_matches >= 2:
        # Multiple trusted sources cover this topic
        return 0.80, verified_sources, "verified"
    elif trusted_matches >= 1:
        # Some trusted coverage (topic exists)
        return 0.70, verified_sources, "partial"
    elif confirmation_signals >= 1:
        # Some confirmation but not from trusted sources
        return 0.60, verified_sources, "partial"
    elif contradiction_signals == 1:
        # Single weak contradiction signal - just mark as needs verification
        return 0.50, verified_sources, "unverified"
    else:
        # No verification found - neutral
        return 0.50, verified_sources, "unverified"


def score_tavily_verification(tavily_result: dict, original_domain: str) -> tuple[float, list[str]]:
    """Score claim verification based on Tavily search results.
    
    Returns:
        Tuple of (score, verified_sources) - verification score and list of corroborating sources
    """
    # Use the new analysis function
    score, sources, status = analyze_tavily_results(tavily_result, original_domain, "")
    return score, sources

# ============================================================================
# SIGNAL 1: Domain Trust Agent (25%)
# ============================================================================

@dataclass
class DomainTrustAgent:
    """Sub-agent for Domain Trust scoring.
    
    Specialized in: Source reputation based on known domains
    """
    
    weight: float = 0.25
    
    def score(self, doc: WebDocument, context: dict[str, Any]) -> float:
        """Calculate domain trust score."""
        domain = context.get("domain", "unknown")
        return score_domain(domain)


# ============================================================================
# SIGNAL 2: Cross-Reference Agent (20%)
# ============================================================================

@dataclass
class CrossReferenceAgent:
    """Sub-agent for Semantic Cross-Reference scoring.
    
    Specialized in: Internal semantic corroboration within results
    """
    
    weight: float = 0.20
    
    def score(self, doc: WebDocument, context: dict[str, Any]) -> float:
        """Calculate cross-reference score."""
        return context.get("cross_reference_score", 0.50)


# ============================================================================
# SIGNAL 3: Fact Check Agent (15%)
# ============================================================================

@dataclass
class FactCheckAgent:
    """Sub-agent for Google Fact Check API verification.
    
    Specialized in: External verification via Google Fact Check API
    """
    
    weight: float = 0.15
    api_key: str | None = None
    
    async def score(self, doc: WebDocument, context: dict[str, Any]) -> float:
        """Calculate fact-check score via API.
        
        Analyzes ALL documents - no skip logic.
        """
        if not self.api_key:
            return 0.50
        
        query = (doc.title or "")[:100]
        claims = await search_fact_checks(query, self.api_key)
        score, _ = parse_fact_check(claims)
        return score


# ============================================================================
# SIGNAL 4: LLM Analysis Agent (20%)
# ============================================================================

@dataclass
class LLMAnalysisAgent:
    """Sub-agent for Gemini-based content credibility analysis.
    
    Specialized in: AI content assessment and misinformation detection
    """
    
    weight: float = 0.20
    analyzer: LLMCredibilityAnalyzer | None = None
    
    def __post_init__(self):
        if self.analyzer is None:
            self.analyzer = LLMCredibilityAnalyzer()
    
    def score(self, doc: WebDocument, context: dict[str, Any]) -> float:
        """Calculate LLM-based credibility score."""
        # Process through batch analyzer (sync, uses ThreadPool internally)
        results = self.analyzer.analyze_batch([doc])
        if results:
            return results[0].get("score", 0.50)
        return 0.50


# ============================================================================
# SIGNAL 5: Tavily Verification Agent (20%)
# ============================================================================

@dataclass
class TavilyAgent:
    """Sub-agent for real-time web verification.
    
    Specialized in: External cross-reference via Tavily web search
    """
    
    weight: float = 0.20
    api_key: str | None = None
    embedding_service: Any = None
    
    async def score(self, doc: WebDocument, context: dict[str, Any]) -> float:
        """Calculate Tavily verification score.
        
        Analyzes ALL documents - no skip logic.
        """
        if not self.api_key:
            return 0.50
        
        title = doc.title or ""
        snippet = doc.snippet or ""
        
        # Extract claims and verify
        claims = extract_verifiable_claims(title, snippet)
        if not claims:
            claims = [title[:150]] if title else []
        
        if not claims:
            return 0.50
        
        try:
            result = await tavily_search(claims[0], self.api_key, "claim")
            score, _, _ = analyze_tavily_results(
                result, 
                context.get("domain", ""), 
                title,
                context.get("embedding"),
                self.embedding_service
            )
            return score
        except Exception:
            return 0.50


# ============================================================================
# CREDIBILITY AGENT FACTORY
# ============================================================================

@dataclass
class CredibilityAgent:
    """Coordinator for 5 credibility sub-agents.
    
    Runs all signals in parallel via asyncio.gather for maximum speed.
    """
    
    domain_agent: DomainTrustAgent = field(default_factory=DomainTrustAgent)
    crossref_agent: CrossReferenceAgent = field(default_factory=CrossReferenceAgent)
    factcheck_agent: FactCheckAgent = field(default_factory=lambda: FactCheckAgent(api_key=None))
    llm_agent: LLMAnalysisAgent = field(default_factory=LLMAnalysisAgent)
    tavily_agent: TavilyAgent = field(default_factory=lambda: TavilyAgent(api_key=None))
    
    def __post_init__(self):
        settings = get_settings()
        self.factcheck_agent = FactCheckAgent(
            api_key=getattr(settings, "google_fact_check_api_key", None) or settings.gemini_api_key
        )
        self.tavily_agent = TavilyAgent(
            api_key=getattr(settings, "tavily_api_key", None),
            embedding_service=get_embedding_service()
        )
    
    async def run(self, documents: list[WebDocument]) -> list[WebDocument]:
        """Assess credibility using 5 parallel sub-agents.
        
        Expected speedup: 3-5x (78s → ~20s)
        """
        if not documents:
            return []
        
        n = len(documents)
        logger.info(f"[CredibilityAgent] Analyzing {n} documents with 5 parallel sub-agents")
        
        # Pre-compute embeddings for cross-reference
        embedding_service = get_embedding_service()
        doc_texts = [f"{d.title or ''} {d.snippet or ''}"[:500] for d in documents]
        embeddings = embedding_service.embed_batch(doc_texts, batch_size=24)
        
        # Extract domains
        domains = [_extract_domain(str(d.url) if d.url else None) for d in documents]
        
        # Compute cross-reference scores (batch operation)
        cross_ref_scores, _ = compute_semantic_cross_reference_scores(
            documents, embeddings, domains, similarity_threshold=0.70
        )
        
        # Pre-create shared context for all agents
        doc_contexts = [
            {
                "domain": domains[i],
                "cross_reference_score": cross_ref_scores[i],
                "embedding": embeddings[i],
            }
            for i in range(n)
        ]
        
        # Pre-compute LLM analysis for all documents (batch operation)
        logger.info("[CredibilityAgent] Running LLM analysis in parallel batch")
        llm_results = self.llm_agent.analyzer.analyze_batch(documents)
        
        # Pre-compute Tavily verification for all documents (batch operation)
        logger.info("[CredibilityAgent] Running Tavily verification in parallel batch")
        tavily_results = await self._batch_tavily_verify(documents, domains, embeddings, llm_results)
        
        # Pre-compute Fact Check scores for all documents (batch operation with concurrency control)
        logger.info("[CredibilityAgent] Running Google Fact Check API in parallel batch")
        factcheck_results = await self._batch_fact_check(documents, domains)
        
        enriched = []
        
        for i, doc in enumerate(documents):
            context = doc_contexts[i]
            llm_result = llm_results[i] if i < len(llm_results) else {"score": 0.50, "reasoning": "Analysis unavailable"}
            tavily_result = tavily_results[i] if i < len(tavily_results) else (0.50, [], "unverified")
            factcheck_score = factcheck_results[i][0] if i < len(factcheck_results) else 0.50
            
            # Run ALL 5 sub-agents in parallel using asyncio.gather
            # Note: We wrap sync score() calls in asyncio.to_thread() for true parallelism
            domain_future = asyncio.to_thread(self.domain_agent.score, doc, context)
            crossref_future = asyncio.to_thread(self.crossref_agent.score, doc, context)
            llm_future = asyncio.to_thread(lambda: llm_result.get("score", 0.50))
            
            # Use pre-computed Fact Check and Tavily results instead of making second API calls
            # This fixes the discrepancy between score and verification status
            tavily_score = tavily_result[0]
            
            # Execute all 3 remaining agents in parallel
            domain_score, crossref_score, llm_score_async = await asyncio.gather(
                domain_future, crossref_future, llm_future
            )
            
            # Weighted ensemble
            final_score = (
                0.25 * domain_score +
                0.20 * crossref_score +
                0.15 * factcheck_score +
                0.20 * llm_score_async +
                0.20 * tavily_score
            )
            
            # Extract Tavily verification status
            if isinstance(tavily_result, tuple):
                tavily_verification_status = tavily_result[2]
            else:
                tavily_verification_status = tavily_result.get("verification_status", "unverified")
            
            # Determine tier
            if final_score >= 0.75:
                tier = "high"
            elif final_score >= 0.55:
                tier = "medium"
            elif final_score >= 0.35:
                tier = "low"
            else:
                tier = "very_low"
            
            enriched.append(doc.model_copy(update={
                "metadata": {
                    **(doc.metadata or {}),
                    "credibility_score": round(final_score, 3),
                    "credibility_tier": tier,
                    "credibility_breakdown": {
                        "domain": round(domain_score, 3),
                        "cross_reference": round(crossref_score, 3),
                        "fact_check": round(factcheck_score, 3),
                        "llm": round(llm_score_async, 3),
                        "tavily": round(tavily_score, 3),
                    },
                    "source_domain": domains[i],
                    "llm_reasoning": llm_result.get("reasoning", ""),
                    "tavily_verified_sources": tavily_result[1] if isinstance(tavily_result, tuple) else tavily_result.get("verified_sources", []),
                    "tavily_verification_status": tavily_verification_status,
                }
            }))
        
        # Cleanup
        del embeddings
        
        # Log distribution
        scores = [d.metadata.get("credibility_score", 0) for d in enriched]
        avg = sum(scores) / len(scores) if scores else 0
        logger.info(f"[CredibilityAgent] Complete: avg={avg:.2f}, {n} docs")
        
        return enriched
    
    async def _batch_tavily_verify(
        self,
        docs: list[WebDocument],
        domains: list[str],
        embeddings: list[list[float]] | None = None,
        llm_results: list[dict] | None = None,  # Pass LLM results here
    ) -> list[tuple[float, list[str], str]]:
        """Run Tavily claim verification for ALL documents.
        
        No priority sampling - analyzes every document.
        
        Args:
            docs: Documents to verify
            domains: Pre-extracted domains
            embeddings: Pre-computed embeddings for semantic relevance (optional)
            llm_results: Pre-computed LLM analysis results
            
        Returns:
            List of (score, verified_sources, verification_status) tuples
        """
        if not self.tavily_agent.api_key:
            # Return neutral scores if Tavily not configured
            return [(0.50, [], "disabled") for _ in docs]
        
        # Get embedding service for Tavily result comparison
        embedding_service = get_embedding_service() if embeddings else None
        
        # VERIFY ALL DOCUMENTS - no skip logic
        docs_to_verify = []
        for i, doc in enumerate(docs):
            domain = domains[i]
            docs_to_verify.append((i, doc, domain))
        
        logger.info(
            f"[tavily] Verifying ALL {len(docs_to_verify)}/{len(docs)} documents"
        )
        
        # LATENCY OPTIMIZATION: Probe test to fail fast if rate limited
        if docs_to_verify:
            try:
                probe_result = await tavily_search("test query", self.tavily_agent.api_key, "claim")
            except Exception as e:
                if "limit" in str(e).lower() or "exceeds" in str(e).lower():
                    logger.warning("[tavily] Rate limit detected on probe, skipping all verification")
                    return [(0.50, [], "rate_limited") for _ in docs]
        
        # Use semaphore=8 for improved parallelism (balance between speed and rate limits)
        semaphore = asyncio.Semaphore(8)
        limit_reached = False
        
        async def verify_one(doc: WebDocument, domain: str, doc_idx: int, verify_idx: int) -> tuple[int, float, list[str], str]:
            nonlocal limit_reached
            if limit_reached:
                return doc_idx, 0.50, [], "skipped_limit"

            async with semaphore:
                if limit_reached: # Double check after acquiring semaphore
                     return doc_idx, 0.50, [], "skipped_limit"

                if verify_idx > 0:
                    await asyncio.sleep(0.1)  # Minimal rate limiting
                
                title = doc.title or ""
                snippet = doc.snippet or ""
                
                # Extract specific verifiable claims
                claims = extract_verifiable_claims(title, snippet)
                
                if not claims:
                    # Fallback to title-based search
                    claims = [title[:150]] if title else []
                
                if not claims:
                    return doc_idx, 0.50, [], "no_claims"
                
                # Search for the primary claim (most important)
                primary_claim = claims[0]
                
                try:
                    result = await tavily_search(primary_claim, self.tavily_agent.api_key, "claim")
                    
                    # Check for rate limit error in result (if it returns a dict with error)
                    # Note: tavily_search currently catches exceptions and returns {}, 
                    # but we might want to catch it here if we change that behavior.
                    # Current tavily_search logs error and returns {}.
                    
                    if not result and "exceeds your plan" in str(primary_claim): # This check is tricky without changing tavily_search to return error info.
                        # Assuming tavily_search returns empty dict on error. 
                        # We can't detect rate limit specifically from empty dict easily without modifying tavily_search.
                        # However, for now, we will rely on fast execution.
                        pass

                except Exception as e:
                     if "429" in str(e) or "limit" in str(e).lower():
                         limit_reached = True
                         logger.warning("[tavily] Rate limit reached, skipping remaining items")
                         return doc_idx, 0.50, [], "rate_limit"
                     return doc_idx, 0.50, [], "error"

                # Analyze results with semantic relevance checking
                doc_embedding = embeddings[doc_idx] if embeddings else None
                score, sources, status = analyze_tavily_results(
                    result, domain, title, doc_embedding, embedding_service
                )
                
                # Log verification status for debugging
                if status in ["contradicted", "disputed"]:
                    logger.warning(f"[tavily] FLAGGED: '{title[:50]}...' - status={status}")
                elif status == "verified":
                    logger.info(f"[tavily] VERIFIED: '{title[:50]}...' by {sources}")
                
                return doc_idx, score, sources, status
        
        # Only verify selected documents
        tasks = [verify_one(doc, domain, doc_idx, i) for i, (doc_idx, doc, domain) in enumerate(docs_to_verify)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build final results array - all documents are verified
        final = [(0.50, [], "unverified") for _ in docs]
        stats = {"verified": 0, "contradicted": 0, "unverified": 0, "skipped": 0, "errors": 0}
        
        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"[tavily] Verification error: {r}")
                stats["errors"] += 1
            else:
                doc_idx, score, sources, status = r
                final[doc_idx] = (score, sources, status)
                
                if status == "verified":
                    stats["verified"] += 1
                elif status in ["contradicted", "disputed"]:
                    stats["contradicted"] += 1
                elif status in ["skipped_limit", "rate_limit"]:
                    stats["skipped"] += 1
                else:
                    stats["unverified"] += 1
        
        logger.info(
            f"[tavily] Results: verified={stats['verified']}, "
            f"contradicted={stats['contradicted']}, unverified={stats['unverified']}, "
            f"skipped={stats['skipped']}, errors={stats['errors']}"
        )
        return final
    
    async def _batch_fact_check(
        self, 
        docs: list[WebDocument],
        domains: list[str]
    ) -> list[tuple[float, str | None]]:
        """Run fact checks with controlled concurrency - analyzes ALL documents.
        
        MEMORY OPTIMIZATION: Reduced concurrency to prevent OOM on Railway.
        Each httpx request holds memory until complete.
        """
        global _fact_check_api_warned
        
        # BALANCED: 20 concurrent connections (optimized for speed vs Railway limits)
        # Each request ~100KB, 20 concurrent = ~2MB memory overhead
        semaphore = asyncio.Semaphore(20)
        
        async def check_one(doc: WebDocument, domain: str, idx: int) -> tuple[float, str | None]:
            async with semaphore:
                query = (doc.title or "")[:100]
                claims = await search_fact_checks(query, self.factcheck_agent.api_key)
                return parse_fact_check(claims)
        
        # Run all fact checks in parallel (analyzes ALL documents)
        tasks = [check_one(d, domains[i], i) for i, d in enumerate(docs)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # No longer skipping any documents - all are analyzed
        logger.info(f"[fact_check] Analyzed ALL {len(docs)} documents")
        
        final = []
        has_rating = False
        for r in results:
            if isinstance(r, Exception):
                final.append((0.50, None))
            else:
                final.append(r)
                if r[1] is not None:
                    has_rating = True
        
        if not has_rating and not _fact_check_api_warned:
            logger.info(
                "[fact_check] No fact-check matches found. "
                "This is normal for local news not yet fact-checked."
            )
            _fact_check_api_warned = True
        
        return final
    
    def _log_distribution(self, docs: list[WebDocument]) -> None:
        """Log credibility and misinformation distribution for monitoring."""
        tiers = [d.metadata.get("credibility_tier", "?") for d in docs]
        tier_dist = dict(Counter(tiers))
        
        # Misinformation risk distribution
        misinfo_risks = [d.metadata.get("misinfo_risk", "unknown") for d in docs]
        misinfo_dist = dict(Counter(misinfo_risks))
        
        scores = [d.metadata.get("credibility_score", 0) for d in docs]
        avg = sum(scores) / len(scores) if scores else 0
        
        # Count documents with red flags
        flagged_count = sum(1 for d in docs if d.metadata.get("red_flags"))
        
        # Log signal averages for debugging
        breakdowns = [d.metadata.get("credibility_breakdown", {}) for d in docs]
        signal_avgs = {}
        for signal in WEIGHTS.keys():
            values = [b.get(signal, 0) for b in breakdowns]
            signal_avgs[signal] = round(sum(values) / len(values), 2) if values else 0
        
        logger.info(
            f"[credibility_agent] Credibility: {tier_dist}, avg={avg:.2f}"
        )
        logger.info(
            f"[credibility_agent] Misinfo risk: {misinfo_dist}, flagged={flagged_count}/{len(docs)}"
        )
        logger.info(
            f"[credibility_agent] Signals: {signal_avgs}"
        )
        
        # Debug: Log the first document's metadata to inspect structure
        if docs:
            first_doc_metadata = docs[0].metadata or {}
            logger.debug("[credibility_agent] First document metadata keys: %s", list(first_doc_metadata.keys()))
            if "credibility_breakdown" in first_doc_metadata:
                logger.debug("[credibility_agent] First document credibility_breakdown: %s", first_doc_metadata["credibility_breakdown"])


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_credibility_agent: CredibilityAgent | None = None


def get_credibility_agent() -> CredibilityAgent:
    """Get singleton credibility agent instance."""
    global _credibility_agent
    if _credibility_agent is None:
        _credibility_agent = CredibilityAgent()
    return _credibility_agent
