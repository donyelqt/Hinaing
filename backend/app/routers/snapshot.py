"""Snapshot generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.snapshot import SnapshotRequest, SnapshotResponse
from ..services.insights.graph import generate_snapshot

router = APIRouter(prefix="/insights", tags=["insights"])


@router.post("/snapshot", response_model=SnapshotResponse)
async def create_snapshot(payload: SnapshotRequest) -> SnapshotResponse:
    try:
        return await generate_snapshot(payload)
    except Exception as exc:  # pragma: no cover - defensive, logs upstream
        raise HTTPException(status_code=500, detail="Failed to generate snapshot") from exc
