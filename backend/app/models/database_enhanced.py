"""
Enhanced database models for RBAC, Sessions, and Audit Logging
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Boolean, Float, JSON, Enum as SQLEnum, UniqueConstraint
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
    """Types of auditable actions - comprehensive coverage"""
    # Authentication & Session
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    SESSION_CREATE = "session_create"
    SESSION_DESTROY = "session_destroy"
    SESSION_TIMEOUT = "session_timeout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # Data Operations
    QUERY = "query"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    SCRAPE = "scrape"
    DELETE = "delete"
    CREATE = "create"
    UPDATE = "update"
    VIEW = "view"
    EXPORT = "export"

    # Module Access
    MODULE_ACCESS = "module_access"
    MODULE_EXIT = "module_exit"
    FEATURE_USAGE = "feature_usage"

    # Admin Operations
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_ASSIGN = "role_assign"
    ROLE_REVOKE = "role_revoke"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_DENY = "permission_deny"
    SETTINGS_CHANGE = "settings_change"

    # File Operations
    FILE_DELETE = "file_delete"
    FILE_MOVE = "file_move"
    FILE_SHARE = "file_share"

    # Project Operations
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    PROJECT_ARCHIVE = "project_archive"

    # API Operations
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    API_REQUEST = "api_request"

    # Errors & Security
    ERROR = "error"
    PERMISSION_DENIED = "permission_denied"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


# User and RBAC Models
class User(Base):
    """User accounts with RBAC"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    meta_info = Column(JSON, nullable=True)

    # Default project for uploads (set after project creation)
    default_project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True
    )

    # Organizational fields
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    function = Column(String(100), nullable=True, index=True)  # Job function/title from predefined list


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
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
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

    # Suppress Pydantic v2 warning about model_ field names
    __pydantic_config__ = {"protected_namespaces": ()}

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
    action = Column(SQLEnum(ActionType, name="action_type", values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
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

    # Suppress Pydantic v2 warning about model_ field names
    __pydantic_config__ = {"protected_namespaces": ()}

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
    role = Column(SQLEnum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]), nullable=True)  # Permission for entire role
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


# Evaluation System Models
class EvaluationConfig(Base):
    """User-specific evaluation configuration (toggleable metrics)"""
    __tablename__ = "evaluation_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=True)

    # Toggle switches for evaluation methods
    enable_ragas = Column(Boolean, default=False)
    enable_llm_as_judge = Column(Boolean, default=False)
    enable_deepeval = Column(Boolean, default=False)
    enable_semantic_similarity = Column(Boolean, default=False)
    enable_bertscore = Column(Boolean, default=False)
    enable_citation_accuracy = Column(Boolean, default=True)
    enable_toxicity = Column(Boolean, default=True)
    enable_bias_detection = Column(Boolean, default=True)
    enable_hallucination = Column(Boolean, default=True)
    enable_answer_relevancy = Column(Boolean, default=True)
    enable_context_precision = Column(Boolean, default=False)
    enable_context_recall = Column(Boolean, default=False)
    enable_faithfulness = Column(Boolean, default=True)

    # Configuration parameters
    llm_judge_model = Column(String(100), default="gpt-4-turbo-preview")
    use_cache = Column(Boolean, default=True)
    async_evaluation = Column(Boolean, default=True)
    batch_size = Column(Integer, default=10)
    min_score_threshold = Column(Float, default=0.7)
    cache_ttl_seconds = Column(Integer, default=3600)

    # Auto-evaluation settings
    auto_evaluate = Column(Boolean, default=False)  # Automatically evaluate all responses
    evaluation_sampling_rate = Column(Float, default=1.0)  # % of queries to evaluate (0.0-1.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    meta_info = Column(JSON, nullable=True)


