"""Snapshot generation endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..schemas.snapshot import SnapshotRequest, SnapshotResponse
from ..services.insights.graph import generate_snapshot
from ..services.task_manager import get_task_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/insights", tags=["insights"])


def _build_progress_callback(task_id: str):
    """Bridge generate_snapshot progress into the TaskManager entry."""

    async def _callback(stage: str, message: str, progress: float) -> None:
        task_manager = get_task_manager()
        task_manager.update_progress(
            task_id,
            stage=stage,
            message=message,
            progress=progress,
        )

    return _callback


@router.post("/snapshot/start")
async def start_snapshot(payload: SnapshotRequest) -> dict[str, str]:
    """Start snapshot generation in the background and return a task id.

    Snapshot runs 60 to 300 seconds. A blocking POST exceeds the hosted
    proxy's response window, so the client starts a task and polls
    /snapshot/status/{task_id}. This matches the chat analyze contract.
    """
    task_manager = get_task_manager()
    task_manager.start_cleanup_loop()
    task_id = task_manager.create_task()

    async def run_pipeline() -> SnapshotResponse:
        return await generate_snapshot(
            payload,
            progress_callback=_build_progress_callback(task_id),
        )

    task_manager.submit_task(task_id, run_pipeline())
    logger.info("[snapshot/start] Task %s submitted for focus areas %s", task_id, payload.focus_areas)

    return {"task_id": task_id}


@router.get("/snapshot/status/{task_id}")
async def get_snapshot_status(task_id: str) -> dict:
    """Poll snapshot task status.

    Returns status, progress, stage, message, and the full SnapshotResponse
    under "result" once the task completes.
    """
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found. It may have expired (TTL: 10 minutes).",
        )

    return task.to_dict()