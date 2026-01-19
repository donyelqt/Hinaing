import gc
import logging
import psutil
from contextlib import asynccontextmanager
from .core.executor import GLOBAL_EXECUTOR

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import agent, health, snapshot, chat, chat_analyze, metrics

# CTO-Grade Memory & Execution Tuning for 16GB Environment
# 1. Increase GC thresholds: less frequent, more efficient collections
gc.set_threshold(50000, 500, 500)

logger = logging.getLogger(__name__)

# Leverage 16GB RAM: Increase from 2 to 8 concurrent heavy pipelines
_active_requests = 0
_MAX_CONCURRENT_HEAVY_REQUESTS = 8


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
    
    # Track all requests for transparency
    logger.info(f"-> {request.method} {request.url.path}")
    
    # Track heavy endpoints for specialized memory handling
    is_heavy = request.url.path in ["/insights/snapshot", "/api/snapshot", "/agents/gemini", "/chat/analyze"]
    
    if is_heavy:
        _active_requests += 1
        logger.info(f"[memory] Starting heavy task: {request.url.path} (Active: {_active_requests})")
    
    try:
        response = await call_next(request)
        return response
    finally:
        if is_heavy:
            _active_requests -= 1
            try:
                # CTO-Grade: Conditional Cleanup
                # We only flush RAM if we are actually reaching limits (75% of 16GB)
                # This keeps our embedding cache and resident models 'Hot' in memory
                vm = psutil.virtual_memory()
                process = psutil.Process()
                mem_mb = process.memory_info().rss / 1024 / 1024
                
                # Check if system RAM is tight (>75%) or process exceeds 8GB
                should_cleanup = vm.percent > 75 or mem_mb > 8192
                
                if should_cleanup:
                    logger.info(f"[memory] High memory pressure ({vm.percent}%). Clearing caches...")
                    from .services.rag.embeddings import clear_embedding_cache
                    clear_embedding_cache()
                    gc.collect()
                    
                logger.info(f"[memory] Request complete. Resident Memory: {mem_mb:.1f}MB, Active: {_active_requests}")
            except Exception as e:
                logger.warning(f"[memory] Cleanup heuristic error: {e}")
                gc.collect()


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    settings = get_settings()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    # CORS: Allow frontend origin, or all origins if not specified
    if settings.frontend_origin:
        allowed_origins = [o.strip() for o in settings.frontend_origin.split(",")]
    else:
        allowed_origins = ["*"]
        
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
