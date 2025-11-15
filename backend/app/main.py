from fastapi import FastAPI

from .routers import health


def create_app() -> FastAPI:
    app = FastAPI(title="Public Sentiment Agent Backend")
    app.include_router(health.router)
    return app


app = create_app()
