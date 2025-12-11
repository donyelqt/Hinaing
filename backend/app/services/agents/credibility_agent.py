"""Multi-Signal Credibility & Source Quality Assessment Agent for Thesis.

5-Signal Ensemble for Source Quality Filtering:
1. Domain Trust (25%) - Source reputation based on known domains
2. Internal Cross-Reference (20%) - SEMANTIC corroboration using MiniLM embeddings
3. Google Fact Check API (15%) - External fact-checker verification
4. LLM Analysis (20%) - AI content quality assessment (Gemini)
5. External Cross-Reference (20%) - Real-time web verification via Tavily

Note: This is a source quality filtering mechanism, not a misinformation detector.
Validation requires labeled ground truth data (documented as thesis limitation).

Each signal is independently measurable for thesis ablation studies.
"""
from __future__ import annotations

import asyncio
import json
import logging
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


async def search_fact_checks(query: str, api_key: str) -> list[dict]:
    """Query Google Fact Check API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
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
        # Use Gemini 2.0 Flash for speed and efficiency
        self.model = genai.GenerativeModel(
            "gemini-2.0-flash-exp",
            safety_settings=SAFETY_SETTINGS,
        )
        self.batch_size = 12
    
    def analyze_batch(self, docs: list[WebDocument]) -> list[dict]:
        """Analyze all documents in batches in PARALLEL."""
        # Create batches
        batches = [docs[i:i + self.batch_size] for i in range(0, len(docs), self.batch_size)]
        
        results = []
        # Execute batches in parallel threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            batch_results = list(executor.map(self._analyze_batch, batches))
            
        for res in batch_results:
            results.extend(res)
            
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
                    max_output_tokens=1500,
                ),
            )
            return self._parse_response(resp.text, len(batch))
        except Exception as e:
            logger.warning(f"[llm_credibility] Gemini 2.0 Flash error: {e}")
            return [{"score": 0.50, "reasoning": "Analysis unavailable", "red_flags": []}] * len(batch)
    
    def _parse_response(self, text: str, count: int) -> list[dict]:
        """Parse LLM JSON response."""
        default = {"score": 0.50, "reasoning": "", "red_flags": [], "misinfo_risk": "unknown"}
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
                        results[idx] = {
                            "score": min(1.0, max(0.0, float(item.get("score", 0.5)))),
                            "reasoning": str(item.get("reasoning", "")),
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
) -> tuple[float, list[dict], str]:
    """Analyze Tavily results for claim verification.
    
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
    
    # Analyze Tavily's AI answer for verification signals
    answer_lower = answer.lower() if answer else ""
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
        content = (result.get("content", "") + title).lower()
        
        # Skip if same domain as original
        if domain == original_domain:
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