class EvaluationResult(Base):
    """Stores evaluation results for RAG responses"""
    __tablename__ = "evaluation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Query and response data
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    num_contexts = Column(Integer, nullable=True)

    # Individual evaluation scores (JSON format for flexibility)
    scores = Column(JSON, nullable=False)  # All evaluation method scores
    overall_score = Column(Float, nullable=True, index=True)  # Weighted average score

    # Performance metrics
    evaluation_time_ms = Column(Float, nullable=True)
    enabled_methods = Column(JSON, nullable=True)  # List of methods that were enabled

    # Metadata
    meta_info = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)  # Any evaluation errors

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class EvaluationCache(Base):
    """Cache for evaluation results to improve performance"""
    __tablename__ = "evaluation_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    result = Column(JSON, nullable=False)
    ttl_seconds = Column(Integer, default=3600)
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class HumanFeedback(Base):
    """Human feedback on RAG responses for evaluation improvement"""
    __tablename__ = "human_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages.id", ondelete="CASCADE"), nullable=True)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_results.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Feedback data
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    thumbs_up = Column(Boolean, nullable=True)  # Simple thumbs up/down
    feedback_text = Column(Text, nullable=True)  # Detailed feedback

    # Specific criteria ratings
    accuracy_rating = Column(Integer, nullable=True)
    helpfulness_rating = Column(Integer, nullable=True)
    clarity_rating = Column(Integer, nullable=True)

    # Issues flagged
    has_hallucination = Column(Boolean, default=False)
    has_bias = Column(Boolean, default=False)
    has_toxicity = Column(Boolean, default=False)
    is_irrelevant = Column(Boolean, default=False)

    # Metadata
    feedback_type = Column(String(50), nullable=True)  # 'inline', 'survey', 'detailed'
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_info = Column(JSON, nullable=True)


class EvaluationMetricsBenchmark(Base):
    """Benchmark dataset for evaluation metrics validation"""
    __tablename__ = "evaluation_benchmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Benchmark data
    query = Column(Text, nullable=False)
    ground_truth_answer = Column(Text, nullable=False)
    context_chunks = Column(JSON, nullable=False)  # List of context chunks

    # Expected scores (for validation)
    expected_scores = Column(JSON, nullable=True)

    # Benchmark metadata
    dataset_name = Column(String(100), nullable=True, index=True)  # e.g., "MS-MARCO", "HotpotQA"
    difficulty = Column(String(50), nullable=True)  # 'easy', 'medium', 'hard'
    category = Column(String(100), nullable=True)  # Domain category

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_info = Column(JSON, nullable=True)


# API Credentials Management (Secrets Management)
class APICredential(Base):
    """Encrypted storage for LLM provider API keys"""
    __tablename__ = "api_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), unique=True, nullable=False, index=True)  # 'openai', 'anthropic', 'huggingface'
    api_key_encrypted = Column(Text, nullable=False)  # Fernet-encrypted API key
    encryption_key_id = Column(String(100), nullable=True)  # For key rotation tracking
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    meta_info = Column(JSON, nullable=True)


class APIKeyAccessLog(Base):
    """Audit log for API key access and modifications"""
    __tablename__ = "api_key_access_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False, index=True)  # 'created', 'updated', 'accessed', 'deleted', 'validated'
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    meta_info = Column(JSON, nullable=True)


# ============================================================================
# NOTE: RBAC Models (Module, Role, RoleModulePermission, UserRole) are now
# defined in app/models/rbac.py to avoid table definition conflicts.
# Import from there if you need RBAC models.
# ============================================================================


# Project Management
class Project(Base):
    """Projects for organizing files and work"""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Organizational hierarchy (proper foreign keys for MinIO path construction)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)  # Deprecated - use department_id instead

    status = Column(String(50), default='active')  # 'active', 'archived', 'completed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True)
    meta_info = Column(JSON, nullable=True)


class ProjectMember(Base):
    """Project team members"""
    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default='member')  # 'owner', 'admin', 'member', 'viewer'
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_info = Column(JSON, nullable=True)


class UserTeam(Base):
    """User to Team many-to-many junction table"""
    __tablename__ = "user_teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_primary = Column(Boolean, default=False)  # One team can be marked as primary

    __table_args__ = (
        UniqueConstraint('user_id', 'team_id', name='uq_user_team'),
    )
