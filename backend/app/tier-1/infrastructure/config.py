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

    # ========================================
    # HYBRID AGENT SYSTEM (Claude Code Integration)
    # ========================================

    # Agent Mode Configuration
    AGENT_MODE_ENABLED: bool = True  # Enable/disable agent mode globally
    AGENT_MODE_DEFAULT: bool = False  # Default state for "Use Claude Code" checkbox

    # API Budget Limits (Cost Control)
    DAILY_API_BUDGET_LIMIT: float = 10.0  # $10/day for Anthropic API
    MONTHLY_API_BUDGET_LIMIT: float = 200.0  # $200/month for Anthropic API

    # Agent Iteration Limits
    LOCAL_MINI_AGENT_MAX_ITERATIONS: int = 20  # Max iterations for local agent
    CLAUDE_CLI_AGENT_MAX_ITERATIONS: int = 50  # Max iterations for Claude CLI agent
    AGENT_EXECUTION_TIMEOUT_SECONDS: int = 600  # 10 minutes max per task

    # Ollama Model Configuration (Local Agent)
    AGENT_CODE_MODEL: str = "qwen2.5-coder:7b"  # Code generation, EDA, data analysis
    AGENT_VISION_MODEL: str = "llama3.2-vision:11b"  # Image analysis, OCR, screenshots
    AGENT_BACKUP_MODEL: str = "deepseek-coder:6.7b"  # Backup for code tasks
    OLLAMA_BASE_URL: str = "http://rag-ollama:11434"  # Updated to match actual container

    # Agent Runtime Configuration
    AGENT_WORKSPACE_BASE: str = "/tmp/agent_workspaces"  # Base directory for agent workspaces
    AGENT_CONTAINER_IMAGE: str = "chatbot-agent-runtime:latest"  # Sandbox container image
    AGENT_ENABLE_STREAMING: bool = True  # Enable real-time event streaming via Redis

    # Task Complexity Thresholds (Auto-routing)
    COMPLEXITY_SIMPLE_THRESHOLD: float = 0.3  # Below this = SIMPLE (direct RAG)
    COMPLEXITY_MEDIUM_THRESHOLD: float = 0.6  # Between 0.3-0.6 = MEDIUM (local agent)
    # Above 0.6 = COMPLEX (local or Claude CLI based on task type)

    # Hybrid Routing Preferences (can be overridden by user)
    PREFER_LOCAL_FOR_DATA_ANALYSIS: bool = True  # Use free local agent for data tasks
    PREFER_LOCAL_FOR_CODE_GENERATION: bool = True  # Use free local agent for code gen
    PREFER_LOCAL_FOR_VISION: bool = True  # Use free local agent for vision tasks
    PREFER_CLAUDE_FOR_RESEARCH: bool = True  # Use Claude CLI for research (if budget allows)
    PREFER_CLAUDE_FOR_WEB_AUTOMATION: bool = True  # Use Claude CLI for web tasks (if budget allows)

    # ========================================
    # MODEL FINE-TUNING SYSTEM
    # ========================================

    # Fine-Tuning Feature Flags
    ENABLE_FINETUNING: bool = True  # Enable/disable fine-tuning feature globally
    FINETUNING_REQUIRE_APPROVAL: bool = True  # Require admin approval for training jobs

    # GPU Configuration
    FINETUNING_GPU_POOL: Optional[List[str]] = None  # GPU IDs to use (None = auto-detect all)
    FINETUNING_DEFAULT_GPU_COUNT: int = 1  # Default number of GPUs per job
    FINETUNING_MIN_GPU_MEMORY_GB: float = 12.0  # Minimum GPU memory required (GB)
    FINETUNING_MAX_CONCURRENT_JOBS: int = 2  # Maximum concurrent training jobs

    # Container Configuration
    FINETUNING_CONTAINER_IMAGE: str = "chatbot-finetuning-runtime:latest"
    FINETUNING_CONTAINER_NETWORK: str = "chatbot_default"  # Docker network
    FINETUNING_WORKSPACE_BASE: str = "/tmp/finetuning_workspaces"  # Base directory for training workspaces

    # Resource Limits
    FINETUNING_MAX_MEMORY_GB: int = 24  # Maximum RAM per training job
    FINETUNING_MAX_CPU_CORES: int = 8  # Maximum CPU cores per job
    FINETUNING_MAX_TRAINING_TIME_HOURS: int = 24  # Maximum training time before timeout
    FINETUNING_MAX_DATASET_SIZE_MB: int = 1000  # Maximum dataset size (1GB)

    # Default Hyperparameters (can be overridden per job)
    FINETUNING_DEFAULT_LEARNING_RATE: float = 2e-4
    FINETUNING_DEFAULT_BATCH_SIZE: int = 4
    FINETUNING_DEFAULT_NUM_EPOCHS: int = 3
    FINETUNING_DEFAULT_WARMUP_STEPS: int = 100
    FINETUNING_DEFAULT_GRADIENT_ACCUMULATION: int = 4
    FINETUNING_DEFAULT_LORA_R: int = 16  # LoRA rank
    FINETUNING_DEFAULT_LORA_ALPHA: int = 32  # LoRA alpha
    FINETUNING_DEFAULT_LORA_DROPOUT: float = 0.05

    # Supported Methods
    FINETUNING_SUPPORTED_METHODS: List[str] = ["peft", "sft", "rlhf-ppo", "rlhf-grpo"]
    FINETUNING_SUPPORTED_OBJECTIVES: List[str] = ["qa", "classification", "instruction", "summarization", "preference"]

    # MLflow Configuration (Optional - for experiment tracking)
    MLFLOW_TRACKING_URI: Optional[str] = None  # e.g., "http://mlflow:5000"
    MLFLOW_EXPERIMENT_NAME: str = "model-finetuning"
    MLFLOW_ENABLE_AUTOLOGGING: bool = True

    # Model Deployment
    FINETUNING_DEFAULT_DEPLOYMENT_TARGET: str = "ollama"  # ollama, vllm
    FINETUNING_AUTO_DEPLOY_ON_COMPLETION: bool = False  # Automatically deploy successful models

    # Checkpointing
    FINETUNING_SAVE_CHECKPOINTS: bool = True
    FINETUNING_CHECKPOINT_FREQUENCY: int = 100  # Save checkpoint every N steps
    FINETUNING_KEEP_BEST_CHECKPOINTS: int = 3  # Number of best checkpoints to keep

    # MinIO Paths for Fine-Tuning
    MINIO_FINETUNING_DATASETS_BUCKET: str = "finetuning-datasets"
    MINIO_FINETUNING_CHECKPOINTS_BUCKET: str = "finetuning-checkpoints"
    MINIO_FINETUNING_MODELS_BUCKET: str = "finetuning-models"

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
    SIMILARITY_THRESHOLD: float = 0.50  # LOWERED to 50% - make vectors accessible to all (per user requirement)
    MIN_SIMILARITY_THRESHOLD: float = 0.40  # Minimum threshold for fallback (40% - more permissive)

    # Source quality thresholds
    HIGH_QUALITY_SOURCE_THRESHOLD: float = 0.70  # Show sources above 70% confidence
    SOURCE_DISPLAY_THRESHOLD: float = 0.50  # Minimum threshold to display a source (50% - more permissive)

    # Query classification thresholds
    # If best match is below this, likely not document-related query
    NO_RELEVANT_DOCS_THRESHOLD: float = 0.35  # LOWERED to 35% - ensure all documents are searchable (per user: "vector should be accessible by all")

    # Hybrid Search Weights (CONFIGURABLE - can be overridden per query)
    # Controls the balance between semantic (vector) and keyword (lexical) search
    # Default: 80% semantic, 20% keyword for better semantic matching
    # Higher semantic weight favors meaning/context, higher keyword weight favors exact matches
    SEMANTIC_WEIGHT: float = 0.8  # 80% weight for vector similarity
    KEYWORD_WEIGHT: float = 0.2   # 20% weight for keyword matching
    # Note: SEMANTIC_WEIGHT + KEYWORD_WEIGHT should equal 1.0

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

    # Compliance and governance
    SCRAPING_ENFORCE_COMPLIANCE: bool = False  # Set to True in production to require scraping configs

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
