from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Enterprise RAG Chatbot"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]

    # PostgreSQL + pgvector
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ragchatbot"
    POSTGRES_PORT: int = 5432

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "documents"
    MINIO_SECURE: bool = False

    # vLLM
    VLLM_ENDPOINT: str = "http://vllm-service:8000"
    VLLM_MODEL: str = "meta-llama/Llama-2-7b-chat-hf"

    # Ollama (local LLM - replaces llama.cpp)
    OLLAMA_ENDPOINT: str = "http://ollama:11434"

    # llama.cpp fallback (DEPRECATED - use Ollama instead)
    LLAMA_CPP_ENDPOINT: str = "http://llama-cpp:8080"

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_API_KEY: Optional[str] = None  # For Claude models

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Prefect
    PREFECT_API_URL: str = "http://prefect-server:4200/api"

    # Feast
    FEAST_REPO_PATH: str = "/app/feast"

    # OpenTelemetry
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "tempo:4317"  # gRPC endpoint (no http://)
    OTEL_SERVICE_NAME: str = "rag-chatbot-api"

    # Feature flags
    USE_VLLM: bool = True
    USE_SEMANTIC_CACHE: bool = True
    ENABLE_TRACING: bool = True

    # Web Scraping Feature Flags
    ENABLE_WEB_SCRAPING: bool = True
    ENABLE_PLAYWRIGHT_SCRAPING: bool = False  # Requires playwright installation
    ENABLE_SMART_SCRAPING: bool = True  # Use AI to filter scraped content

    # RAG settings
    CHUNK_SIZE: int = 800  # Increased from 500 for better context (optimal for embeddings)
    CHUNK_OVERLAP: int = 150  # Increased from 50 for better continuity (20% overlap)
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.75  # INCREASED to 75% for higher quality matches
    MIN_SIMILARITY_THRESHOLD: float = 0.60  # Minimum threshold for fallback (60% minimum quality)

    # Source quality thresholds
    HIGH_QUALITY_SOURCE_THRESHOLD: float = 0.75  # Only show sources above 75% confidence
    SOURCE_DISPLAY_THRESHOLD: float = 0.70  # Minimum threshold to display a source (70%)

    # Query classification thresholds
    # If best match is below this, likely not document-related query
    NO_RELEVANT_DOCS_THRESHOLD: float = 0.70  # INCREASED to 70% - stricter threshold to prevent irrelevant document retrieval

    # Web Scraping Configuration
    SCRAPER_DEFAULT_STRATEGY: str = "auto"  # auto, trafilatura, beautifulsoup, playwright, hybrid
    SCRAPER_TIMEOUT: float = 30.0  # Request timeout in seconds
    SCRAPER_MAX_RETRIES: int = 3  # Maximum retry attempts
    SCRAPER_FOLLOW_REDIRECTS: bool = True
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Content extraction options
    SCRAPER_INCLUDE_LINKS: bool = True
    SCRAPER_INCLUDE_TABLES: bool = True
    SCRAPER_INCLUDE_IMAGES: bool = False
    SCRAPER_INCLUDE_METADATA: bool = True

    # Content filtering
    SCRAPER_REMOVE_NAV: bool = True
    SCRAPER_REMOVE_FOOTER: bool = True
    SCRAPER_REMOVE_HEADER: bool = True
    SCRAPER_REMOVE_ADS: bool = True

    # JavaScript rendering (Playwright)
    SCRAPER_ENABLE_JAVASCRIPT: bool = False  # Enable for JS-heavy sites
    SCRAPER_WAIT_TIMEOUT: float = 10.0  # Wait timeout for JS rendering

    # Rate limiting and throttling
    SCRAPER_RESPECT_ROBOTS_TXT: bool = True
    SCRAPER_DELAY_BETWEEN_REQUESTS: float = 1.0  # Delay in seconds
    SCRAPER_MAX_CONCURRENT_REQUESTS: int = 5

    # Content quality
    SCRAPER_MIN_CONTENT_LENGTH: int = 100  # Minimum content length in characters
    SCRAPER_MAX_CONTENT_LENGTH: Optional[int] = 1000000  # Maximum content length (1MB)

    # Smart scraping (AI-powered content filtering)
    SMART_SCRAPE_MODEL: str = "gpt-3.5-turbo"  # Model for content filtering
    SMART_SCRAPE_MAX_TOKENS: int = 2000  # Max tokens for filtered content

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
