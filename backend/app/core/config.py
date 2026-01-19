from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service metadata
    app_name: str = "Public Sentiment Agent Backend"
    environment: str = "development"
    frontend_origin: str = "http://localhost:3000,http://localhost:3001"

    # External services (all optional with defaults to prevent startup crash)
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""

    qdrant_url: str = ""
    qdrant_api_key: str | None = None

    gemini_api_key: str = ""

    facebook_app_id: str = ""
    facebook_app_secret: str = ""
    facebook_access_token: str = ""

    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "Hinaing/1.0 (Academic Research)"

    # LangSearch
    langsearch_api_key: str | None = None
    langsearch_base_url: str = "https://api.langsearch.com/v1/web-search"
    langsearch_rerank_url: str = "https://api.langsearch.com/v1/rerank"

    langsmith_api_key: str | None = None
    langsmith_project: str = "pr-scholarly-mesenchyme-11"
    
    # Google Fact Check API (uses same Google Cloud project as Gemini)
    google_fact_check_api_key: str | None = None
    
    # Tavily API for claim verification
    tavily_api_key: str | None = None
    ingestion_interval_seconds: int = 120
    ingestion_region_keywords: list[str] = [
        "baguio",
        "baguio city",
        "cordillera",
        "session road",
        "burnham park",
    ]

    # Apify Facebook Groups Scraper
    apify_api_token: str | None = None
    apify_facebook_groups_actor_id: str = "apify~facebook-groups-scraper"
    apify_facebook_group_urls: str = "[]"  # JSON array string
    apify_facebook_results_limit: int = 10


def get_settings() -> Settings:
    return Settings()
