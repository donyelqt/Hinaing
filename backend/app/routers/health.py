import psutil
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/", summary="Root health check")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "hinaing-backend"}


@router.get("/health/memory", summary="Memory usage stats")
async def memory_stats() -> dict:
    """Check memory usage - useful for debugging Railway crashes."""
    process = psutil.Process()
    mem_info = process.memory_info()
    
    return {
        "status": "ok",
        "memory_mb": round(mem_info.rss / 1024 / 1024, 2),
        "memory_percent": round(process.memory_percent(), 2),
        "cpu_percent": round(process.cpu_percent(), 2),
    }