# ─────────────────────────────────────────────────────────────────────────────
# Enhanced Credibility Agent (5 Signals)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EnhancedCredibilityAgent:
    """5-Signal Source Quality Assessment Agent.
    
    Signals:
    1. Domain Trust (25%) - Known source reputation
    2. Internal Cross-Reference (20%) - Semantic corroboration within results
    3. Fact Check API (15%) - External verification (Google)
    4. LLM Analysis (20%) - AI content assessment (Gemini)
    5. External Cross-Reference (20%) - Real-time web verification (Tavily)
    """
    
    _llm: LLMCredibilityAnalyzer | None = field(default=None, init=False)
    _api_key: str | None = field(default=None, init=False)
    _tavily_api_key: str | None = field(default=None, init=False)
    
    def __post_init__(self):
        settings = get_settings()
        self._api_key = getattr(settings, "google_fact_check_api_key", None)
        if not self._api_key:
            self._api_key = settings.gemini_api_key
        self._tavily_api_key = getattr(settings, "tavily_api_key", None)
        self._llm = LLMCredibilityAnalyzer()
        
        if self._tavily_api_key:
            logger.info("[credibility_agent] Tavily API enabled for claim verification")
        else:
            logger.warning("[credibility_agent] Tavily API key not set - Signal 7 disabled")
    
    async def run(self, documents: list[WebDocument]) -> list[WebDocument]:
        """Assess credibility for all documents using 7 signals."""
        if not documents:
            return []
        
        n = len(documents)
        tavily_enabled = bool(self._tavily_api_key)
        logger.info(f"[credibility_agent] Analyzing {n} documents (7 signals, tavily={tavily_enabled})")
        
        # ─── Signal 1: Domain Trust (sync, fast) ───
        domains = [_extract_domain(str(d.url) if d.url else None) for d in documents]
        domain_scores = [score_domain(d) for d in domains]
        
        # ─── Compute Embeddings for Semantic Cross-Reference ───
        embedding_service = get_embedding_service()
        doc_texts = [
            f"{d.title or ''} {d.snippet or ''}"[:500]  # Limit text length
            for d in documents
        ]
        logger.info(f"[credibility_agent] Computing semantic embeddings for {n} documents")
        embeddings = embedding_service.embed_batch(doc_texts, batch_size=16)
        
        # ─── Signal 2: Semantic Cross-Reference (using embeddings) ───
        cross_ref_scores, corroborator_counts = compute_semantic_cross_reference_scores(
            documents, embeddings, domains, similarity_threshold=0.70
        )
        
        # ─── Signal 3: Fact Check API (async) ───
        fact_results = await self._batch_fact_check(documents)
        
        # ─── Signal 4: LLM Analysis (sync, batched) ───
        llm_results = self._llm.analyze_batch(documents)
        
        # ─── Signal 5: Tavily External Cross-Reference (async) ───
        tavily_results = await self._batch_tavily_verify(documents, domains)
        tavily_scores = [r[0] for r in tavily_results]
        tavily_sources = [r[1] for r in tavily_results]
        tavily_statuses = [r[2] if len(r) > 2 else "unknown" for r in tavily_results]
        
        # ─── Combine with Weights ───
        enriched = []
        for i, doc in enumerate(documents):
            fact_score, fact_rating = fact_results[i]
            llm_data = llm_results[i]
            
            # Weighted combination (5 signals)
            final_score = (
                WEIGHTS["domain"] * domain_scores[i] +
                WEIGHTS["cross_reference"] * cross_ref_scores[i] +
                WEIGHTS["fact_check"] * fact_score +
                WEIGHTS["llm"] * llm_data["score"] +
                WEIGHTS["tavily"] * tavily_scores[i]
            )
            
            # Determine tier
            if final_score >= 0.75:
                tier = "high"
            elif final_score >= 0.55:
                tier = "medium"
            elif final_score >= 0.35:
                tier = "low"
            else:
                tier = "very_low"
            
            # Red flags from LLM analysis
            all_red_flags = llm_data.get("red_flags", [])
            
            # Determine quality tier based on score
            llm_misinfo = llm_data.get("misinfo_risk", "unknown")
            if llm_misinfo == "high" or len(all_red_flags) >= 2:
                misinfo_risk = "high"
            elif llm_misinfo == "medium" or len(all_red_flags) >= 1:
                misinfo_risk = "medium"
            else:
                misinfo_risk = "low" if final_score >= 0.55 else "medium"
            
            enriched.append(doc.model_copy(update={
                "metadata": {
                    **(doc.metadata or {}),
                    "credibility_score": round(final_score, 3),
                    "credibility_tier": tier,
                    "misinfo_risk": misinfo_risk,
                    "credibility_breakdown": {
                        "domain": round(domain_scores[i], 3),
                        "cross_reference": round(cross_ref_scores[i], 3),
                        "fact_check": round(fact_score, 3),
                        "llm": round(llm_data["score"], 3),
                        "tavily": round(tavily_scores[i], 3),
                    },
                    "tavily_verified_sources": tavily_sources[i],
                    "tavily_verification_status": tavily_statuses[i],
                    "corroborating_sources": corroborator_counts[i],
                    "fact_check_rating": fact_rating,
                    "llm_reasoning": llm_data.get("reasoning", ""),
                    "red_flags": all_red_flags,
                    "source_domain": domains[i],
                }
            }))
        
        self._log_distribution(enriched)
        return enriched
    
    async def _batch_tavily_verify(
        self,
        docs: list[WebDocument],
        domains: list[str],
    ) -> list[tuple[float, list[str], str]]:
        """Run Tavily claim verification with rate limiting.
        
        Uses claim extraction to search for specific verifiable claims,
        not just general topic matching.
        
        Returns:
            List of (score, verified_sources, verification_status) tuples
        """
        if not self._tavily_api_key:
            # Return neutral scores if Tavily not configured
            return [(0.50, [], "disabled") for _ in docs]
        
        # Use semaphore=1 to process Tavily requests sequentially
        # This ensures we catch rate limits immediately and skip remaining items
        semaphore = asyncio.Semaphore(1)
        limit_reached = False
        
        async def verify_one(doc: WebDocument, domain: str, idx: int) -> tuple[float, list[str], str]:
            nonlocal limit_reached
            if limit_reached:
                return 0.50, [], "skipped_limit"

            async with semaphore:
                if limit_reached: # Double check after acquiring semaphore
                     return 0.50, [], "skipped_limit"

                if idx > 0:
                    await asyncio.sleep(0.1)  # Minimal rate limiting
                
                title = doc.title or ""
                snippet = doc.snippet or ""
                
                # Extract specific verifiable claims
                claims = extract_verifiable_claims(title, snippet)
                
                if not claims:
                    # Fallback to title-based search
                    claims = [title[:150]] if title else []
                
                if not claims:
                    return 0.50, [], "no_claims"
                
                # Search for the primary claim (most important)
                primary_claim = claims[0]
                
                try:
                    result = await tavily_search(primary_claim, self._tavily_api_key, "claim")
                    
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
                         return 0.50, [], "rate_limit"
                     return 0.50, [], "error"

                # Analyze results
                score, sources, status = analyze_tavily_results(result, domain, title)
                
                # Log verification status for debugging
                if status in ["contradicted", "disputed"]:
                    logger.warning(f"[tavily] FLAGGED: '{title[:50]}...' - status={status}")
                elif status == "verified":
                    logger.info(f"[tavily] VERIFIED: '{title[:50]}...' by {sources}")
                
                return score, sources, status
        
        tasks = [verify_one(d, domains[i], i) for i, d in enumerate(docs)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final = []
        stats = {"verified": 0, "contradicted": 0, "unverified": 0, "skipped": 0, "errors": 0}
        
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning(f"[tavily] Verification error: {r}")
                final.append((0.50, [], "error"))
                stats["errors"] += 1
            else:
                final.append(r)
                score, sources, status = r
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
        docs: list[WebDocument]
    ) -> list[tuple[float, str | None]]:
        """Run fact checks with rate limiting."""
        global _fact_check_api_warned
        
        semaphore = asyncio.Semaphore(10)
        
        async def check_one(doc: WebDocument, idx: int) -> tuple[float, str | None]:
            async with semaphore:
                # No sleep needed with higher concurrency unless strict rate limits exist
                if idx > 0:
                    # Minimal yield to let event loop breathe but not wait
                    await asyncio.sleep(0)
                query = (doc.title or "")[:100]
                claims = await search_fact_checks(query, self._api_key)
                return parse_fact_check(claims)
        
        tasks = [check_one(d, i) for i, d in enumerate(docs)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
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


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_credibility_agent: EnhancedCredibilityAgent | None = None


def get_credibility_agent() -> EnhancedCredibilityAgent:
    """Get singleton credibility agent instance."""
    global _credibility_agent
    if _credibility_agent is None:
        _credibility_agent = EnhancedCredibilityAgent()
    return _credibility_agent
