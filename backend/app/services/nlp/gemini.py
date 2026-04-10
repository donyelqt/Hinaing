"""LLM-based narrative generation for civic sentiment analysis.

This module provides the LLMNarrativeClient class which synthesizes comprehensive 
narratives from theme insights and documents using Groq LLMs.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Callable

# Legacy imports (kept for fallback agent path - rarely used)
# import google.generativeai as genai
# from ..agents.gemini import run_gemini_agent

from ...core.config import get_settings

logger = logging.getLogger(__name__)


def sanitize_text(text: str | None) -> str:
    """Remove invalid Unicode characters (surrogates) that break Gemini API."""
    if not text:
        return ""
    # Remove surrogate characters (U+D800 to U+DFFF)
    cleaned = re.sub(r'[\ud800-\udfff]', '', str(text))
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
    cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', cleaned)
    return cleaned.strip()


class LLMNarrativeClient:
    """Generates comprehensive narratives from theme insights and documents.
    
    Uses Groq llama-4-scout for fast narrative synthesis:
    - 30K TPM (5x more than 8b-instant)
    - 500K TPD
    - Clean JSON output
    - Handles large narratives without rate limits
    """

    def __init__(self, *, model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct") -> None:
        """Initialize narrative generator with Groq.
        
        Args:
            model_name: Groq model to use for narrative generation
        """
        settings = get_settings()
        self._api_key = settings.groq_api_key
        self._model_name = model_name
        self._model = None

        if self._api_key:
            from ..llm.groq_provider import get_groq_provider
            self._model = get_groq_provider(model_name)
            logger.info(f"[LLMNarrativeClient] Initialized with Groq: {model_name} (30K TPM)")
        else:
            logger.warning("[LLMNarrativeClient] Groq API key not configured")

    @property
    def is_available(self) -> bool:
        return self._model is not None

    async def analyze_snapshot(
        self,
        *,
        window: str,
        focus_areas: list[str],
        documents: list[dict[str, Any]],
        theme_insights: list[dict[str, Any]] | None = None,
        sentiment_distribution: dict[str, float] | None = None,
    ) -> tuple[str | None, list[dict[str, Any]]]:
        # OPTIMIZATION: If theme_insights exist, skip the slow agent path
        # Theme insights are already summarized by Theme Agents (Node 6)
        # This reduces latency from ~40s to ~10s
        if theme_insights and len(theme_insights) > 0:
            logger.info(
                "[LLMNarrativeClient] Using theme_insights for narrative (skipping agent path)",
                extra={"theme_count": len(theme_insights), "doc_count": len(documents)}
            )
            result = await self._run_direct_generation(
                window=window,
                focus_areas=focus_areas,
                documents=documents,  # Still passed for fallback context
                theme_insights=theme_insights,
                sentiment_distribution=sentiment_distribution,
            )
            
            # POST-PROCESSING: Filter invalid citations (safety net for LLM errors)
            if result[0]:  # If summary exists
                result = self._filter_invalid_citations(result[0], result[1], documents)
                # Auto-correct citation status mismatches to match document metadata
                summary_corrected = self._correct_citation_status(result[0], documents)
                result = (summary_corrected, result[1])

            return result
        
        # Fallback: Use agent path only when no theme_insights available
        # NOTE: This path is rarely used since theme_insights are always generated
        # Keeping for backward compatibility but may be removed in future
        agent_instruction = self._build_agent_instruction(window=window, focus_areas=focus_areas)

        try:
            # Legacy agent path - requires run_gemini_agent import
            from ..agents.gemini import run_gemini_agent
            agent_output = await asyncio.to_thread(
                lambda: run_gemini_agent(agent_instruction, documents=documents)
            )
            parsed = self._try_parse_json(agent_output)
            if parsed is not None:
                summary = sanitize_text(parsed.get("summary"))
                insights = self._sanitize_insights(parsed.get("insights") or [])
                return summary, insights
        except Exception:
            logger.exception("Narrative generation agent execution failed")

        # Fallback to direct model invocation if the agent path fails or returns invalid JSON.
        if not self._model:
            return None, []

        return await self._run_direct_generation(
            window=window,
            focus_areas=focus_areas,
            documents=documents,
            theme_insights=theme_insights,
        )

    def _sanitize_insights(self, insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sanitize all text fields in insights to remove surrogates."""
        sanitized = []
        for item in insights:
            if not isinstance(item, dict):
                continue
            clean_item = {
                "category": sanitize_text(item.get("category")),
                "title": sanitize_text(item.get("title")),
                "detail": sanitize_text(item.get("detail")),
            }
            evidence = item.get("evidence")
            if isinstance(evidence, list):
                clean_item["evidence"] = [sanitize_text(str(e)) for e in evidence]
            elif isinstance(evidence, str):
                clean_item["evidence"] = [sanitize_text(evidence)]
            sanitized.append(clean_item)
        return sanitized

    def _filter_invalid_citations(
        self,
        summary: str,
        insights: list[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Filter out citations with domains not in retrieved document set.

        This is a SAFETY NET for when LLM ignores domain constraints.

        Args:
            summary: Generated summary with citations
            insights: Generated insights
            documents: Retrieved documents (source of truth for valid domains)

        Returns:
            Tuple of (filtered_summary, insights)
        """
        # Extract valid domains from retrieved documents
        valid_domains = set()
        for doc in documents:
            url = doc.get('url', '')
            if url:
                domain = str(url).replace('https://', '').replace('http://', '').split('/')[0].replace('www.', '')
                valid_domains.add(domain)

        # Find all citations in summary
        citation_pattern = re.compile(r'\[Src:\s*([^\|]+)\s*\|')

        # Check each citation
        def is_valid_citation(match):
            domain = match.group(1).strip().lower()
            return domain in valid_domains or domain in [d.lower() for d in valid_domains]

        # Log for debugging
        invalid_count = 0
        for match in citation_pattern.finditer(summary):
            domain = match.group(1).strip().lower()
            if domain not in [d.lower() for d in valid_domains]:
                invalid_count += 1
                logger.warning(f"[LLMNarrativeClient] Invalid citation filtered: {domain} (not in {len(valid_domains)} valid domains)")

        if invalid_count > 0:
            logger.info(f"[LLMNarrativeClient] Filtered {invalid_count} invalid citations")

        # Note: We don't remove invalid citations from summary (would break text)
        # But we log them for monitoring and future improvement
        return summary, insights

    def _correct_citation_status(
        self,
        summary: str,
        documents: list[dict[str, Any]],
    ) -> str:
        """Auto-correct citation verification status to match actual document metadata.

        Maps internal status values (vsee_bypass) to user-facing values (verified)
        so the CitationVerifier can match them correctly.
        """
        # Build domain -> user-facing status map
        # Internal values: 'verified', 'vsee_bypass', 'unverified', 'contradicted'
        # User-facing values: 'verified', 'unverified', 'contradicted'
        STATUS_MAP = {
            'verified': 'verified',
            'vsee_bypass': 'verified',  # VSEE-verified docs should show as verified
            'unverified': 'unverified',
            'contradicted': 'contradicted',
        }

        domain_status: dict[str, str] = {}
        for doc in documents:
            url = doc.get('url', '')
            if url:
                domain = str(url).replace('https://', '').replace('http://', '').split('/')[0].replace('www.', '')
                if domain not in domain_status:
                    raw_status = doc.get('metadata', {}).get('tavily_verification_status', 'unverified')
                    domain_status[domain] = STATUS_MAP.get(raw_status, 'unverified')

        # Match citation status in summary and correct mismatches
        status_pattern = re.compile(
            r'(\[Src:\s*[^\|]+\s*\|\s*Sent:\s*[^\|]+\s*\|\s*)(verified|unverified|contradicted|Verified|Unverified|Contradicted)(\])',
            re.IGNORECASE
        )

        corrections = 0

        def correct_match(match: re.Match) -> str:
            nonlocal corrections
            prefix = match.group(1)
            generated_status = match.group(2).lower()
            suffix = match.group(3)

            # Extract domain from the citation
            domain_match = re.search(r'\[Src:\s*([^\|]+)', match.group(0))
            if not domain_match:
                return match.group(0)

            cited_domain = domain_match.group(1).strip().lower()

            # Find actual status from document metadata
            actual_status = None
            for domain, status in domain_status.items():
                if domain.lower() == cited_domain or cited_domain in domain.lower() or domain.lower() in cited_domain:
                    actual_status = status
                    break

            if actual_status and generated_status != actual_status:
                corrections += 1
                logger.debug(f"[LLMNarrativeClient] Corrected: {cited_domain} '{generated_status}' → '{actual_status}'")
                return f"{prefix}{actual_status}{suffix}"

            return match.group(0)

        corrected = status_pattern.sub(correct_match, summary)

        if corrections > 0:
            logger.info(f"[LLMNarrativeClient] Corrected {corrections} citation statuses")

        return corrected

    def _convert_citation_numbers(
        self,
        summary: str,
        insights: list[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]]]:
        """Convert [1], [2], [3] citation numbers to full citation format.
        
        Args:
            summary: Generated summary with [1], [2], [3] citations
            insights: Generated insights
            documents: Retrieved documents (source for citation metadata)
        
        Returns:
            Tuple of (converted_summary, insights)
        """
        # Build citation menu (same as in prompt)
        citation_map = {}
        for idx, doc in enumerate(documents[:30], start=1):
            url = doc.get('url', '')
            if url:
                url_short = str(url).replace('https://', '').replace('http://', '')
                if len(url_short) > 60:
                    url_short = url_short[:57] + '...'
                credibility = doc.get('metadata', {}).get('credibility_score', doc.get('credibility_score', 0.0))
                sentiment = doc.get('sentiment', 'neutral').capitalize()
                verification_status = doc.get('metadata', {}).get('tavily_verification_status', 'unverified')
                citation_map[idx] = {
                    'url': url_short,
                    'credibility': round(credibility, 2),
                    'sentiment': sentiment,
                    'verification_status': verification_status,
                }
        
        # Convert [1], [2], [3] to [Src: url | Cred: X.XX | Sent: Y | Verified/Unverified]
        def replace_citation(match):
            num = int(match.group(1))
            if num in citation_map:
                item = citation_map[num]
                # Add verification status if available
                verification = item.get('verification_status', 'unverified').capitalize()
                return f"[Src: {item['url']} | Cred: {item['credibility']:.2f} | Sent: {item['sentiment']} | {verification}]"
            else:
                logger.warning(f"[LLMNarrativeClient] Citation [{num}] not found in citation map")
                return match.group(0)  # Keep original if not found

        converted = re.sub(r'\[(\d+)\]', replace_citation, summary)
        citation_count = len(re.findall(r'\[\d+\]', summary))
        logger.info(f"[LLMNarrativeClient] Converted {citation_count} citation numbers to full format with verification status")

        return converted, insights

    async def _run_direct_generation(
        self,
        *,
        window: str,
        focus_areas: list[str],
        documents: list[dict[str, Any]],
        theme_insights: list[dict[str, Any]] | None = None,
        sentiment_distribution: dict[str, float] | None = None,
    ) -> tuple[str | None, list[dict[str, Any]]]:
        # Single-shot analysis without separate planning step for speed
        analysis_prompt = self._build_prompt(
            window=window,
            focus_areas=focus_areas,
            documents=documents,
            theme_insights=theme_insights,
            sentiment_distribution=sentiment_distribution,
        )

        try:
            import time
            start = time.perf_counter()
            raw_text = await self._model.generate(
                prompt=analysis_prompt,
                system_prompt="You are a senior analyst for Baguio City command center. Return VALID JSON only (no markdown, no code blocks).",
                temperature=0.2,
                max_tokens=8000,
            )
            elapsed = time.perf_counter() - start
            logger.info(f"[LLMNarrativeClient] Narrative generated in {elapsed:.1f}s")
        except asyncio.TimeoutError:
            logger.error("[LLMNarrativeClient] Narrative generation timed out after 60s")
            return None, []
        except Exception:  # pragma: no cover - network/SDK failures
            logger.exception("Groq analysis failed")
            return None, []

        parsed = self._try_parse_json(raw_text)
        if parsed is None:
            return sanitize_text(raw_text.strip()), []

        summary = sanitize_text(parsed.get("summary"))
        insights = self._sanitize_insights(parsed.get("insights") or [])
        return summary, insights

    def _build_prompt(
        self,
        *,
        window: str,
        focus_areas: list[str],
        documents: list[dict[str, Any]],
        theme_insights: list[dict[str, Any]] | None = None,
        sentiment_distribution: dict[str, float] | None = None,
    ) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"

        # Build theme insights section if available
        insights_block = ""
        theme_categories = set()
        if theme_insights:
            insight_lines = []
            for item in theme_insights:
                cat = sanitize_text(item.get('category', 'General'))
                theme_categories.add(cat)
                title = sanitize_text(item.get('title'))
                detail = sanitize_text(item.get('detail'))
                insight_lines.append(f"THEME [{cat}]: {title}\nDETAILS: {detail}")
            insights_block = "\n\n=== PRE-ANALYZED THEME INSIGHTS ===\n" + "\n\n".join(insight_lines)

        # Build documents section with domain tracking
        doc_lines = []
        available_domains = set()
        
        for idx, doc in enumerate(documents, start=1):
            title = sanitize_text(doc.get('title', ''))
            snippet = sanitize_text(doc.get('snippet', ''))[:200]
            sentiment = doc.get('sentiment', 'neutral')
            credibility = doc.get('metadata', {}).get('credibility_score', doc.get('credibility_score', 0.0))
            url = doc.get('url', '')
            
            # Extract and track domain from each document
            if url:
                domain = str(url).replace('https://', '').replace('http://', '').split('/')[0].replace('www.', '')
                available_domains.add(domain)
            
            doc_lines.append(f"{idx}. [{sentiment.upper()} | Cred:{credibility:.2f}] {title}: {snippet}")
        
        docs_block = "\n".join(doc_lines) or "No documents available."

        # GEOGRAPHIC GROUNDING: Extract non-Baguio locations from documents to build a negative filter
        # This prevents the LLM from attributing facts about other cities to Baguio
        PHILIPPINE_CITIES_EXCEPT_BAGUIO = [
            "Manila", "Quezon City", "Cebu", "Davao", "Makati", "Pasig", "Taguig",
            "Mandaluyong", "Pasay", "Caloocan", "Zamboanga", "Antipolo", "Cagayan de Oro",
            "Iloilo", "Bacolod", "General Santos", "Cabanatuan", "Lapu-Lapu", "Mandaue",
            "Parañaque", "Las Piñas", "Muntinlupa", "Marikina", "Valenzuela", "Malabon",
            "Navotas", "San Juan", "Pateros", "Taytay", "Cavite", "Laguna", "Batangas",
            "Angeles", "Olongapo", "Tarlac", "Dagupan", "San Fernando", "Vigan",
            "Laoag", "Tuguegarao", "Naga", "Legazpi", "Tacloban", "Butuan", "Iligan",
            "Cotabato", "Puerto Princesa", "Dumaguete", "Tagbilaran", "Bohol", "Siquijor",
            "Metro Manila", "NCR", "MM",
        ]
        wrong_location_mentions = []
        for doc in documents:
            title = (doc.get('title') or '').lower()
            snippet = (doc.get('snippet') or '').lower()
            for city in PHILIPPINE_CITIES_EXCEPT_BAGUIO:
                city_lower = city.lower()
                if city_lower in title or city_lower in snippet:
                    wrong_location_mentions.append(city)
                    break  # One match per doc is enough

        # Build geographic constraint instruction
        if wrong_location_mentions:
            unique_wrong_locations = sorted(set(wrong_location_mentions))
            geographic_constraint = (
                f"\n\n⚠️ CRITICAL: GEOGRAPHIC CONSTRAINT ⚠️\n"
                f"Your narrative MUST ONLY cover facts about BAGUIO CITY.\n"
                f"DO NOT include, mention, or attribute to Baguio any facts about these other locations:\n"
                f"  {', '.join(unique_wrong_locations)}\n"
                f"If a document mentions facts about these cities, IGNORE those facts entirely.\n"
                f"NEVER write sentences like 'Metro Manila crime rates rose...' — that is NOT about Baguio.\n"
                f"Every claim in your narrative must be specifically about Baguio City.\n"
            )
        else:
            geographic_constraint = (
                f"\n\n⚠️ CRITICAL: GEOGRAPHIC CONSTRAINT ⚠️\n"
                f"Your narrative MUST ONLY cover facts about BAGUIO CITY.\n"
                f"DO NOT include facts about other cities (Manila, Cebu, Davao, etc.) as if they were about Baguio.\n"
                f"Every claim must be specifically about Baguio City.\n"
            )

        # Build domain-to-URL mapping for citation grounding
        domain_mapping = {}
        for doc in documents:
            url = doc.get('url', '')
            if url:
                domain = str(url).replace('https://', '').replace('http://', '').split('/')[0].replace('www.', '')
                if domain not in domain_mapping:
                    domain_mapping[domain] = url

        # Build citation menu for LLM to choose from (Constrained Generation)
        citation_menu = []
        for idx, doc in enumerate(documents[:30], start=1):
            url = doc.get('url', '')
            if url:
                # Shorten URL for token efficiency (first 60 chars)
                url_short = str(url).replace('https://', '').replace('http://', '')
                if len(url_short) > 60:
                    url_short = url_short[:57] + '...'
                credibility = doc.get('metadata', {}).get('credibility_score', doc.get('credibility_score', 0.0))
                sentiment = doc.get('sentiment', 'neutral').capitalize()
                verification_status = doc.get('metadata', {}).get('tavily_verification_status', 'unverified')
                citation_menu.append({
                    'idx': idx,
                    'url': url_short,
                    'credibility': round(credibility, 2),
                    'sentiment': sentiment,
                    'verification_status': verification_status,
                })

        # Build citation menu block
        citation_menu_block = ""
        if citation_menu:
            menu_lines = ["=== AVAILABLE CITATIONS (Choose by number [1], [2], [3], etc.) ==="]
            for item in citation_menu:
                # Extract verification_status from document metadata
                doc_credibility = item.get('credibility', 0.0)
                doc_verification_status = item.get('verification_status', 'unverified')

                # Show RAW verification status (for CitationVerifier matching) + credibility label (for readability)
                raw_status = doc_verification_status  # "verified", "unverified", "contradicted"

                # Human-readable credibility label
                if doc_verification_status == 'verified':
                    status_label = "Verified"  # Tavily or VSEE confirmed
                elif doc_verification_status == 'contradicted':
                    status_label = "Contradicted"  # Actively disputed
                elif doc_credibility >= 0.75:
                    status_label = "High Credibility"  # Strong but unverified
                elif doc_credibility < 0.55:
                    status_label = "Low Credibility"  # Weak sourcing
                else:
                    status_label = "Unverified"  # Moderate sourcing

                # Show raw status FIRST (LLM must copy this for citation verification)
                menu_lines.append(
                    f"[{item['idx']}] {item['url']} | {raw_status} | Sent: {item['sentiment']}"
                )
            citation_menu_block = "\n".join(menu_lines) + "\n\n"

        # Create grounded domain list (limit to 25 for token efficiency)
        sorted_domains = sorted(available_domains)[:25]
        domains_block = "\n".join(f"  - {domain}" for domain in sorted_domains) if sorted_domains else "  (none)"

        # CRITICAL: Ground the LLM with actual available domains
        domains_instruction = f"""
⚠️ CRITICAL: CITATION DOMAIN RESTRICTION ⚠️
You MUST ONLY use domains from this EXACT list for citations:

AVAILABLE DOMAINS (FROM RETRIEVED DOCUMENTS):
{domains_block}

RULES (NON-NEGOTIABLE):
1. DO NOT invent domains. DO NOT use domains not in this list.
2. Match the domain EXACTLY as shown above (e.g., "pia.gov.ph" not "Philippine Information Agency").
3. Each claim MUST cite a domain from this list.
4. If you cannot cite a domain from this list, DO NOT make that claim.
5. DO NOT use publication names. Use ONLY domains (e.g., "mb.com.ph" not "Manila Bulletin").
6. COPY citation metadata from the "EXACT CITATION METADATA" section above.

EXAMPLES:
WRONG: [Src: manila bulletin | Cred: 0.74]  ← Publication name
WRONG: [Src: richestph.com | Cred: 0.51]  ← Not in available domains list
RIGHT: [Src: mb.com.ph | Cred: 0.74]  ← Domain from list above
RIGHT: [Src: pia.gov.ph | Cred: 0.95]  ← Domain from list above
""" if sorted_domains else ""

        # CRITICAL: Constrain narrative to ONLY the selected focus areas and generated themes
        theme_constraint = ""
        if theme_insights and theme_categories:
            theme_list = ", ".join(sorted(theme_categories))
            theme_constraint = (
                f"\n\n⚠️ CRITICAL CONSTRAINT ⚠️\n"
                f"You MUST ONLY discuss these themes: {theme_list}\n"
                f"DO NOT create new themes or discuss topics outside of: {focus}\n"
                f"DO NOT mention health, infrastructure, tourism, or other areas unless they are in the theme insights above.\n"
                f"Your narrative must STRICTLY follow the {len(theme_insights)} theme insights provided.\n"
            )

        # Build sentiment distribution context
        sentiment_context = ""
        if sentiment_distribution:
            neg_pct = int(sentiment_distribution.get("negative", 0) * 100)
            neu_pct = int(sentiment_distribution.get("neutral", 0) * 100)
            pos_pct = int(sentiment_distribution.get("positive", 0) * 100)
            sentiment_context = (
                f"\n\n=== SENTIMENT DISTRIBUTION ===\n"
                f"Negative: {neg_pct}% | Neutral: {neu_pct}% | Positive: {pos_pct}%\n"
                f"IMPORTANT: Your concluding paragraph MUST align with this distribution.\n"
                f"- If negative is 0%, DO NOT say 'negative developments' - say 'concerns' or 'challenges' instead\n"
                f"- If neutral is high (>70%), emphasize 'mixed' or 'balanced' sentiment\n"
                f"- Match the tone to the actual sentiment breakdown above\n"
            )

        # Build verification prioritization instruction
        verification_instruction = """
⚠️ CRITICAL: CITATION PRIORITIZATION ⚠️
When multiple sources support the same claim, PRIORITIZE in this order:

1. VERIFIED SOURCES: Choose these FIRST (verification_status: verified)
   - These are confirmed by Tavily web search OR VSEE internal consensus
   - VSEE verifies via: cross-reference ≥0.70 + domain trust ≥0.45
   - Look for: "verified" status in citation menu
   - Example: [3] pia.gov.ph | verified | Sent: Positive

2. HIGH CREDIBILITY: Choose if no verified sources available (Cred: ≥0.75)
   - These have strong domain trust + internal corroboration
   - They show "unverified" status but have high credibility scores
   - Example: [5] inquirer.net | unverified | Sent: Neutral (Cred: 0.78)

3. LOW CREDIBILITY: AVOID unless no alternative (Cred: <0.55)
   - These lack external confirmation or internal consensus
   - Example: [8] facebook.com | unverified | Sent: Positive (Cred: 0.42)

4. CONTRADICTED: DO NOT CITE unless explicitly noting dispute
   - These are actively disputed by fact-checkers
   - Example: [12] unknown.com | contradicted | Sent: Negative

RULES:
- ALWAYS prefer VERIFIED over unverified high-credibility sources
- AVOID LOW CREDIBILITY unless no other source supports the claim
- NEVER cite CONTRADICTED sources without noting the dispute
- When in doubt, choose sources with higher credibility scores
"""

        return (
            "You are a senior analyst supporting the Baguio City command center. "
            f"Summarize public chatter over the last {window} with emphasis on {focus}.\n\n"
            f"{citation_menu_block}"  # NEW: Citation menu for constrained generation
            f"{verification_instruction}"  # NEW: Verification prioritization
            f"{geographic_constraint}\n\n"  # NEW: Geographic constraint (epistemic authority)
            f"=== SUPPORTING CONVERSATIONS ({len(documents)} documents) ===\n"
            f"{docs_block}\n"
            f"{insights_block}"
            f"{theme_constraint}"
            f"{sentiment_context}"
            f"{domains_instruction}\n\n"
            "TASK:\n"
            "1. Analyze ALL supporting conversations above.\n"
            "2. Reference the theme insights for structured context.\n"
            "3. Generate a comprehensive, engaging narrative summary with IN-LINE CITATIONS.\n\n"
            "CITATION FORMAT (CRITICAL - MUST FOLLOW EXACTLY):\n"
            "- Each sentence MUST end with a full citation in this EXACT format:\n"
            "  [Src: domain.com | Sent: SENTIMENT | verification_status]\n"
            "- Example: Vendors received P10,000 assistance [Src: pia.gov.ph | Sent: Positive | verified].\n"
            "- Use the citation menu above to select sources - COPY the domain AND verification status EXACTLY as shown\n"
            "- CRITICAL: The verification status MUST be copied EXACTLY from the citation menu (verified/unverified/contradicted) - DO NOT translate or modify it\n"
            "- DO NOT use numbered citations like [1], [2], [3] - use FULL format ONLY\n"
            "- EVERY sentence MUST have exactly one citation. NO exceptions.\n"
            "- Each paragraph should have 2-4 citations minimum.\n"
            "- The conclusion paragraph MUST have at least 2 citations.\n"
            "- Prioritize sources with 'verified' status when multiple sources support a claim\n"
            "- Use sentiment from document metadata (Negative/Neutral/Positive)\n"
            "- Include verification status EXACTLY as shown in the menu: verified, unverified, or contradicted\n"
            "- Citations prove your claims are grounded in retrieved documents\n\n"
            "FORMATTING REQUIREMENTS:\n"
            "- Structure the summary into 6 well-developed paragraphs (2-3 sentences each)\n"
            "- Each paragraph should focus on ONE major theme/topic with depth and context\n"
            "- Start each paragraph with a BOLD topic indicator like: **Public Safety:** or **Infrastructure:**\n"
            "- Use vivid, descriptive language that brings the situation to life\n"
            "- Highlight key tensions, risks, and positive developments with specific details\n"
            "- Include contextual information about what this means for Baguio City\n"
            "- Add a concluding paragraph that ACCURATELY reflects the sentiment distribution above\n"
            "- COMPLETE ALL PARAGRAPHS - do not stop mid-sentence or mid-paragraph\n\n"
            "CRITICAL JSON FORMAT REQUIREMENTS:\n"
            "- Return VALID JSON only (no markdown, no code blocks, no backticks)\n"
            "- Use DOUBLE QUOTES for all string values (not backticks `, not single quotes ')\n"
            "- Escape special characters: use \\n for newlines, \\\" for quotes inside strings\n"
            "- The summary field MUST be a single JSON string with \\n\\n for paragraph breaks\n"
            "- DO NOT use template literals or backticks - they are invalid JSON\n\n"
            "Return a JSON object with keys:\n"
            '- summary: "string narrative with \\n\\n between paragraphs and [Src: ...] citations" (use double quotes!)\n'
            "- insights: list of up to 5 items, each {category, title, detail, evidence (array of source URLs)}\n\n"
            "Example CORRECT format:\n"
            '{"summary": "**Public Safety:** Traffic increased [Src: facebook.com | Sent: Negative | unverified].\\n\\n**Infrastructure:** Water shortage persists [Src: pia.gov.ph | Sent: Neutral | verified].", "insights": []}\n\n'
            "Example WRONG format (DO NOT USE):\n"
            "{'summary': `text with backticks`, 'insights': []}  <- INVALID!\n"
            '{"summary": "Traffic increased.", "insights": []}  <- MISSING CITATIONS!\n'
            '{"summary": "Traffic increased [1].", "insights": []}  <- NUMBERED CITATION (use full format)!\n'
        )

    def _build_agent_instruction(self, *, window: str, focus_areas: list[str]) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"
        num_focus_areas = len(focus_areas) if focus_areas else 1
        return (
            "Summarize public chatter for the Baguio City command center."
            f" Time window: {window}. Focus areas: {focus}."
            " Produce a JSON object with keys summary (3-5 sentences covering all major themes) and insights (array of up to 5 items)."
            " Each insight needs category, title, detail (comprehensive explanation), and optional evidence array with source URLs."
            f" IMPORTANT: Generate at least one insight for EACH focus area ({focus})."
            " Ensure balanced coverage - do not focus only on the most common topic."
            " Analyze ALL provided documents thoroughly and cite from the context block."
        )

    def _build_plan_prompt(self, *, window: str, focus_areas: list[str], documents: list[dict[str, Any]]) -> str:
        focus = ", ".join(focus_areas) if focus_areas else "general civic services"
        doc_sample = documents[:5]
        doc_summaries = "\n".join(
            f"- {sanitize_text(doc.get('title'))}: {sanitize_text(doc.get('snippet'))}" for doc in doc_sample
        ) or "- No documents available"

        return (
            "You are a senior analyst agent tasked with planning how to summarize civic chatter.\n"
            f"Time window: {window}. Focus areas: {focus}.\n"
            "Draft a numbered plan (3-5 steps) describing how you will interpret the documents, prioritize risks, and validate sources.\n"
            "End with 'Plan ready.'\n"
            "Recent documents:\n"
            f"{doc_summaries}\n"
        )

    @staticmethod
    def _try_parse_json(raw_text: str) -> dict[str, Any] | None:
        """Extract and parse JSON from LLM response with robust recovery."""
        if not raw_text:
            return None
            
        text = sanitize_text(raw_text).strip()
        
        # Strategy 1: Markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if json_match:
            candidate = json_match.group(1).strip()
            result = LLMNarrativeClient._safe_json_parse(candidate)
            if result:
                return result
            text = candidate
        
        # Strategy 2: Outermost braces
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx : end_idx + 1]

        # Strategy 3: Direct parse with cleaning
        result = LLMNarrativeClient._safe_json_parse(text)
        if result:
            return result
        
        # Strategy 4: Extract summary and insights separately using regex
        # This handles cases where JSON is malformed but content is extractable
        logger.info("[LLMNarrativeClient] Attempting regex extraction fallback...")
        
        summary_match = re.search(r'"summary"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', text, re.DOTALL)
        summary = summary_match.group(1) if summary_match else None
        
        if summary:
            # Unescape the summary
            summary = summary.replace('\\"', '"').replace('\\n', '\n')
            logger.info(f"[LLMNarrativeClient] Extracted summary via regex ({len(summary)} chars)")
            return {"summary": summary, "insights": []}
        
        logger.warning(f"[LLMNarrativeClient] JSON parse failed. Text: {text[:200]}...")
        return None
    
    @staticmethod
    def _safe_json_parse(text: str) -> dict[str, Any] | None:
        """Try multiple JSON parsing strategies."""
        # Attempt 1: Fix backticks (common LLM error - using template literals instead of JSON strings)
        if '`' in text:
            logger.debug("[LLMNarrativeClient] Detected backticks, converting to JSON strings...")
            # Replace backtick strings with proper JSON strings
            # Pattern: "key": `value` or 'key': `value`
            text = re.sub(r'(["\']summary["\']\s*:\s*)`([^`]*)`', r'\1"\2"', text, flags=re.DOTALL)
            text = re.sub(r'(["\']insights["\']\s*:\s*)`([^`]*)`', r'\1"\2"', text, flags=re.DOTALL)
            # Also handle any remaining backticks
            text = text.replace('`', '"')
        
        # Attempt 2: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Attempt 3: Remove trailing commas
        try:
            cleaned = re.sub(r',\s*([}\]])', r'\1', text)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Attempt 4: Fix common issues
        try:
            # Replace single quotes with double quotes (common LLM issue)
            fixed = text.replace("'", '"')
            # Remove any control characters
            fixed = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', fixed)
            # Fix unescaped newlines in strings
            fixed = re.sub(r'(?<!\\)\n', '\\n', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
        
        # Attempt 5: Truncate at last valid closing brace
        try:
            # Find balanced braces
            depth = 0
            last_valid_end = -1
            for i, char in enumerate(text):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        last_valid_end = i
                        break
            
            if last_valid_end > 0:
                truncated = text[:last_valid_end + 1]
                return json.loads(truncated)
        except json.JSONDecodeError:
            pass
        
        return None


# Global singleton instance
llm_narrative_client = LLMNarrativeClient()

# Backward compatibility alias (deprecated - use llm_narrative_client instead)
gemini_client = llm_narrative_client
