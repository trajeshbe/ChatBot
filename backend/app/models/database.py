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
    meta_info = Column(JSON, nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)

    # Hierarchical organization: role/dept/team/username/project/folder/file
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)
    user_role = Column(String(50), nullable=True)  # Role at upload time
    minio_path = Column(String(1024), nullable=True)  # Full hierarchical path


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384))  # Dimension matches EMBEDDING_DIMENSION in config
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
    status = Column(String(50), nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    meta_info = Column(JSON, nullable=True)

    # Enhanced scraping fields
    compliance_level = Column(String(50), default='balanced')  # strict, balanced, aggressive
    proxy_used = Column(String(255), nullable=True)
    user_agent_used = Column(String(512), nullable=True)
    auth_method = Column(String(50), nullable=True)  # none, basic, bearer, api_key, etc.
    llm_provider = Column(String(50), nullable=True)  # ollama, openai, anthropic
    scraping_time_ms = Column(Float, nullable=True)
    protocols_detected = Column(JSON, nullable=True)

    # Project tracking
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    scraped_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)


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
        'WebScrapeJob', 'QueryCache',
        'User', 'APIKey', 'ChatSession', 'SessionDocument', 'ConversationMessage',
        'AuditLog', 'UsageMetrics', 'DocumentPermission', 'SessionContext',
        'UserRole', 'ActionType', 'Base'
    ]
except ImportError:
    # Enhanced models not available yet
    __all__ = [
        'Document', 'DocumentChunk', 'Conversation', 'Message',
        'WebScrapeJob', 'QueryCache', 'Base'
    ]
