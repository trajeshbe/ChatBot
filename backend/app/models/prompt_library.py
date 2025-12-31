"""
Prompt Library and Output Templates Models
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class PromptLibrary(Base):
    """
    Prompt Library - Reusable prompts for common tasks
    """
    __tablename__ = "prompt_library"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    prompt_text = Column(Text, nullable=False)

    # Classification
    prompt_type = Column(String(100), nullable=False)  # entity_extraction, summarization, etc.
    category = Column(String(100))  # business, technical, research, general
    module = Column(String(100))  # chat, scraping, project_estimator, web_scraper, etc.
    tags = Column(JSONB, default=list)  # Flexible categorization

    # Output Configuration
    expected_output_format = Column(String(50), default='text')  # json, markdown, table, list, etc.
    output_schema = Column(JSONB)  # JSON schema for structured outputs

    # Examples
    example_input = Column(Text)
    example_output = Column(Text)

    # Ownership & Visibility
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'))
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id', ondelete='SET NULL'))
    is_public = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # Usage Metrics
    usage_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    # Versioning
    version = Column(Integer, default=1)
    parent_prompt_id = Column(UUID(as_uuid=True), ForeignKey('prompt_library.id', ondelete='SET NULL'))

    # Metadata
    meta_info = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    project = relationship("Project", foreign_keys=[project_id])
    department = relationship("Department", foreign_keys=[department_id])
    ratings = relationship("PromptRating", back_populates="prompt", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PromptLibrary(id={self.id}, name='{self.name}', type='{self.prompt_type}')>"


class PromptRating(Base):
    """
    User ratings for prompts
    """
    __tablename__ = "prompt_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey('prompt_library.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    feedback = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    prompt = relationship("PromptLibrary", back_populates="ratings")
    user = relationship("User")

    def __repr__(self):
        return f"<PromptRating(prompt_id={self.prompt_id}, user_id={self.user_id}, rating={self.rating})>"


class OutputTemplate(Base):
    """
    Output Templates for structured exports
    """
    __tablename__ = "output_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Template Configuration
    template_type = Column(String(50), nullable=False)  # excel, word, ppt, markdown, json, pdf
    template_config = Column(JSONB, nullable=False)  # Structure definition
    template_file_path = Column(String(512))  # Path to template file if using file-based templates

    # Ownership & Visibility
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'))
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id', ondelete='SET NULL'))
    is_public = Column(Boolean, default=False)

    # Usage Metrics
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    # Metadata
    meta_info = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    project = relationship("Project", foreign_keys=[project_id])
    department = relationship("Department", foreign_keys=[department_id])

    def __repr__(self):
        return f"<OutputTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"


class PromptUsageLog(Base):
    """
    Analytics log for prompt usage
    """
    __tablename__ = "prompt_usage_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey('prompt_library.id', ondelete='CASCADE'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id', ondelete='SET NULL'))

    # Usage details
    actual_prompt_used = Column(Text)  # After variable substitution
    input_provided = Column(Text)
    output_generated = Column(Text)

    # Performance
    execution_time_ms = Column(Float)
    token_count = Column(Integer)

    # Outcome
    was_successful = Column(Boolean, default=True)
    error_message = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    prompt = relationship("PromptLibrary")
    user = relationship("User")

    def __repr__(self):
        return f"<PromptUsageLog(prompt_id={self.prompt_id}, user_id={self.user_id})>"
