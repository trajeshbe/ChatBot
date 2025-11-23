"""
Database models for Scraping Configuration & Compliance System
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Boolean, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

# Use the same Base as the main database models
from app.models.database import Base


class ScrapingConfig(Base):
    """Domain-specific scraping configuration and policies"""
    __tablename__ = "scraping_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(255), nullable=False, unique=True, index=True)

    # Compliance settings
    allow_scraping = Column(Boolean, default=False, nullable=False)
    robots_txt_compliant = Column(Boolean, default=True, nullable=False)
    robots_txt_url = Column(String(512), nullable=True)
    robots_txt_checked_at = Column(DateTime(timezone=True), nullable=True)

    # Rate limiting
    rate_limit_enabled = Column(Boolean, default=True, nullable=False)
    rate_limit_requests_per_minute = Column(Integer, default=10)
    rate_limit_delay_seconds = Column(Float, default=2.0)
    max_concurrent_requests = Column(Integer, default=1)

    # API configuration (for sites with official APIs)
    use_api = Column(Boolean, default=False, nullable=False)
    api_endpoint = Column(String(512), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)  # Encrypted API key
    api_documentation_url = Column(String(512), nullable=True)

    # Terms of Service compliance
    terms_checked = Column(Boolean, default=False, nullable=False)
    terms_url = Column(String(512), nullable=True)
    terms_checked_at = Column(DateTime(timezone=True), nullable=True)
    terms_notes = Column(Text, nullable=True)

    # Permission tracking
    permission_granted = Column(Boolean, default=False, nullable=False)
    permission_contact = Column(String(255), nullable=True)  # Email/contact who granted permission
    permission_granted_at = Column(DateTime(timezone=True), nullable=True)
    permission_expires_at = Column(DateTime(timezone=True), nullable=True)
    permission_document_url = Column(String(512), nullable=True)

    # Scraping method preferences
    preferred_method = Column(String(50), default='auto')  # 'api', 'playwright', 'requests', 'auto'
    user_agent = Column(String(512), nullable=True)
    custom_headers = Column(JSON, nullable=True)

    # Notes and metadata
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)

    # Status tracking
    status = Column(String(50), default='active')  # 'active', 'blocked', 'suspended', 'deprecated'
    block_reason = Column(Text, nullable=True)


class ScrapingAuditLog(Base):
    """Audit log for all scraping attempts"""
    __tablename__ = "scraping_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("scraping_configs.id", ondelete="SET NULL"), nullable=True)
    domain = Column(String(255), nullable=False, index=True)
    url = Column(String(1024), nullable=False)

    # Request details
    method = Column(String(50), nullable=True)  # 'api', 'playwright', 'requests'
    user_agent = Column(String(512), nullable=True)

    # Response details
    status_code = Column(Integer, nullable=True)
    success = Column(Boolean, default=False, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    bytes_downloaded = Column(Integer, nullable=True)

    # Compliance tracking
    robots_txt_allowed = Column(Boolean, nullable=True)
    rate_limit_respected = Column(Boolean, nullable=True)
    permission_verified = Column(Boolean, nullable=True)

    # Metadata
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class DomainStatistics(Base):
    """Aggregate scraping statistics per domain"""
    __tablename__ = "domain_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(255), nullable=False, unique=True, index=True)

    # Request counts
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    blocked_requests = Column(Integer, default=0)

    # Traffic stats
    total_bytes_downloaded = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, nullable=True)

    # Rate limiting violations
    rate_limit_violations = Column(Integer, default=0)
    robots_txt_violations = Column(Integer, default=0)

    # Time tracking
    first_scraped_at = Column(DateTime(timezone=True), nullable=True)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
