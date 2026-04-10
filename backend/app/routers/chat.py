"""Chat endpoint for conversational insights."""
from __future__ import annotations

import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from ..services.agents.chat_agent import run_chat_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    jurisdiction: str = "Baguio City"


class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = []


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    try:
        response, sources = await run_chat_agent(
            message=payload.message,
            history=payload.history,
            jurisdiction=payload.jurisdiction
        )
        return ChatResponse(response=response, sources=sources)
    except Exception as exc:
        logger.exception(f"Chat endpoint error: {exc}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(exc)}")
