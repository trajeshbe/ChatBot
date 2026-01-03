"""
Database models for dynamic module configuration system.

Enables UI-based configuration for all Tier 2 Domain Verticals and Tier 3 Customer Solutions.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

# Import Base from the existing database models
try:
    from app.models.database_enhanced import Base
except ImportError:
    from app.models.database import Base


class ModuleConfiguration(Base):
    """
    Base configuration for each Tier 2/3 module.

    Stores the primary configuration including LLM models, prompts, parameters,
    thresholds, and scoring weights for each module.
    """
    __tablename__ = "module_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    module_type = Column(String(50), nullable=False, index=True)  # 'tier2_domain_vertical' or 'tier3_customer_solution'
    category = Column(String(100), index=True)  # 'procurement', 'hr_talent', etc.

    # Configuration stored as JSONB
    config = Column(JSONB, nullable=False, default=dict)

    # Metadata
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    is_active = Column(Boolean, default=True, index=True)

    # Version tracking
    current_version = Column(Integer, default=1)

    # Note: Relationships removed to avoid circular dependency issues
    # Queries should use module_name as the join key instead

    def __repr__(self):
        return f"<ModuleConfiguration(module_name='{self.module_name}', type='{self.module_type}', version={self.current_version})>"


class ModuleUserOverride(Base):
    """
    Per-user/customer configuration overrides.

    Allows users to override specific configuration values for A/B testing
    or personalized experiences.
    """
    __tablename__ = "module_user_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    module_name = Column(String(100), nullable=False, index=True)

    # Override configuration (only contains overridden fields)
    overrides = Column(JSONB, nullable=False, default=dict)

    # Metadata
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # A/B Testing support
    variant_name = Column(String(100), index=True)
    experiment_id = Column(UUID(as_uuid=True), index=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<ModuleUserOverride(user_id='{self.user_id}', module='{self.module_name}', variant='{self.variant_name}')>"


class ConfigVersion(Base):
    """
    Version history for configuration changes.

    Provides audit trail and ability to restore previous configurations.
    """
    __tablename__ = "config_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_name = Column(String(100), nullable=False, index=True)
    version = Column(Integer, nullable=False, index=True)

    # Full configuration snapshot at this version
    config = Column(JSONB, nullable=False)

    # Change tracking
    changed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    changed_at = Column(TIMESTAMP, default=func.now(), index=True)
    change_description = Column(Text)

    # Diff from previous version (JSON patch format)
    diff = Column(JSONB)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<ConfigVersion(module='{self.module_name}', version={self.version}, changed_at='{self.changed_at}')>"


class ConfigSchema(Base):
    """
    JSON schemas for validating module configurations.

    Ensures configuration updates are valid and prevents misconfigurations.
    """
    __tablename__ = "config_schemas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schema_name = Column(String(100), nullable=False, unique=True, index=True)
    schema_version = Column(String(20), nullable=False, default='1.0')
    module_type = Column(String(50), index=True)  # NULL = global schema

    # JSON Schema definition
    schema = Column(JSONB, nullable=False)

    # Metadata
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)

    def __repr__(self):
        return f"<ConfigSchema(name='{self.schema_name}', version='{self.schema_version}')>"


class ConfigTemplate(Base):
    """
    Reusable configuration templates for quick module setup.

    Provides pre-configured templates for common use cases and industries.
    """
    __tablename__ = "config_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)

    # Template configuration
    template = Column(JSONB, nullable=False)

    # Categories and tags
    category = Column(String(100), index=True)
    tags = Column(ARRAY(Text), index=True)
    module_type = Column(String(50), index=True)

    # Metadata
    created_at = Column(TIMESTAMP, default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    is_public = Column(Boolean, default=True, index=True)
    usage_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<ConfigTemplate(name='{self.template_name}', category='{self.category}')>"


class ConfigAuditLog(Base):
    """
    Detailed audit trail for all configuration changes.

    Tracks who changed what, when, and why for compliance and debugging.
    """
    __tablename__ = "config_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_name = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)  # 'create', 'update', 'delete', 'override', 'restore'

    # Change details
    changed_field_path = Column(String(255))  # 'llm.model', 'prompts.system.main'
    old_value = Column(JSONB)
    new_value = Column(JSONB)

    # User context
    changed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), index=True)
    changed_at = Column(TIMESTAMP, default=func.now(), index=True)
    ip_address = Column(INET)
    user_agent = Column(Text)

    # Additional context
    change_reason = Column(Text)
    meta_data = Column('metadata', JSONB)  # Mapped to 'metadata' column in DB

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<ConfigAuditLog(module='{self.module_name}', action='{self.action}', changed_at='{self.changed_at}')>"
