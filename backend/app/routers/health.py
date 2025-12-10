from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/", summary="Root health check")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "hinaing-backend"}
