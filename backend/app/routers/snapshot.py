"""Snapshot generation endpoints."""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException

from ..schemas.snapshot import SnapshotRequest, SnapshotResponse
from ..services.insights.graph import generate_snapshot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/insights", tags=["insights"])


@router.post("/snapshot", response_model=SnapshotResponse)
async def create_snapshot(payload: SnapshotRequest) -> SnapshotResponse:
    try:
        return await generate_snapshot(payload)
    except Exception as exc:  # pragma: no cover - defensive, logs upstream
        logger.exception("[snapshot] Error in create_snapshot: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
