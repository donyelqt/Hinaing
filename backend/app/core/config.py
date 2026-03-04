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
    openrouter_api_key: str | None = None

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
    
    # Self-Learning Concerns Memory (for Query Orchestrator)
    # Reduces API cost by caching LLM-generated concerns for 7 days
    concerns_memory_enabled: bool = True  # Enable/disable self-learning
    concerns_memory_ttl_days: int = 7  # Days before regenerating concerns
    
    # Groq Configuration (ultra-fast inference)
    groq_api_key: str | None = None
    groq_default_model: str = "llama-3.3-70b-versatile"
    groq_timeout: float = 30.0
    groq_max_retries: int = 3
    
    # LLM Provider Selection (per node) - ALL USING GROQ
    llm_provider_query_orchestrator: str = "groq"  # Node 1: groq/compound (UNLIMITED TPD)
    llm_provider_sentiment: str = "groq"           # Node 4: llama-4-scout-17b (30K TPM)
    llm_provider_credibility: str = "groq"         # Node 5: llama-3.1-8b-instant (6K TPM)
    llm_provider_theme_agents: str = "groq"        # Node 6: llama-4-scout-17b (30K TPM)
    llm_provider_coordinator: str = "groq"         # Node 7: llama-4-scout-17b (30K TPM)
    
    # Fallback Configuration (DISABLED - Groq SDK has built-in retries)
    # Groq SDK already retries 3 times with exponential backoff
    # Fallback to Gemini defeats the purpose of using Groq for speed
    llm_enable_fallback: bool = False
    llm_fallback_provider: str = "gemini"
    
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
