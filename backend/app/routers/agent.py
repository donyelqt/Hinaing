"""Endpoints for Gemini agent interactions."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.agent import GeminiAgentRequest, GeminiAgentResponse
from ..services.agents.gemini import run_gemini_agent

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/gemini", response_model=GeminiAgentResponse)
async def invoke_gemini_agent(payload: GeminiAgentRequest) -> GeminiAgentResponse:
    try:
        output = run_gemini_agent(
            payload.message,
            documents=[doc.model_dump() for doc in (payload.documents or [])] or None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return GeminiAgentResponse(output=output)
