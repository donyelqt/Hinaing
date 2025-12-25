import gc
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import agent, health, snapshot, chat, chat_analyze, metrics

logger = logging.getLogger(__name__)

# Track concurrent requests to prevent memory exhaustion
_active_requests = 0
_MAX_CONCURRENT_HEAVY_REQUESTS = 2


def _load_models_sync():
    """Load ML models synchronously (called from background task)."""
    # Preload RoBERTa sentiment model
    try:
        from .services.agents.sentiment_agent import get_sentiment_model
        get_sentiment_model()
        logger.info("System cleaned: Ollama removed.")
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
    # Force garbage collection on shutdown
    gc.collect()
    logger.info("[shutdown] Application shutting down")


async def memory_cleanup_middleware(request: Request, call_next):
    """Clean up memory after heavy requests."""
    global _active_requests
    
    # Track heavy endpoints
    is_heavy = request.url.path in ["/insights/snapshot", "/api/snapshot"]
    
    if is_heavy:
        _active_requests += 1
        logger.info(f"[memory] Active heavy requests: {_active_requests}")
    
    try:
        response = await call_next(request)
        return response
    finally:
        if is_heavy:
            _active_requests -= 1
            try:
                from .services.rag.embeddings import clear_embedding_cache
                
                # Clear embedding cache (still uses local RAM)
                clear_embedding_cache()
                
                # Force garbage collection
                gc.collect()
                
                # Log memory after cleanup
                import psutil
                process = psutil.Process()
                mem_mb = process.memory_info().rss / 1024 / 1024
                logger.info(f"[memory] Cleanup done. Memory: {mem_mb:.1f}MB, Active: {_active_requests}")
            except Exception as e:
                logger.warning(f"[memory] Cleanup error: {e}")
                gc.collect()


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
    
    # Add memory cleanup middleware FIRST (runs after CORS due to middleware order)
    @app.middleware("http")
    async def cleanup_middleware(request: Request, call_next):
        # Skip cleanup logic for OPTIONS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)
        return await memory_cleanup_middleware(request, call_next)
    
    # CORS middleware added AFTER custom middleware (runs BEFORE due to reverse order)
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
    app.include_router(chat_analyze.router)
    app.include_router(agent.router)
    app.include_router(metrics.router)
    return app


app = create_app()
