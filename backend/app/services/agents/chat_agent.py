"""Conversational agent for civic insights using LangSearch."""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ...core.config import get_settings
from ..langsearch import LangSearchClient
from ..agents.context_agent import ContextAugmentationAgent

logger = logging.getLogger(__name__)


def search_civic_data(query: str):
    """Search for real-time civic information in Baguio City."""
    pass


def search_sentiment_data(query: str, sentiment_filter: str = None):
    """Search for sentiment analysis data from previous analyses.
    
    Args:
        query: Topic to search sentiment for (e.g., "tourism", "infrastructure")
        sentiment_filter: Optional filter - "positive", "negative", or "neutral"
    """
    pass


# Define tools map for Gemini (schema only)
tools_map = {
    'search_civic_data': search_civic_data,
    'search_sentiment_data': search_sentiment_data
}


def _is_sentiment_query(message: str) -> bool:
    """Detect if user is asking about sentiment/opinion data."""
    sentiment_keywords = [
        "sentiment", "opinion", "feel", "feeling", "mood", "perception",
        "think about", "view on", "attitude", "reaction", "response to",
        "positive", "negative", "what do people", "how do citizens",
        "public opinion", "community sentiment", "latest sentiment"
    ]
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in sentiment_keywords)


async def run_chat_agent(
    message: str,
    history: Optional[List[dict]] = None,
    jurisdiction: str = "Baguio City",
    system_instruction: str | None = None
) -> Tuple[str, List[dict]]:
    """Run the conversational loop with Hybrid Retrieval (Web + Memory)."""
    settings = get_settings()
    if not settings.gemini_api_key:
        return "Error: Gemini API key missing.", []

    genai.configure(api_key=settings.gemini_api_key)
    
    # Default system instruction if none provided
    if system_instruction is None:
        system_instruction = (
            "You are **Hinaing's Conversational Assistant**. "
            "Role: You are a specialized Fast Response Unit for civic Q&A. "
            "Architecture: You are the **Agentic RAG Control Group**. You are distinct from the deep 7-node 'Sense-Making' architecture. "
            "Mandate: "
            "1. **Greetings & Small Talk:** Do NOT search. For 'hello', 'hi', 'hey', 'thanks', 'bye', etc., respond naturally without calling any tools. "
            "2. **Civic Questions:** Use `search_civic_data` for substantive civic questions about Baguio (crimes, disasters, infrastructure, events, policies, etc.). "
            "3. **Sentiment Questions:** Use `search_sentiment_data` when users ask about public opinion, sentiment, how people feel, or mood about a topic. This searches previously analyzed sentiment data. "
            "4. **Identity Questions:** Do NOT search. State clearly: 'I am an **Agentic RAG system** (ReAct Loop).' Explain that the 'Analysis' feature of Hinaing is a **separate Multi-Agent System (7-Node and 18 Agents)** which you can discuss but are not part of. "
            "5. Don't guess. Use tools only for factual civic queries or sentiment lookups. "
            "6. **Prioritize Recent Info:** When presenting search results, prioritize and highlight the MOST RECENT information. Note publication dates when available. "
            "7. **Be Helpful:** If the exact answer isn't found, share RELATED information that might be useful. Don't just say 'no results' - explain what WAS found and how it relates to the question."
        )

    # Use Flash for conversational speed
    # Include sentiment tool if query seems sentiment-related
    tools = [search_civic_data]
    if _is_sentiment_query(message):
        tools.append(search_sentiment_data)
    
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        tools=tools,
        system_instruction=system_instruction
    )
    
    # Build history for Gemini
    chat_history = []
    if history:
        for msg in history:
            role = "user" if msg.role == "user" else "model"
            chat_history.append({"role": role, "parts": [msg.content]})

    # Start chat session
    chat = model.start_chat(history=chat_history)
    
    # Initialize Context Agent for Memory Recall
    context_agent = ContextAugmentationAgent()
    
    # Send message
    try:
        response = await chat.send_message_async(
            f"Context: Jurisdiction is {jurisdiction}. User asks: {message}\n"
            f"Please structure your answer clearly. "
            f"Use **bolding** for key terms, lists for concerns, and short paragraphs.",
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        sources = []
        final_text = ""
        
        async def handle_tool_call(part) -> str | None:
            fn = part.function_call
            if not fn:
                return None
                
            fn_name = fn.name
            fn_args = dict(fn.args)
            
            # Handle sentiment-specific search
            if fn_name == 'search_sentiment_data':
                query = fn_args.get('query', '')
                sentiment_filter = fn_args.get('sentiment_filter')
                logger.info(f"[ChatAgent] invoking Sentiment Search for: {query} (filter={sentiment_filter})")
                
                try:
                    docs, stats = await context_agent.search_with_sentiment(
                        query=query,
                        limit=15,
                        sentiment_filter=sentiment_filter
                    )
                    
                    if not docs:
                        return f"No sentiment data found for '{query}'. Try running a full analysis first."
                    
                    # Format results with sentiment breakdown
                    output_lines = [
                        f"📊 **Sentiment Analysis Results for '{query}'**",
                        f"Total documents analyzed: {stats['total']}",
                        f"- 🟢 Positive: {stats['positive']} ({stats['positive_pct']}%)",
                        f"- 🔴 Negative: {stats['negative']} ({stats['negative_pct']}%)",
                        f"- ⚪ Neutral: {stats['neutral']} ({stats['neutral_pct']}%)",
                        "",
                        "**Key Sources:**"
                    ]
                    
                    for doc in docs[:10]:
                        sentiment_emoji = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(doc.sentiment, "")
                        title = doc.title[:60] + "..." if len(doc.title) > 60 else doc.title
                        output_lines.append(f"{sentiment_emoji} [{title}]({doc.url})")
                        if doc.snippet:
                            output_lines.append(f"   > {doc.snippet[:150]}...")
                        
                        # Collect for UI
                        sources.append({
                            "title": str(doc.title),
                            "url": str(doc.url) if doc.url else None,
                            "type": "SENTIMENT",
                            "sentiment": doc.sentiment
                        })
                    
                    return "\n".join(output_lines)
                    
                except Exception as e:
                    logger.exception(f"Sentiment search failed: {e}")
                    return f"Sentiment search error: {str(e)}"
            
            if fn_name == 'search_civic_data':
                query = fn_args.get('query', '')
                logger.info(f"[ChatAgent] invoking Hybrid Search for: {query}")
                
                try:
                    # Parallel Execution: 1. Web Search (Fresh) 2. Memory Recall (History)
                    search_client = LangSearchClient()
                    
                    # Only add jurisdiction if not already in query
                    query_lower = query.lower()
                    if "baguio" not in query_lower:
                        fresh_query = f"{query} {jurisdiction}"
                    else:
                        fresh_query = query  # Query already has location context
                    
                    # Create tasks - use freshness filter for recent results
                    # Try last month first, fallback to no filter if empty
                    web_task = search_client.search(
                        query=fresh_query,
                        time_window="30d",  # Last month for fresh results
                        limit=20
                    )
                    memory_task = context_agent.retrieve_knowledge(
                        focus_areas=[query],
                        limit=10
                    )
                    
                    # Run both
                    web_docs, memory_docs = await asyncio.gather(web_task, memory_task, return_exceptions=True)
                    
                    # Handle exceptions gracefully
                    if isinstance(web_docs, Exception):
                        logger.error(f"Web search failed: {web_docs}")
                        web_docs = []
                    if isinstance(memory_docs, Exception):
                        logger.error(f"Memory recall failed: {memory_docs}")
                        memory_docs = []
                    
                    # Fallback: If no recent results, try without time filter
                    if not web_docs:
                        logger.info("[ChatAgent] No recent results (30d), trying without time filter")
                        try:
                            web_docs = await search_client.search(
                                query=fresh_query,
                                time_window=None,
                                limit=20
                            )
                        except Exception as e:
                            logger.error(f"Fallback search failed: {e}")
                            web_docs = []
                        
                    logger.info(f"[ChatAgent] Found {len(web_docs)} web docs and {len(memory_docs)} memory docs")

                    # Filter to only recent results (last 6 months)
                    # LangSearch API doesn't strictly enforce freshness, so we filter client-side
                    six_months_ago = datetime.now() - timedelta(days=180)
                    fresh_web_docs = [
                        doc for doc in web_docs 
                        if doc.published_at and doc.published_at > six_months_ago
                    ]
                    
                    # If we have fresh results, use them; otherwise use all (sorted by date)
                    if fresh_web_docs:
                        logger.info(f"[ChatAgent] Filtered to {len(fresh_web_docs)} fresh docs (last 6 months)")
                        web_docs_to_use = fresh_web_docs
                    else:
                        logger.info("[ChatAgent] No fresh docs found, using all results sorted by date")
                        web_docs_to_use = web_docs

                    # Sort by date (most recent first)
                    web_docs_sorted = sorted(
                        web_docs_to_use,
                        key=lambda d: d.published_at or datetime.min,
                        reverse=True
                    )
                    
                    # Combine and Deduplicate
                    combined_docs = []
                    seen_urls = set()
                    
                    # Add Web Docs first (sorted by recency)
                    for doc in web_docs_sorted:
                        if doc.url and doc.url not in seen_urls:
                            doc.metadata = doc.metadata or {}
                            doc.metadata["source_type"] = "WEB"
                            combined_docs.append(doc)
                            seen_urls.add(doc.url)
                            
                    # Add MEMORY Docs (filter by relevance score to avoid irrelevant citations)
                    MEMORY_RELEVANCE_THRESHOLD = 0.45  # Filter out low-quality matches
                    for doc in memory_docs:
                        if doc.url and doc.url not in seen_urls:
                            # Check relevance score from RAG
                            score = doc.metadata.get("_score", 0) if doc.metadata else 0
                            if score < MEMORY_RELEVANCE_THRESHOLD:
                                logger.debug(f"[ChatAgent] Skipping low-relevance memory doc (score={score:.3f}): {doc.title}")
                                continue
                            doc.metadata = doc.metadata or {}
                            doc.metadata["source_type"] = "MEMORY"
                            combined_docs.append(doc)
                            seen_urls.add(doc.url)
                            
                    if not combined_docs:
                        return "No relevant results found in web or memory."
                        
                    # Format for LLM - include dates for recency awareness
                    formatted_output = []
                    for doc in combined_docs[:15]:  # Limit context window
                        title = doc.title or "Untitled"
                        snippet = doc.snippet or ""
                        url = str(doc.url) if doc.url else "No URL"
                        src_type = doc.metadata.get("source_type", "WEB")
                        
                        # Include publication date if available
                        date_str = ""
                        if doc.published_at:
                            date_str = f" (Published: {doc.published_at.strftime('%Y-%m-%d')})"
                        
                        formatted_output.append(f"[{src_type}]{date_str} Source: {title}\nURL: {url}\nSnippet: {snippet}\n")
                        
                        # Collect for UI with date
                        sources.append({
                            "title": str(title), 
                            "url": str(url) if url else None, 
                            "type": src_type,
                            "date": doc.published_at.isoformat() if doc.published_at else None
                        })
                        
                    return "\n".join(formatted_output)
                    
                except Exception as e:
                    logger.exception(f"Hybrid Search failed: {e}")
                    return f"Search error: {str(e)}"
            
            return None

        # Iterate parts of the response
        function_response_parts = []
        for part in response.parts:
            if part.function_call:
                res = await handle_tool_call(part)
                if res:
                    function_response_parts.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=part.function_call.name,
                                response={'result': res}
                            )
                        )
                    )

        if function_response_parts:
            # Send tool outputs back to model
            final_resp = await chat.send_message_async(
                function_response_parts
            )
            final_text = final_resp.text
        else:
            final_text = response.text

        return final_text, sources

    except Exception as e:
        logger.exception("Chat agent error")
        return f"I encountered an error: {str(e)}", []
