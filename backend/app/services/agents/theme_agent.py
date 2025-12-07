"""Direct Gemini client for theme-specific insights - no ReAct overhead."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import google.generativeai as genai

from ...core.config import get_settings

logger = logging.getLogger(__name__)


def sanitize_text(text: Any) -> str:
    """Remove invalid Unicode characters (surrogates) that break Gemini API.
    
    Handles HttpUrl, strings, and other types by converting to string first.
    """
    if not text:
        return ""
    # Convert to string first (handles HttpUrl, int, etc.)
    text_str = str(text)
    # Remove surrogate characters (U+D800 to U+DFFF)
    cleaned = re.sub(r'[\ud800-\udfff]', '', text_str)
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
    cleaned = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]', '', cleaned)
    return cleaned.strip()


def run_theme_agent(
    theme_label: str,
    prompt: str,
    documents: list[dict[str, Any]],
) -> str:
    """Generate theme insight using direct Gemini call (no ReAct)."""
    
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY missing")
    
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Build context with sanitized text - INCLUDE URLs for evidence
    doc_lines = []
    for doc in documents[:5]:
        title = sanitize_text(doc.get('title', 'Untitled'))
        snippet = sanitize_text(doc.get('snippet', ''))[:200]
        url = sanitize_text(doc.get('url', ''))
        if url:
            doc_lines.append(f"- [{title}]({url}): {snippet}")
        else:
            doc_lines.append(f"- {title}: {snippet}")
    context_block = "\n".join(doc_lines)
    
    # Theme-specific focus
    theme_focus = {
        "Health & Wellness": "Focus ONLY on health topics (diseases, hospitals, medical services, sanitation). Ignore other topics.",
        "Public Safety": "Focus ONLY on safety topics (crime, police, fire, emergencies). Ignore other topics.",
        "Infrastructure": "Focus ONLY on infrastructure (roads, traffic, water, power, buildings). Ignore other topics.",
        "Environment": "Focus ONLY on environment (pollution, waste, flooding, climate). Ignore other topics.",
        "Tourism & Events": "Focus ONLY on tourism/events (visitors, hotels, festivals). Ignore other topics.",
        "Business & Economy": "Focus ONLY on economy (business, markets, revenue, employment). Ignore other topics.",
    }
    
    focus = theme_focus.get(theme_label, f"Focus on {theme_label} aspects only.")
    
    # Build prompt
    full_prompt = f"""You are a civic analyst for Baguio City.

Theme: {theme_label}
{focus}

Task: Analyze the documents below and create a JSON response.

Documents:
{context_block}

Return ONLY valid JSON with this exact structure:
{{
  "title": "Concise insight title",
  "detail": "Actionable detail under 240 characters",
  "evidence": ["actual_url_from_documents_above"]
}}

IMPORTANT: The "evidence" array MUST contain the actual URLs from the documents above (the URLs in parentheses after titles). Do NOT use placeholder text like "URL1" - use the real URLs.

If documents lack {theme_label} content, return: {{"title": "No {theme_label} Data", "detail": "Documents don't contain relevant {theme_label} information.", "evidence": []}}

JSON:"""
    
    logger.info(f"[Direct Gemini] Starting for '{theme_label}'")
    
    try:
        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=500,
            )
        )
        
        # Sanitize output to remove surrogates that break JSON serialization
        output = sanitize_text(response.text)
        logger.info(f"[Direct Gemini] Completed for '{theme_label}'")
        
        # Validate JSON
        try:
            parsed = json.loads(output)
            # Handle case where Gemini returns a list instead of dict
            if isinstance(parsed, list) and len(parsed) > 0:
                parsed = parsed[0]  # Take first item
            if not isinstance(parsed, dict):
                raise ValueError(f"Expected dict, got {type(parsed)}")
            # Sanitize all string fields in the parsed JSON
            sanitized = {
                "title": sanitize_text(parsed.get("title", "")),
                "detail": sanitize_text(parsed.get("detail", "")),
                "evidence": [sanitize_text(str(e)) for e in parsed.get("evidence", []) if e],
            }
            return json.dumps(sanitized)
        except (json.JSONDecodeError, ValueError):
            # Extract JSON if wrapped in markdown
            if "```json" in output:
                output = output.split("```json")[1].split("```")[0].strip()
            elif "```" in output:
                output = output.split("```")[1].split("```")[0].strip()
            # Try parsing again after extraction
            try:
                parsed = json.loads(output)
                # Handle list case again
                if isinstance(parsed, list) and len(parsed) > 0:
                    parsed = parsed[0]
                if not isinstance(parsed, dict):
                    raise ValueError(f"Expected dict, got {type(parsed)}")
                sanitized = {
                    "title": sanitize_text(parsed.get("title", "")),
                    "detail": sanitize_text(parsed.get("detail", "")),
                    "evidence": [sanitize_text(str(e)) for e in parsed.get("evidence", []) if e],
                }
                return json.dumps(sanitized)
            except (json.JSONDecodeError, ValueError):
                return output
            
    except Exception as e:
        logger.error(f"[Direct Gemini] Failed for '{theme_label}': {e}")
        return json.dumps({
            "title": f"Error in {theme_label}",
            "detail": "Failed to generate insight due to technical error.",
            "evidence": []
        })
