"""Conversational agent for civic insights using LangSearch."""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Any

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ...core.config import get_settings
from ..langsearch import LangSearchClient

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
    jurisdiction: str = "Baguio City"
) -> Tuple[str, List[dict]]:
    """Run the conversational loop."""
    settings = get_settings()
    if not settings.gemini_api_key:
        return "Error: Gemini API key missing.", []

    genai.configure(api_key=settings.gemini_api_key)
    
    # Use Flash for conversational speed
    model = genai.GenerativeModel(
        "gemini-2.0-flash-exp",
        tools=[search_civic_data]
    )
    
    # Build history for Gemini
    chat_history = []
    if history:
        for msg in history:
            role = "user" if msg.role == "user" else "model"
            chat_history.append({"role": role, "parts": [msg.content]})

    # Start chat session
    chat = model.start_chat(history=chat_history)
    
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
                logger.info(f"[ChatAgent] invoking LangSearch for: {query}")
                
                # Use LangSearchClient
                client = LangSearchClient()
                try:
                    # Provide default context for better search
                    docs = await client.search(
                        query=f"{query} {jurisdiction}",
                        time_window="24h" # Default to fresh content for chat
                    )
                    
                    if not docs:
                        return "No relevant results found."
                        
                    formatted_docs = []
                    for doc in docs[:5]:
                        title = doc.title or "Untitled"
                        snippet = doc.snippet or "No snippet"
                        url = doc.url or "No URL"
                        formatted_docs.append(f"Source: {title}\nURL: {url}\nSnippet: {snippet}\n")
                        
                        # Collect for UI return
                        sources.append({"title": title, "url": url})
                        
                    return "\n".join(formatted_docs)
                except Exception as e:
                    logger.error(f"LangSearch failed: {e}")
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
