"""Citation verification module.

Verifies that in-line citations in generated summaries actually match
their source documents and accurately represent the cited content.

Supports TWO citation formats:
1. URL-based (preferred): [Src: https://example.com/article | Cred: 0.XX | Sent: SENTIMENT]
2. Domain-based (fallback): [Src: example.com | Cred: 0.XX | Sent: SENTIMENT]
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class CitationVerifier:
    """Verifies in-line citations against source documents.

    Checks:
    1. Citation format validity
    2. URL matches a source document (with alias resolution)
    3. Credibility score is accurate (within ±0.08)
    4. Sentiment label matches document
    5. Cited document semantically supports the claim
    """

    # Citation format: [Src: URL_OR_DOMAIN | Cred: 0.XX | Sent: SENTIMENT]
    # Supports both full URLs and domain-only citations
    CITATION_PATTERN = re.compile(
        r'\[Src:\s*([^\|]+)\s*\|\s*Cred:\s*([\d.]+)\s*\|\s*Sent:\s*(\w+)\]'
    )

    # Production-grade thresholds (relaxed for LLM generation variance)
    CREDIBILITY_TOLERANCE = 0.08  # ±0.08 (handles LLM rounding to 1 decimal)
    VALIDITY_THRESHOLD = 0.60  # 60% accuracy (domain match is primary signal)

    # Domain alias map for Philippine media (LLM uses common names, URLs use official domains)
    # This is a SAFETY NET for when LLM ignores prompt instructions and generates from memory
    DOMAIN_ALIASES = {
        # GMA Network
        "gmanews.tv": "gmanetwork.com",
        "gma news": "gmanetwork.com",
        "gma network": "gmanetwork.com",
        "gma": "gmanetwork.com",
        # ABS-CBN
        "abs-cbn.com": "abs-cbn.news",
        "abs-cbn news": "abs-cbn.news",
        "abs-cbn": "abs-cbn.news",
        "philstar": "philstar.com",
        "the philstar": "philstar.com",
        # Manila Bulletin
        "mb.com.ph": "mb.com.ph",
        "manila bulletin": "mb.com.ph",
        "mb": "mb.com.ph",
        "manila-bulletin.net": "mb.com.ph",  # Common variant
        "manila bulletin net": "mb.com.ph",
        # SunStar
        "sunstar.com.ph": "sunstar.com.ph",
        "sunstar baguio": "sunstar.com.ph",
        "sunstar": "sunstar.com.ph",
        # Philippine Information Agency
        "pia.gov.ph": "pia.gov.ph",
        "pia": "pia.gov.ph",
        # Baguio Herald
        "baguioherald.com": "baguioherald.com",
        "baguio herald": "baguioherald.com",
        # Cordillera Today / Cordillera Sun
        "cordilleratoday.com": "cordilleratoday.com",
        "cordillera today": "cordilleratoday.com",
        "cordillera sun": "cordilleratoday.com",
        "cordilleransun.com": "cordilleratoday.com",
        # Northern Luzon / RNG Luzon
        "nlsentinel.com": "nlsentinel.com",
        "northern luzon sentinel": "nlsentinel.com",
        "rngluzon": "nlsentinel.com",
        "rng luzon": "nlsentinel.com",
        "northern luzon": "nlsentinel.com",
        # Facebook (various URL formats)
        "facebook.com": "facebook.com",
        "fb.com": "facebook.com",
        "fb": "facebook.com",
        # Reddit
        "reddit.com": "reddit.com",
        "www.reddit.com": "reddit.com",
        # Inquirer
        "inquirer.net": "inquirer.net",
        "newsinfo.inquirer.net": "inquirer.net",
        # PNA
        "pna.gov.ph": "pna.gov.ph",
        "philippine news agency": "pna.gov.ph",
        # Good Morning Baguio
        "goodmorningbaguio.com": "goodmorningbaguio.com",
        "good morning baguio": "goodmorningbaguio.com",
        # WordPress blogs
        "wordpress.com": "wordpress.com",
        "tongtongantiumili.wordpress.com": "tongtongantiumili.wordpress.com",
        # Additional Philippine news sites
        "rappler.com": "rappler.com",
        "philstar.com": "philstar.com",
        "businessworld.com.ph": "businessworld.com.ph",
        "manilatimes.net": "manilatimes.net",
        # DENR (government)
        "denr.gov.ph": "denr.gov.ph",
        # Common typos and variants
        "denr": "denr.gov.ph",
        "veritas": "veritasph.com",
        "veritas ph": "veritasph.com",
        "veritasph.com": "veritasph.com",
    }

    def __init__(self):
        """Initialize citation verifier."""
        logger.info("[CitationVerifier] Initialized with production thresholds")

    def extract_citations(self, text: str) -> list[dict[str, Any]]:
        """Extract all citations from text.

        Args:
            text: Text containing citations in format [Src: ... | Cred: ... | Sent: ...]

        Returns:
            List of citation dicts with:
            - raw: Original citation string
            - source: Extracted URL or domain
            - credibility: Credibility score (float)
            - sentiment: Sentiment label
            - position: Character position in text
        """
        citations = []
        for match in self.CITATION_PATTERN.finditer(text):
            source = match.group(1).strip()
            citations.append({
                "raw": match.group(0),
                "source": source,
                "credibility": float(match.group(2)),
                "sentiment": match.group(3).strip(),
                "position": match.start(),
            })
        logger.info(f"[CitationVerifier] Extracted {len(citations)} citations")
        return citations

    def extract_claim_with_citation(
        self,
        text: str,
        citation_pos: int
    ) -> tuple[str, int, int]:
        """Extract the claim text associated with a citation.

        Strategy: Get text immediately preceding the citation (up to 150 chars or sentence boundary).

        Args:
            text: Full text containing claim + citation
            citation_pos: Position of citation in text

        Returns:
            Tuple of (claim_text, start_pos, end_pos)
        """
        # Look backwards from citation to find claim
        start = max(0, citation_pos - 200)
        claim_segment = text[start:citation_pos]

        # Find sentence boundary (look for period, newline, or start)
        boundary_chars = ['.', '\n', '!', '?', ':']
        claim_start = len(claim_segment)
        for i in range(len(claim_segment) - 1, -1, -1):
            if claim_segment[i] in boundary_chars:
                claim_start = i + 1
                break

        claim_text = claim_segment[claim_start:].strip()

        # Clean up: remove leading conjunctions, quotes
        claim_text = re.sub(r'^(And|But|However|Moreover|Furthermore|The|A|An)\s+', '', claim_text)
        claim_text = claim_text.strip('"\'').strip()

        return claim_text, start + claim_start, citation_pos

    def find_cited_document(
        self,
        citation: dict[str, Any],
        documents: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Find the document matching a citation.

        PRODUCTION STRATEGY (3-tier fallback):
        1. Metadata matching (sentiment + credibility) - PRIMARY
        2. Direct URL match - SECONDARY
        3. Domain alias resolution - FALLBACK

        Args:
            citation: Citation dict with 'source', 'credibility', 'sentiment' keys
            documents: List of source documents with metadata

        Returns:
            Matching document or None
        """
        cited_cred = citation.get("credibility", 0.0)
        cited_sent = citation.get("sentiment", "").lower().strip()
        cited_source = citation.get("source", "").lower().strip()
        
        logger.debug(f"[CitationVerifier] Looking for: cred={cited_cred}, sent={cited_sent}, source={cited_source}")

        # ============================================================
        # TIER 1: METADATA MATCHING (PRIMARY - Most Accurate)
        # Match on sentiment + credibility (what LLM actually copies correctly)
        # ============================================================
        cred_tolerance = 0.03  # ±0.03 tolerance for rounding
        metadata_matches = []
        
        for doc in documents:
            doc_cred = doc.get("metadata", {}).get("credibility_score", doc.get("credibility_score", 0.0))
            doc_sent = doc.get("sentiment", "neutral").lower().strip()
            
            # Check sentiment match (exact)
            sent_match = cited_sent == doc_sent
            
            # Check credibility match (with tolerance)
            cred_match = abs(cited_cred - doc_cred) <= cred_tolerance
            
            if sent_match and cred_match:
                metadata_matches.append((doc, abs(cited_cred - doc_cred)))
                logger.debug(f"[CitationVerifier] Metadata match: cred={doc_cred}, sent={doc_sent}, diff={abs(cited_cred - doc_cred):.3f}")
        
        # Return best metadata match (lowest cred difference)
        if metadata_matches:
            # TIEBREAKER: If multiple docs have same metadata, use domain matching
            if len(metadata_matches) > 1:
                cited_domain = self._extract_domain(cited_source) if cited_source else None
                logger.debug(f"[CitationVerifier] Collision detected ({len(metadata_matches)} docs), using domain tiebreaker: {cited_domain}")
                
                for doc, diff in metadata_matches:
                    doc_url = doc.get("url", "")
                    if doc_url and cited_domain:
                        doc_domain = self._extract_domain(doc_url)
                        # Check if domains match (including alias resolution)
                        resolved_cited = self.DOMAIN_ALIASES.get(cited_domain, cited_domain)
                        resolved_doc = self.DOMAIN_ALIASES.get(doc_domain, doc_domain)
                        
                        if resolved_cited == doc_domain or resolved_cited == resolved_doc or cited_domain == doc_domain:
                            logger.info(f"[CitationVerifier] Found metadata + domain match (Tier 1, tiebreaker)")
                            return doc
            
            best_match = min(metadata_matches, key=lambda x: x[1])[0]
            logger.info(f"[CitationVerifier] Found metadata match (Tier 1)")
            return best_match

        # ============================================================
        # TIER 2: DIRECT URL MATCH (SECONDARY)
        # ============================================================
        if cited_source.startswith('http://') or cited_source.startswith('https://'):
            logger.debug(f"[CitationVerifier] Attempting direct URL match for: {cited_source}")
            
            source_normalized = self._normalize_url(cited_source)
            
            for doc in documents:
                doc_url = doc.get("url", "")
                if not doc_url:
                    continue
                doc_url_str = str(doc_url).lower().strip()
                doc_url_normalized = self._normalize_url(doc_url_str)
                
                if source_normalized == doc_url_normalized:
                    logger.info(f"[CitationVerifier] Found URL match (Tier 2)")
                    return doc
                
                if doc_url_normalized.startswith(source_normalized) or source_normalized.startswith(doc_url_normalized):
                    logger.info(f"[CitationVerifier] Found URL prefix match (Tier 2)")
                    return doc

        # ============================================================
        # TIER 3: DOMAIN ALIAS RESOLUTION (FALLBACK)
        # ============================================================
        cited_domain = cited_source
        
        # Resolve domain aliases
        resolved_domain = self.DOMAIN_ALIASES.get(cited_domain, cited_domain)
        if resolved_domain != cited_domain:
            logger.debug(f"[CitationVerifier] Resolved alias: '{cited_domain}' → '{resolved_domain}'")
        
        logger.debug(f"[CitationVerifier] Looking for domain: '{resolved_domain}' (original: '{cited_domain}')")

        best_match = None
        best_score = 0.0

        for doc in documents:
            doc_url = doc.get("url", "")
            if not doc_url:
                continue

            if not isinstance(doc_url, str):
                doc_url = str(doc_url)

            doc_domain = self._extract_domain(doc_url)

            if resolved_domain == doc_domain or cited_domain == doc_domain:
                logger.debug(f"[CitationVerifier] Exact domain match: '{cited_domain}' -> '{doc_domain}'")
                return doc

            if resolved_domain in doc_domain or doc_domain in resolved_domain:
                score = 0.9
                if score > best_score:
                    best_score = score
                    best_match = doc
                    logger.debug(f"[CitationVerifier] Subdomain match: '{cited_domain}' -> '{doc_domain}' (score: {score})")
                continue

            cited_base = resolved_domain.replace('.com', '').replace('.ph', '').replace('.net', '').replace('www.', '')
            doc_base = doc_domain.replace('.com', '').replace('.ph', '').replace('.net', '').replace('www.', '')
            
            if cited_base in doc_base or doc_base in cited_base:
                score = 0.7
                if score > best_score:
                    best_score = score
                    best_match = doc
                    logger.debug(f"[CitationVerifier] Partial domain match: '{cited_domain}' -> '{doc_domain}' (score: {score})")

        if best_match:
            logger.info(f"[CitationVerifier] Found domain match (Tier 3, score: {best_score})")
            return best_match

        logger.warning(f"[CitationVerifier] No match found for source: '{cited_source}'")
        return None

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for matching.

        - Remove fragment identifiers (#section)
        - Normalize trailing slashes
        """
        # Remove fragment
        url = url.split('#')[0]
        # Normalize trailing slashes
        url = url.rstrip('/')
        return url

    def _extract_path(self, url: str) -> str:
        """Extract path component from URL.

        Example: https://example.com/path/to/page?query=1 → /path/to/page
        """
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Remove domain
        path_start = url.find('/')
        if path_start == -1:
            return ''
        # Remove query params
        path = url[path_start:].split('?')[0]
        return path

    def _extract_domain(self, url: str | Any) -> str:
        """Extract domain from URL.

        Examples:
            https://facebook.com/post/123 → facebook.com
            https://mb.com.ph/2023/3/17/article → mb.com.ph

        Args:
            url: URL string or HttpUrl object (Pydantic)

        Returns:
            Extracted domain
        """
        # Convert HttpUrl object to string (Pydantic type handling)
        if not isinstance(url, str):
            url = str(url)

        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Remove path
        domain = url.split('/')[0]
        # Remove www.
        domain = re.sub(r'^www\.', '', domain)
        return domain

    def verify_citation_accuracy(
        self,
        citation: dict[str, Any],
        document: dict[str, Any]
    ) -> dict[str, Any]:
        """Verify citation metadata accuracy.

        Args:
            citation: Extracted citation with domain, credibility, sentiment
            document: Source document with metadata

        Returns:
            Verification result:
            - domain_match: bool
            - credibility_accurate: bool (within ±0.03)
            - sentiment_match: bool
            - accuracy_score: float (0.0-1.0)
        """
        # Check domain match (already done in find_cited_document)
        domain_match = True

        # Check credibility score accuracy (TIGHTER: ±0.03)
        doc_credibility = document.get("metadata", {}).get(
            "credibility_score",
            document.get("credibility_score", 0.0)
        )
        cred_diff = abs(citation["credibility"] - doc_credibility)
        credibility_accurate = cred_diff <= self.CREDIBILITY_TOLERANCE

        # Check sentiment match
        doc_sentiment = document.get("sentiment", "neutral").lower()
        citation_sentiment = citation["sentiment"].lower()

        # Normalize sentiment labels
        sentiment_map = {
            "negative": ["negative", "neg"],
            "neutral": ["neutral", "neu"],
            "positive": ["positive", "pos"],
        }

        sentiment_match = (
            citation_sentiment in sentiment_map.get(doc_sentiment, [doc_sentiment])
        )

        # Calculate accuracy score (equal weights)
        accuracy_score = (
            (1.0 if domain_match else 0.0) * 0.34 +
            (1.0 if credibility_accurate else 0.0) * 0.33 +
            (1.0 if sentiment_match else 0.0) * 0.33
        )

        return {
            "domain_match": domain_match,
            "credibility_accurate": credibility_accurate,
            "sentiment_match": sentiment_match,
            "accuracy_score": round(accuracy_score, 3),
            "cited_credibility": citation["credibility"],
            "actual_credibility": doc_credibility,
            "credibility_diff": round(cred_diff, 3),
            "cited_sentiment": citation["sentiment"],
            "actual_sentiment": doc_sentiment,
        }

    async def verify_claim_citation_pair(
        self,
        claim_text: str,
        citation: dict[str, Any],
        document: dict[str, Any],
        entailment_checker: Any | None = None
    ) -> dict[str, Any]:
        """Verify that a claim is supported by its cited document.

        Args:
            claim_text: The factual claim (without citation)
            citation: The citation associated with the claim
            document: The cited source document
            entailment_checker: Optional EntailmentChecker for NLI verification

        Returns:
            Verification result:
            - citation_accurate: bool (metadata matches)
            - claim_entailed: bool (NLI verification)
            - is_hallucination: bool (claim not supported by cited source)
            - hallucination_type: str | None (fabricated, misattributed, exaggerated)
        """
        # Step 1: Verify citation metadata accuracy
        metadata_result = self.verify_citation_accuracy(citation, document)

        # Step 2: Verify claim is entailed by the cited document (not just any document)
        claim_entailed = False
        entailment_score = 0.0

        if entailment_checker:
            try:
                result = await entailment_checker.check_entailment(
                    claim=claim_text,
                    documents=[document],
                    top_k=1,
                )
                entailment_score = result.get("entailment_score", 0.0)
                claim_entailed = entailment_score >= 0.75
            except Exception as exc:
                logger.warning(f"[CitationVerifier] NLI check failed: {exc}")
                claim_entailed = False
                entailment_score = 0.0

        # Step 3: Determine hallucination/misattribution status
        # SEPARATE: Hallucination (claim false) vs Misattribution (claim true, wrong source)
        is_hallucination = not claim_entailed and metadata_result["accuracy_score"] < 0.5
        is_misattribution = claim_entailed and metadata_result["accuracy_score"] < self.VALIDITY_THRESHOLD

        hallucination_type = None
        if is_hallucination:
            if not metadata_result["domain_match"]:
                hallucination_type = "fabricated_source"
            else:
                hallucination_type = "unsupported_by_citation"
        elif is_misattribution:
            hallucination_type = "misattribution"

        # Step 4: Calculate overall verification score
        verification_score = (
            metadata_result["accuracy_score"] * 0.4 +
            (1.0 if claim_entailed else 0.0) * 0.6
        )

        return {
            "citation_accurate": metadata_result["accuracy_score"] >= self.VALIDITY_THRESHOLD,
            "claim_entailed": claim_entailed,
            "entailment_score": entailment_score,
            "is_hallucination": is_hallucination,
            "is_misattribution": is_misattribution,
            "hallucination_type": hallucination_type,
            "verification_score": round(verification_score, 3),
            "metadata_result": metadata_result,
        }

    def verify_all_citations(
        self,
        summary: str,
        documents: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Verify all citations in a summary.

        Args:
            summary: Generated narrative summary with citations
            documents: Source documents used for generation

        Returns:
            Verification report:
            - total_citations: Number of citations found
            - valid_citations: Citations with accurate metadata and matching source
            - invalid_citations: Citations without matching documents
            - citation_accuracy_rate: valid / total
            - citation_details: List of detailed results
        """
        citations = self.extract_citations(summary)

        if not citations:
            logger.warning("[CitationVerifier] No citations found in summary")
            return {
                "total_citations": 0,
                "valid_citations": 0,
                "invalid_citations": 0,
                "citation_accuracy_rate": 0.0,
                "citation_details": [],
            }

        logger.info(f"[CitationVerifier] Verifying {len(citations)} citations against {len(documents)} documents")
        
        citation_details = []
        valid_count = 0

        for citation in citations:
            # Find matching document
            matched_doc = self.find_cited_document(citation, documents)

            if matched_doc:
                # Verify citation accuracy
                metadata_result = self.verify_citation_accuracy(citation, matched_doc)
                # Accept matches with accuracy >= 0.70 (includes partial domain matches)
                is_valid = metadata_result["accuracy_score"] >= 0.70
                if is_valid:
                    valid_count += 1
                else:
                    logger.debug(f"[CitationVerifier] Citation '{citation['source']}' matched but accuracy too low: {metadata_result['accuracy_score']:.3f} (need >= 0.70)")

                citation_details.append({
                    "citation": citation["raw"],
                    "source": citation["source"],
                    "is_valid": is_valid,
                    "accuracy_score": metadata_result["accuracy_score"],
                    "credibility_match": metadata_result["credibility_accurate"],
                    "sentiment_match": metadata_result["sentiment_match"],
                    "source_url": matched_doc.get("url"),
                })
            else:
                # No matching document found
                citation_details.append({
                    "citation": citation["raw"],
                    "source": citation["source"],
                    "is_valid": False,
                    "accuracy_score": 0.0,
                    "credibility_match": False,
                    "sentiment_match": False,
                    "source_url": None,
                    "error": "No matching source document found",
                })

        citation_accuracy_rate = valid_count / len(citations) if citations else 0.0
        
        logger.info(f"[CitationVerifier] Verification complete: {valid_count}/{len(citations)} valid ({citation_accuracy_rate:.1%})")

        return {
            "total_citations": len(citations),
            "valid_citations": valid_count,
            "invalid_citations": len(citations) - valid_count,
            "citation_accuracy_rate": round(citation_accuracy_rate, 3),
            "citation_details": citation_details,
        }
