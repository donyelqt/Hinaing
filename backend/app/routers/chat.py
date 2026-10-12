"""Chat endpoint for conversational insights."""
from __future__ import annotations

import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
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
    llm_mode: str = Field(default="cloud", description="LLM execution mode: cloud (Groq) or local (Ollama/Qwen)")

    @field_validator("llm_mode")
    @classmethod
    def _validate_llm_mode(cls, v: str) -> str:
        normalized = str(v).strip().lower()
        if normalized not in ("cloud", "local"):
            raise ValueError(f"llm_mode must be 'cloud' or 'local', got {v!r}")
        return normalized


class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = []


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    try:
        response, sources = await run_chat_agent(
            message=payload.message,
            history=payload.history,
            jurisdiction=payload.jurisdiction,
            llm_mode=payload.llm_mode
        )
        return ChatResponse(response=response, sources=sources)
    except Exception as exc:
        logger.exception(f"Chat endpoint error: {exc}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(exc)}")
