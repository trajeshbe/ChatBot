from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    source_type = Column(String(50), nullable=False)  # 'upload' or 'scrape'
    source_url = Column(String(1024), nullable=True)  # For scraped content
    processing_status = Column(String(50), default='pending', nullable=True)  # 'pending', 'processing', 'completed', 'failed'
    error_message = Column(Text, nullable=True)
    meta_info = Column('metadata', JSON, nullable=True)  # Mapped to 'metadata' column in DB (metadata is reserved in SQLAlchemy)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Organizational hierarchy
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)
    user_role = Column(String(50), nullable=True)  # Role of uploader at upload time
    minio_path = Column(String(1024), nullable=True)  # Full hierarchical MinIO path


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    # Multi-column vector storage for different embedding strategies
    # Primary embedding column (384-dim, text semantic by default)
    embedding = Column(Vector(384), nullable=True)  # Text semantic embeddings (all-MiniLM-L6-v2)

    # Additional embedding columns for content-specific strategies
    table_embedding = Column(Vector(512), nullable=True)      # Table structure embeddings
    visual_embedding = Column(Vector(512), nullable=True)     # Vision embeddings (CLIP)
    numerical_embedding = Column(Vector(256), nullable=True)  # Numerical/statistical embeddings
    code_embedding = Column(Vector(768), nullable=True)       # Code embeddings (CodeBERT)

    # Embedding metadata
    embedding_strategy = Column(String(50), nullable=True)    # Strategy used (text_semantic, table_structure, etc.)
    embedding_metadata = Column(JSON, nullable=True)          # ContentAnalyzer results and strategy info

    meta_info = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Denormalized fields for fast RAG queries and access control
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    meta_info = Column(JSON, nullable=True)

    # Project context
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # References to source documents/chunks
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WebScrapeJob(Base):
    __tablename__ = "web_scrape_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(1024), nullable=False)
    scrape_prompt = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='pending')  # 'pending', 'processing', 'completed', 'failed'
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Project tracking (fixed FK to reference modules, not projects)
    project_id = Column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    scraped_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)

    # NOTE: Enhanced scraping fields commented out until migration is created
    # compliance_level = Column(String(50), default='balanced')  # strict, balanced, aggressive
    # proxy_used = Column(String(255), nullable=True)
    # user_agent_used = Column(String(512), nullable=True)
    # auth_method = Column(String(50), nullable=True)  # none, basic, bearer, api_key, etc.
    # llm_provider = Column(String(50), nullable=True)  # ollama, openai, anthropic
    # scraping_time_ms = Column(Float, nullable=True)
    # protocols_detected = Column(JSON, nullable=True)
    # meta_info = Column(JSON, nullable=True)


class QueryCache(Base):
    __tablename__ = "query_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(384))
    response = Column(JSON, nullable=False)
    sources = Column(JSON, nullable=True)
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ttl_seconds = Column(Integer, default=3600)


class AgentTask(Base):
    """Agent task tracking table"""
    __tablename__ = "agent_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(255), unique=True, nullable=False, index=True)  # Human-readable task ID
    task_name = Column(String(255), nullable=True, index=True)  # 🆕 NEW: LLM-generated task name

    # Task details
    task_description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default='pending')  # pending, running, completed, failed, cancelled
    session_id = Column(String(255), nullable=True, index=True)
    model = Column(String(100), nullable=False, default='qwen2.5-coder:7b')
    minio_base_path = Column(Text, nullable=True)  # 🆕 NEW: Base path in MinIO for task artifacts

    # Configuration
    max_iterations = Column(Integer, default=20)
    timeout_seconds = Column(Integer, default=600)

    # Progress tracking
    current_iteration = Column(Integer, default=0)
    current_phase = Column(String(50), nullable=True)  # THINK, PLAN, ACT, OBSERVE

    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Results
    result = Column(Text, nullable=True)  # Final answer or result
    artifacts = Column(ARRAY(String), default=[])  # List of generated artifact paths
    tools_used = Column(ARRAY(String), default=[])  # List of tools executed
    llm_calls = Column(Integer, default=0)

    # Error handling
    error = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    meta_info = Column(JSON, nullable=True)

    # Project tracking (similar to other models)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)


# Import enhanced models (RBAC, audit logs, sessions)
# These are imported here to ensure they use the same Base
try:
    from app.models.database_enhanced import (
        User, APIKey, ChatSession, SessionDocument, ConversationMessage,
        AuditLog, UsageMetrics, DocumentPermission, SessionContext,
        UserRole, ActionType
    )
    __all__ = [
        'Document', 'DocumentChunk', 'Conversation', 'Message',
        'WebScrapeJob', 'QueryCache', 'AgentTask',
        'User', 'APIKey', 'ChatSession', 'SessionDocument', 'ConversationMessage',
        'AuditLog', 'UsageMetrics', 'DocumentPermission', 'SessionContext',
        'UserRole', 'ActionType', 'Base'
    ]
except ImportError:
    # Enhanced models not available yet
    __all__ = [
        'Document', 'DocumentChunk', 'Conversation', 'Message',
        'WebScrapeJob', 'QueryCache', 'AgentTask', 'Base'
    ]
