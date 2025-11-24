from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service metadata
    app_name: str = "Public Sentiment Agent Backend"
    environment: str = "development"
    frontend_origin: str = "http://localhost:3000"

    # External services
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str

    qdrant_url: str
    qdrant_api_key: str | None = None

    gemini_api_key: str

    facebook_app_id: str
    facebook_app_secret: str
    facebook_access_token: str

    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str = "baguio-public-sentiment/0.1"

    # LangSearch
    langsearch_api_key: str | None = None
    langsearch_base_url: str = "https://api.langsearch.com/v1/web-search"
    langsearch_rerank_url: str = "https://api.langsearch.com/v1/rerank"

    langsmith_api_key: str | None = None
    langsmith_project: str = "pr-scholarly-mesenchyme-11"
    ingestion_interval_seconds: int = 120
    ingestion_region_keywords: list[str] = [
        "baguio",
        "baguio city",
        "cordillera",
        "session road",
        "burnham park",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
