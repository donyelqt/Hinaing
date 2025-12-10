import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import agent, health, snapshot, chat

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload heavy models at startup to avoid OOM during requests."""
    logger.info("[startup] Preloading ML models...")
    
    # Preload RoBERTa sentiment model (prevents OOM on first request)
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
    yield
    logger.info("[shutdown] Application shutting down")


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    settings = get_settings()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
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
