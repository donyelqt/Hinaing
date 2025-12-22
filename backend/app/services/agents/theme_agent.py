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
    # OPTIMIZATION: Use Flash for theme agents (much faster, sufficient quality for summaries)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Build context with sanitized text - INCLUDE URLs for evidence
    # OPTIMIZATION: Show more documents (15 instead of 5) for better insight diversity
    doc_lines = []
    for doc in documents[:15]:
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
    
    # Build prompt - Request EXACTLY 3 insights per theme
    full_prompt = f"""You are a civic analyst for Baguio City.

Theme: {theme_label}
{focus}

Task: Analyze the documents below and generate EXACTLY 3 DISTINCT insights.

Documents ({len(documents[:15])} shown):
{context_block}

CRITICAL REQUIREMENTS:
1. Generate EXACTLY 3 insights (no more, no less)
2. Each insight must address a DIFFERENT issue or sub-topic
3. DO NOT merge unrelated problems into one insight
4. Each insight should be actionable and specific
5. Prioritize the most important/urgent issues first

Examples of DISTINCT insights for Infrastructure:
✅ GOOD:
  - Insight 1: "Traffic congestion on Kennon Road"
  - Insight 2: "Water supply interruptions in District 3"
  - Insight 3: "Parking shortage in CBD area"

❌ BAD:
  - Insight 1: "Infrastructure challenges including traffic, water, and parking" (too broad, merged)

Return ONLY valid JSON with this exact structure:
{{
  "insights": [
    {{
      "title": "First specific issue title",
      "detail": "Actionable detail under 240 characters",
      "evidence": ["actual_url_from_documents_above"]
    }},
    {{
      "title": "Second distinct issue title",
      "detail": "Actionable detail under 240 characters",
      "evidence": ["actual_url_from_documents_above"]
    }},
    {{
      "title": "Third different issue title",
      "detail": "Actionable detail under 240 characters",
      "evidence": ["actual_url_from_documents_above"]
    }}
  ]
}}

IMPORTANT:
- The "evidence" array MUST contain actual URLs from the documents above
- If documents truly lack {theme_label} content, return: {{"insights": []}}
- Generate EXACTLY 3 insights if you have sufficient content

JSON:"""
    
    logger.info(f"[Direct Gemini] Starting for '{theme_label}'")
    
    # Disable safety filters for civic news analysis
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    try:
        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=4000,  # Increased from 3000 to handle multiple insights with 15 docs
            ),
            safety_settings=safety_settings,
        )
        
        # Check if response is valid
        if not response.candidates:
            logger.warning(f"[Direct Gemini] No candidates returned for '{theme_label}'. Feedback: {response.prompt_feedback}")
            return json.dumps({
                "insights": [{
                    "title": f"No Data for {theme_label}",
                    "detail": "AI model returned no response.",
                    "evidence": []
                }]
            })

        candidate = response.candidates[0]
        if candidate.finish_reason != 1:  # 1 = STOP
            reason_map = {1: "STOP", 2: "MAX_TOKENS", 3: "SAFETY", 4: "RECITATION", 5: "OTHER"}
            reason_str = reason_map.get(candidate.finish_reason, f"UNKNOWN({candidate.finish_reason})")
            logger.warning(f"[Direct Gemini] Finish reason: {candidate.finish_reason} ({reason_str}) for '{theme_label}'. Safety: {candidate.safety_ratings}")
            
            # If blocked or truncated with no content
            if not candidate.content.parts:
                return json.dumps({
                    "insights": [{
                        "title": f"Generation Failed ({reason_str})",
                        "detail": f"Model stopped due to {reason_str}. Try reducing document count or simplifying prompt.",
                        "evidence": []
                    }]
                })
            
            # If MAX_TOKENS but we have partial content, try to parse it
            if candidate.finish_reason == 2:  # MAX_TOKENS
                logger.warning(f"[Direct Gemini] MAX_TOKENS hit for '{theme_label}'. Attempting to parse partial response...")
                # Continue to try parsing the partial response below

        # Safe access to text
        try:
            output = sanitize_text(response.text)
        except Exception as exc:
            logger.warning(f"[Direct Gemini] Failed to access text: {exc}. Parts: {candidate.content.parts}")
            return json.dumps({
                "insights": [{
                    "title": f"Processing Error ({theme_label})",
                    "detail": "Failed to parse AI response.",
                    "evidence": []
                }]
            })
        
        # CRITICAL: Remove markdown code blocks BEFORE parsing
        # Gemini often wraps JSON in ```json ... ```
        if "```json" in output:
            # Extract content between ```json and ```
            parts = output.split("```json")
            if len(parts) > 1:
                json_part = parts[1].split("```")[0].strip()
                output = json_part
                logger.debug(f"[Direct Gemini] Extracted JSON from markdown for '{theme_label}'")
        elif "```" in output:
            # Generic code block
            parts = output.split("```")
            if len(parts) >= 3:
                output = parts[1].strip()
                logger.debug(f"[Direct Gemini] Extracted from generic code block for '{theme_label}'")

        logger.info(f"[Direct Gemini] Completed for '{theme_label}'")
        
        # Validate JSON
        try:
            parsed = json.loads(output)
            
            # Handle different response formats
            insights_list = []
            
            if isinstance(parsed, dict):
                if "insights" in parsed and isinstance(parsed["insights"], list):
                    # New format: {"insights": [...]}
                    insights_list = parsed["insights"]
                elif "title" in parsed:
                    # Old format: single insight object
                    insights_list = [parsed]
            elif isinstance(parsed, list):
                # Direct list of insights
                insights_list = parsed
            
            # Sanitize all insights
            sanitized_insights = []
            for item in insights_list:
                if isinstance(item, dict):
                    sanitized_insights.append({
                        "title": sanitize_text(item.get("title", "")),
                        "detail": sanitize_text(item.get("detail", "")),
                        "evidence": [sanitize_text(str(e)) for e in item.get("evidence", []) if e],
                    })
            
            # Return as {"insights": [...]} format for consistency
            return json.dumps({"insights": sanitized_insights})
            
        except (json.JSONDecodeError, ValueError) as json_err:
            logger.warning(f"[Direct Gemini] JSON parse failed for '{theme_label}': {output[:100]}")
            
            # Try to repair truncated JSON (common with MAX_TOKENS)
            if '"insights"' in output and output.count('[') > output.count(']'):
                # Truncated array - try to close it
                repaired = output.rstrip() + ']}}'
                try:
                    parsed = json.loads(repaired)
                    if "insights" in parsed and isinstance(parsed["insights"], list):
                        sanitized_insights = []
                        for item in parsed["insights"]:
                            if isinstance(item, dict) and "title" in item:
                                sanitized_insights.append({
                                    "title": sanitize_text(item.get("title", "")),
                                    "detail": sanitize_text(item.get("detail", "")),
                                    "evidence": [sanitize_text(str(e)) for e in item.get("evidence", []) if e],
                                })
                        if sanitized_insights:
                            logger.info(f"[Direct Gemini] Repaired truncated JSON for '{theme_label}', recovered {len(sanitized_insights)} insights")
                            return json.dumps({"insights": sanitized_insights})
                except:
                    pass
            
            # Extract JSON if wrapped in markdown
            if "```json" in output:
                output = output.split("```json")[1].split("```")[0].strip()
            elif "```" in output:
                output = output.split("```")[1].split("```")[0].strip()
            # Try parsing again after extraction
            try:
                parsed = json.loads(output)
                
                # Handle different formats again
                insights_list = []
                if isinstance(parsed, dict):
                    if "insights" in parsed and isinstance(parsed["insights"], list):
                        insights_list = parsed["insights"]
                    elif "title" in parsed:
                        insights_list = [parsed]
                elif isinstance(parsed, list):
                    insights_list = parsed
                
                sanitized_insights = []
                for item in insights_list:
                    if isinstance(item, dict):
                        sanitized_insights.append({
                            "title": sanitize_text(item.get("title", "")),
                            "detail": sanitize_text(item.get("detail", "")),
                            "evidence": [sanitize_text(str(e)) for e in item.get("evidence", []) if e],
                        })
                
                return json.dumps({"insights": sanitized_insights})
                
            except (json.JSONDecodeError, ValueError):
                logger.warning(f"[Direct Gemini] JSON parse failed for '{theme_label}': {output[:100]}")
                return json.dumps({
                    "insights": [{
                        "title": f"Analysis for {theme_label}",
                        "detail": output[:500],
                        "evidence": []
                    }]
                })
            
    except Exception as e:
        logger.exception(f"[Direct Gemini] Unexpected error for '{theme_label}': {e}")
        return json.dumps({
            "insights": [{
                "title": f"Error in {theme_label}",
                "detail": "Failed to generate insight due to technical error.",
                "evidence": []
            }]
        })
