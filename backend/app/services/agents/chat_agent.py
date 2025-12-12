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


# Define tools map for Gemini (schema only)
tools_map = {
    'search_civic_data': search_civic_data
}


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
            "Architecture: You are the **Assistant Interface**. You are distinct from the deep 7-node 'Sense-Making' architecture. "
            "Mandate: "
            "1. **Greetings & Small Talk:** Do NOT search. For 'hello', 'hi', 'hey', 'thanks', 'bye', etc., respond naturally without calling any tools. "
            "2. **Civic Questions:** Use `search_civic_data` ONLY for substantive civic questions about Baguio (crimes, disasters, infrastructure, events, policies, etc.). "
            "3. **Identity Questions:** Do NOT search. State clearly: 'I am a specialized **Single-Agent Assistant**.' Explain that the 'Analysis' feature of Hinaing is a **separate Multi-Agent System (7 Nodes)** which you can discuss but are not part of. "
            "4. Don't guess. Use tools only for factual civic queries."
        )

    # Use Flash for conversational speed
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        tools=[search_civic_data],
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
            
            if fn_name == 'search_civic_data':
                query = fn_args.get('query', '')
                logger.info(f"[ChatAgent] invoking Hybrid Search for: {query}")
                
                try:
                    # Parallel Execution: 1. Web Search (Fresh) 2. Memory Recall (History)
                    search_client = LangSearchClient()
                    
                    # Calculate date cutoff for explicitly fresh results (last 30 days)
                    cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                    fresh_query = f"{query} {jurisdiction} after:{cutoff_date}"
                    
                    # Create tasks
                    web_task = search_client.search(
                        query=fresh_query,
                        time_window=None # Use explicit after: query instead of API filter
                        )
                    memory_task = context_agent.retrieve_knowledge(
                        focus_areas=[query], # Use query as focus area approximation
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
                        
                    logger.info(f"[ChatAgent] Found {len(web_docs)} web docs and {len(memory_docs)} memory docs")

                    # Combine and Deduplicate
                    combined_docs = []
                    seen_urls = set()
                    
                    # Add FRESH Web Docs first
                    for doc in web_docs:
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
                        
                    # Format for LLM
                    formatted_output = []
                    for doc in combined_docs[:15]: # Limit context context window
                        title = doc.title or "Untitled"
                        snippet = doc.snippet or ""
                        url = str(doc.url) if doc.url else "No URL"
                        src_type = doc.metadata.get("source_type", "WEB")
                        
                        formatted_output.append(f"[{src_type}] Source: {title}\nURL: {url}\nSnippet: {snippet}\n")
                        
                        # Collect for UI
                        sources.append({"title": str(title), "url": str(url) if url else None, "type": src_type})
                        
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
