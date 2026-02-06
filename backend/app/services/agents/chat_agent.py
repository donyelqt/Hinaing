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
    history: Optional[List[Any]] = None,  # Accepts both ChatMessage objects and dicts
    jurisdiction: str = "Baguio City",
    system_instruction: str | None = None
) -> Tuple[str, List[dict]]:
    """Run the conversational loop with Hybrid Retrieval (Web + Memory) using Groq."""
    settings = get_settings()
    if not settings.groq_api_key:
        return "Error: Groq API key missing.", []

    # Use groq/compound for accurate, grounded chat responses (UNLIMITED TPD, 70K TPM)
    # Prevents hallucination by better following RAG instructions
    from ..llm.groq_provider import get_groq_provider
    llm = get_groq_provider("groq/compound")
    
    # Default system instruction if none provided
    if system_instruction is None:
        system_instruction = (
            "You are **Hinaing** (Hinaing Chat Assistant) - an Agentic RAG system developed by the University of the Cordilleras (UC) Computer Science R&D Team: "
            "Doniele Arys Antonio (Research Developer), Krisha May Cutiam (Researcher), and Justine May Macario (Researcher). "
            "DO NOT call yourself 'Compound' or 'Groq' - those are just your underlying infrastructure. Your product name is 'Hinaing'. "
            "Role: You are a specialized Fast Response Unit for civic Q&A about Baguio City. "
            "Architecture: You are the **Agentic RAG Control Group**. You are distinct from the deep 7-node 'Sense-Making' architecture. "
            "\n"
            "CRITICAL RULES - NO HALLUCINATION:\n"
            "1. **ONLY use information from search results** - NEVER make up schools, partnerships, dates, or events\n"
            "2. **If search returns no results** - Say 'I couldn't find specific information about [topic]' - DO NOT invent data\n"
            "3. **Cite sources** - Always reference where information came from (search results)\n"
            "4. **Be honest about limitations** - If you don't know, say so\n"
            "\n"
            "Mandate: "
            "1. **Greetings & Small Talk:** Do NOT search. For 'hello', 'hi', 'hey', 'thanks', 'bye', etc., respond naturally without calling any tools. "
            "2. **Civic Questions:** Use `search_civic_data` for substantive civic questions about Baguio (crimes, disasters, infrastructure, events, policies, etc.). "
            "3. **Sentiment Questions:** Use `search_sentiment_data` when users ask about public opinion, sentiment, how people feel, or mood about a topic. This searches previously analyzed sentiment data. "
            "4. **Identity Questions:** Do NOT search. State clearly: 'I am Hinaing, an Agentic RAG system developed by the UC Computer Science R&D Team.' Explain that the 'Analysis' feature of Hinaing is a **separate Multi-Agent System (7-Node and 18 Agents)** which you can discuss but are not part of. "
            "5. Don't guess. Use tools only for factual civic queries or sentiment lookups. "
            "6. **Prioritize Recent Info:** When presenting search results, prioritize and highlight the MOST RECENT information. Note publication dates when available. "
            "7. **Be Helpful:** If the exact answer isn't found, share RELATED information that might be useful. Don't just say 'no results' - explain what WAS found and how it relates to the question."
        )

    # Initialize Context Agent for Memory Recall
    context_agent = ContextAugmentationAgent()
    
    # Build conversation history context if provided
    history_context = ""
    if history and len(history) > 0:
        # Include last 3 exchanges for context
        recent_history = history[-6:]  # Last 3 Q&A pairs (6 messages)
        history_lines = []
        for msg in recent_history:
            # Handle both dict and Pydantic model
            if hasattr(msg, 'role'):
                # Pydantic model
                role = msg.role
                content = msg.content
            else:
                # Dict
                role = msg.get("role", "user")
                content = msg.get("content", "")
            
            if role == "user":
                history_lines.append(f"User: {content}")
            elif role == "assistant":
                history_lines.append(f"Assistant: {content}")
        
        if history_lines:
            history_context = "\n\nConversation History:\n" + "\n".join(history_lines) + "\n"
    
    # Build conversation prompt
    conversation_prompt = f"""Context: Jurisdiction is {jurisdiction}. User asks: {message}
{history_context}
Please structure your answer clearly. Use **bolding** for key terms, lists for concerns, and short paragraphs.

If you need to search for information, indicate what you're searching for."""

    sources = []
    
    try:
        # Detect if this is a greeting/small talk (skip search)
        message_lower = message.lower().strip()
        
        # Very short acknowledgments (1-3 words, no question marks)
        is_acknowledgment = (
            len(message.split()) <= 3 and 
            "?" not in message and
            any(ack in message_lower for ack in [
                "ok", "okay", "sure", "yes", "no", "yep", "nope", "alright", "got it",
                "i see", "understood", "cool", "nice", "great", "awesome", "perfect"
            ])
        )
        
        # Standard greetings (English + Tagalog/Filipino)
        is_greeting = any(greeting in message_lower for greeting in [
            # English
            "hello", "hi", "hey", "thanks", "thank you", "bye", "goodbye", 
            "good morning", "good afternoon", "good evening",
            # Tagalog/Filipino
            "kamusta", "kumusta", "musta", "salamat", "maraming salamat",
            "paalam", "magandang umaga", "magandang hapon", "magandang gabi"
        ])
        
        # Detect identity/meta questions about the system (skip search)
        is_identity_question = any(pattern in message_lower for pattern in [
            "who are you", "what are you", "who made you", "who created you", "who built you",
            "who developed you", "i am the developer", "i'm the developer", "i made you",
            "what is hinaing", "what's hinaing", "tell me about yourself", "introduce yourself",
            "what can you do", "what do you do", "how do you work", "explain yourself"
        ])
        
        if is_acknowledgment or is_greeting or is_identity_question:
            # Handle acknowledgments, greetings, and identity questions without search
            if is_acknowledgment:
                system_prompt = "You are a friendly civic assistant. Respond to acknowledgments naturally and briefly (6-7 sentences max)."
            elif is_identity_question:
                system_prompt = (
                    "You are **Hinaing**, an Agentic RAG system developed by the University of the Cordilleras (UC) Computer Science R&D Team. "
                    "DO NOT call yourself 'Compound' - that's just your underlying model. Your product name is 'Hinaing'. "
                    "\n\n"
                    "R&D Team Members:\n"
                    "- Doniele Arys Antonio (Research Developer)\n"
                    "- Krisha May Cutiam (Researcher)\n"
                    "- Justine Mae Macario (Researcher)\n"
                    "\n"
                    "When introducing yourself, you MUST mention these key points:\n"
                    "1. Your name: 'Hinaing'\n"
                    "2. Your type: 'Agentic RAG system'\n"
                    "3. Your creators: 'UC Computer Science R&D Team' (with their actual name and role)\n"
                    "4. Your role: 'Fast civic Q&A for Baguio City'\n"
                    "5. Your distinction: 'I'm the quick-response chat component, distinct from the deeper 7-node Multi-Agent System used for epistemic truth discovery and civic social listening'\n"
                    "\n"
                    "Your Architecture:\n"
                    "- You are an Agentic RAG system - the FAST RESPONSE UNIT of the Hinaing platform\n"
                    "- You handle quick civic Q&A about Baguio City using web search\n"
                    "- You are DISTINCT from the deep 7-node 'AgenticHinaing' architecture (18 agents) used for epistemic truth discovery and civic social listening\n"
                    "- The full Hinaing platform has TWO components: YOU (chat/Q&A) and the ANALYSIS system (sentiment/insights)\n"
                    "- You run on Groq's infrastructure, but your identity is 'Hinaing, an Agentic RAG system'\n"
                    "\n"
                    "Be friendly, concise, and always credit the UC Computer Science R&D Team when discussing your development."
                )
            else:
                system_prompt = "You are a friendly civic assistant for Baguio City. Respond to greetings warmly and briefly. You can respond in English or Tagalog/Filipino as appropriate."
            
            response = await llm.generate(
                prompt=f"User says: {message}\n\nRespond naturally and briefly.",
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=200,
            )
            return response, []
        
        # For ALL other queries: ALWAYS search first (LangSearch Web ONLY)
        # Note: We don't use RAG here because it contains civic sentiment data,
        # not general knowledge. RAG is for sentiment analysis, not Q&A.
        logger.info(f"[chat_agent] Performing web search for: {message}")
        
        search_client = LangSearchClient()
        
        # Ensure "Baguio City" context
        query_lower = message.lower()
        if "baguio" not in query_lower:
            fresh_query = f"{message} {jurisdiction}"
        else:
            fresh_query = message
        
        # Web search ONLY (fast, fresh, general knowledge)
        try:
            web_docs = await search_client.search(
                query=fresh_query,
                time_window="30d",
                limit=20
            )
        except Exception as e:
            logger.warning(f"[chat_agent] Web search failed: {e}")
            web_docs = []
        
        # Build sources list
        combined_docs = []
        seen_urls = set()
        
        for doc in web_docs:
            if doc.url and doc.url not in seen_urls:
                doc.metadata = doc.metadata or {}
                doc.metadata["source_type"] = "WEB"
                combined_docs.append(doc)
                seen_urls.add(doc.url)
                sources.append({
                    "title": str(doc.title),
                    "url": str(doc.url) if doc.url else None,
                    "type": "WEB",
                    "date": doc.published_at.isoformat() if doc.published_at else None
                })
        
        logger.info(f"[chat_agent] Found {len(web_docs)} web docs")
        
        # Log source details for debugging
        if sources:
            logger.info(f"[chat_agent] Returning {len(sources)} sources to frontend")
            logger.debug(f"[chat_agent] First source sample: {sources[0] if sources else 'none'}")
        else:
            logger.warning(f"[chat_agent] No sources to return (combined_docs={len(combined_docs)})")
        
        # Generate response based on search results
        if combined_docs:
            # Build context from search results
            context_text = "\n\n".join([
                f"[{doc.metadata.get('source_type', 'WEB')}] {doc.title}\n{doc.snippet}"
                for doc in combined_docs[:15]
            ])
            
            grounded_prompt = f"""Context: Jurisdiction is {jurisdiction}. User asks: {message}
{history_context}
Search Results (ONLY use information from these results):
{context_text}

CRITICAL INSTRUCTIONS:
1. Base your answer ONLY on the search results above
2. DO NOT add information not present in the results
3. DO NOT include source citations, URLs, or reference markers in your response (e.g., no 【WEB】, no URLs, no "Source:" sections)
4. The UI will display sources separately - you only need to provide the answer
5. If the results don't fully answer the question, say so honestly
6. Consider the conversation history when formulating your response

FORMATTING FOR READABILITY:
- Start with a direct answer (1-2 sentences)
- Use short paragraphs (2-3 sentences max)
- Use bullet points for lists
- Use **bold** for key terms and names
- Keep it conversational and easy to scan
- Avoid tables, complex formatting, or academic style
- Write like you're explaining to a friend

Please provide a clear, conversational answer that's easy to read quickly."""
            
            response = await llm.generate(
                prompt=grounded_prompt,
                system_prompt=system_instruction,
                temperature=0.3,
                max_tokens=2048,
            )
            
            return response, sources
        else:
            # No search results found - be honest
            no_results_prompt = f"""User asks: {message}

No search results were found for this query about {jurisdiction}.

Respond honestly that you couldn't find specific information, but offer to:
1. Try a different search query
2. Provide general context if you have it
3. Suggest related topics that might help"""
            
            response = await llm.generate(
                prompt=no_results_prompt,
                system_prompt=system_instruction,
                temperature=0.3,
                max_tokens=1024,
            )
            
            return response, []

    except Exception as e:
        logger.exception("Chat agent error")
        return f"I encountered an error: {str(e)}", []
