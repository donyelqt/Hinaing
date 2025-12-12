"""Background Task Manager for Multi-Agent Pipeline.

Provides resilient execution of long-running analysis tasks that survive
client disconnections (mobile alt-tab, screen off, network issues).

Architecture:
- Tasks run as asyncio background tasks
- Progress and results cached in-memory (upgradeable to Redis)
- Frontend polls /status/{task_id} instead of relying on SSE stream
- Results cached for 10 minutes for follow-up questions
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskState:
    """State of a background task."""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    stage: str = "pending"
    message: str = "Task queued"
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": self.progress,
            "stage": self.stage,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class TaskManager:
    """Manages background tasks with progress tracking.
    
    Thread-safe singleton that handles:
    - Task creation and execution
    - Progress updates from pipeline callbacks
    - Result caching with TTL
    - Automatic cleanup of old tasks
    """
    
    _instance: "TaskManager | None" = None
    
    def __new__(cls) -> "TaskManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._tasks: dict[str, TaskState] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._ttl = timedelta(minutes=10)  # Cache results for 10 minutes
        self._cleanup_interval = 60  # Cleanup every 60 seconds
        self._cleanup_task: asyncio.Task | None = None
        self._initialized = True
        logger.info("TaskManager initialized")
    
    def start_cleanup_loop(self):
        """Start background cleanup of expired tasks."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("TaskManager cleanup loop started")
    
    async def _cleanup_loop(self):
        """Periodically remove expired tasks."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")
    
    def _cleanup_expired(self):
        """Remove tasks older than TTL."""
        now = datetime.now()
        expired = [
            task_id for task_id, state in self._tasks.items()
            if now - state.updated_at > self._ttl
        ]
        for task_id in expired:
            del self._tasks[task_id]
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired tasks")
    
    def create_task(self) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = TaskState(task_id=task_id)
        logger.info(f"Created task: {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> TaskState | None:
        """Get task state by ID."""
        return self._tasks.get(task_id)
    
    def update_progress(
        self,
        task_id: str,
        stage: str,
        message: str,
        progress: float
    ):
        """Update task progress (called by pipeline callback)."""
        if task_id not in self._tasks:
            return
        
        state = self._tasks[task_id]
        state.status = TaskStatus.RUNNING
        state.stage = stage
        state.message = message
        state.progress = progress
        state.updated_at = datetime.now()
        
        logger.debug(f"Task {task_id}: {stage} ({progress:.0%})")
    
    def complete_task(self, task_id: str, result: Any):
        """Mark task as completed with result."""
        if task_id not in self._tasks:
            return
        
        state = self._tasks[task_id]
        state.status = TaskStatus.COMPLETED
        state.progress = 1.0
        state.stage = "complete"
        state.message = "Analysis complete"
        state.result = result
        state.updated_at = datetime.now()
        
        # Clean up running task reference
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]
        
        logger.info(f"Task {task_id} completed")
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed with error."""
        if task_id not in self._tasks:
            return
        
        state = self._tasks[task_id]
        state.status = TaskStatus.FAILED
        state.stage = "error"
        state.message = f"Analysis failed: {error}"
        state.error = error
        state.updated_at = datetime.now()
        
        # Clean up running task reference
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]
        
        logger.error(f"Task {task_id} failed: {error}")
    
    async def run_task(
        self,
        task_id: str,
        coro: Coroutine,
        result_formatter: Callable[[Any], Any] | None = None
    ):
        """Execute a coroutine as a background task.
        
        Args:
            task_id: Task identifier
            coro: Coroutine to execute
            result_formatter: Optional function to format the result
        """
        try:
            self._tasks[task_id].status = TaskStatus.RUNNING
            result = await coro
            
            # Format result if formatter provided
            if result_formatter:
                result = result_formatter(result)
            
            self.complete_task(task_id, result)
        except Exception as e:
            logger.exception(f"Task {task_id} execution failed")
            self.fail_task(task_id, str(e)[:200])
    
    def submit_task(
        self,
        task_id: str,
        coro: Coroutine,
        result_formatter: Callable[[Any], Any] | None = None
    ):
        """Submit a task for background execution (non-blocking).
        
        Args:
            task_id: Task identifier
            coro: Coroutine to execute
            result_formatter: Optional function to format the result
        """
        async_task = asyncio.create_task(
            self.run_task(task_id, coro, result_formatter)
        )
        self._running_tasks[task_id] = async_task
        logger.info(f"Task {task_id} submitted for background execution")


# Global singleton
_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """Get the global TaskManager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
