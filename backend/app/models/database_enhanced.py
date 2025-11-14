"""
Enhanced database models for RBAC, Sessions, and Audit Logging
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Boolean, Float, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
import enum

# Use the same Base as the main database models
from app.models.database import Base


# Enums for RBAC
class UserRole(str, enum.Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_USER = "api_user"


class ActionType(str, enum.Enum):
    """Types of auditable actions"""
    QUERY = "query"
    UPLOAD = "upload"
    SCRAPE = "scrape"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    VIEW = "view"


# User and RBAC Models
class User(Base):
    """User accounts with RBAC"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    meta_info = Column(JSON, nullable=True)


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    meta_info = Column(JSON, nullable=True)


# Enhanced Session Management
class ChatSession(Base):
    """Chat sessions with user tracking and metadata"""
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=True)  # Auto-generated from first query
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    meta_info = Column(JSON, nullable=True)  # Browser, IP, etc.


class SessionDocument(Base):
    """Association between sessions and documents (short-term memory)"""
    __tablename__ = "session_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    priority = Column(Integer, default=0)  # Higher priority documents checked first
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Auto-expire old associations
    meta_info = Column(JSON, nullable=True)


class ConversationMessage(Base):
    """Messages within a chat session (replaces old Message table)"""
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    model_id = Column(String(100), nullable=True)  # Which model was used
    model_name = Column(String(255), nullable=True)  # Display name
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    cost_usd = Column(Float, nullable=True)
    sources = Column(JSON, nullable=True)  # Source documents/chunks used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_info = Column(JSON, nullable=True)


# Audit Logging
class AuditLog(Base):
    """Comprehensive audit trail for all user actions"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    action = Column(SQLEnum(ActionType), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)  # 'document', 'query', 'model', etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text, nullable=True)
    request_data = Column(JSON, nullable=True)  # Sanitized request payload
    response_data = Column(JSON, nullable=True)  # Sanitized response
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(512), nullable=True)
    status_code = Column(Integer, nullable=True)  # HTTP status
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    meta_info = Column(JSON, nullable=True)


# Usage Tracking and Analytics
class UsageMetrics(Base):
    """Aggregated usage metrics for analytics"""
    __tablename__ = "usage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    model_id = Column(String(100), nullable=True, index=True)
    total_queries = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    documents_uploaded = Column(Integer, default=0)
    pages_scraped = Column(Integer, default=0)
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_info = Column(JSON, nullable=True)


# Document Access Control
class DocumentPermission(Base):
    """Fine-grained document access control"""
    __tablename__ = "document_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    role = Column(SQLEnum(UserRole), nullable=True)  # Permission for entire role
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    meta_info = Column(JSON, nullable=True)


# Session Context (Short-term Memory)
class SessionContext(Base):
    """Stores session-specific context and preferences"""
    __tablename__ = "session_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    preferred_model = Column(String(100), nullable=True)
    context_window_size = Column(Integer, default=10)  # Number of recent messages to include
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1024)
    active_document_ids = Column(JSON, nullable=True)  # List of document IDs in short-term memory
    conversation_summary = Column(Text, nullable=True)  # Auto-generated summary of conversation
    conversation_embedding = Column(Vector(384), nullable=True)  # Embedding of conversation for semantic search
    tags = Column(JSON, nullable=True)  # User-defined tags
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    meta_info = Column(JSON, nullable=True)
