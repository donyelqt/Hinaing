import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import agent, health, snapshot, chat

logger = logging.getLogger(__name__)


def _load_models_sync():
    """Load ML models synchronously (called from background task)."""
    # Preload RoBERTa sentiment model
    try:
        from .services.agents.sentiment_agent import get_sentiment_model
        get_sentiment_model()
        logger.info("[startup] RoBERTa sentiment model loaded")
    except Exception as e:
        logger.warning(f"[startup] Failed to preload sentiment model: {e}")
    
    # Preload embedding model for RAG
    try:
        from .services.rag.embeddings import get_embedding_service
        get_embedding_service()
        logger.info("[startup] Embedding model loaded")
    except Exception as e:
        logger.warning(f"[startup] Failed to preload embedding model: {e}")
    
    logger.info("[startup] Model preloading complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start server immediately, load models in background."""
    logger.info("[startup] Application starting - health check ready")
    
    # Start model loading in background (non-blocking)
    # This allows the server to respond to health checks immediately
    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(_load_models_sync)
    
    yield
    
    executor.shutdown(wait=False)
    logger.info("[shutdown] Application shutting down")


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    settings = get_settings()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    # CORS: Allow frontend origin, or all origins if not specified
    allowed_origins = [settings.frontend_origin] if settings.frontend_origin else ["*"]
    if settings.environment != "development":
        # In production, also allow common patterns
        allowed_origins = ["*"]  # Allow all for now; restrict later if needed
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(snapshot.router)
    app.include_router(chat.router)
    app.include_router(agent.router)
    return app


app = create_app()
