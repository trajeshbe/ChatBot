"""
Export Wizard Database Models

SQLAlchemy models for the POC Export Wizard system.
Tracks export jobs, packages, and deployment metadata.

Author: Claude Code
Date: 2026-01-03
"""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Integer, JSON, Text, Boolean, Enum as SQLEnum, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.database import Base


class DeploymentType(str, PyEnum):
    """Supported deployment types."""
    DOCKER_COMPOSE = "docker_compose"
    DOCKER_COMPOSE_HA = "docker_compose_ha"
    KUBERNETES = "kubernetes"
    AWS_CLOUDFORMATION = "aws_cloudformation"
    AWS_TERRAFORM = "aws_terraform"
    AZURE_ARM = "azure_arm"
    AZURE_BICEP = "azure_bicep"
    GCP_DEPLOYMENT_MANAGER = "gcp_deployment_manager"
    GCP_TERRAFORM = "gcp_terraform"


class ExportStatus(str, PyEnum):
    """Export job status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LicenseTier(str, PyEnum):
    """License tiers for exported packages."""
    STARTER = "starter"  # $50K/year
    PROFESSIONAL = "professional"  # $100K/year
    ENTERPRISE = "enterprise"  # $250K/year


class ExportJob(Base):
    """
    Export job tracking.

    Tracks the entire export process from initiation to completion.
    """
    __tablename__ = "export_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Job metadata
    job_name = Column(String(255), nullable=False)
    tenant_id = Column(String(255), nullable=False, index=True)
    module_name = Column(String(255), nullable=False)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Export configuration
    deployment_type = Column(SQLEnum(DeploymentType, name="deployment_type", values_callable=lambda x: [e.value for e in x]), nullable=False)
    license_tier = Column(SQLEnum(LicenseTier, name="license_tier", values_callable=lambda x: [e.value for e in x]), nullable=False, default=LicenseTier.PROFESSIONAL)

    # Customer information
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    license_expiry = Column(DateTime, nullable=True)
    max_users = Column(Integer, nullable=True)

    # Export options
    options = Column(JSON, nullable=False, default=dict)
    # {
    #   "include_embeddings": true,
    #   "include_monitoring": true,
    #   "include_backups": true,
    #   "white_label": true,
    #   "custom_branding": {...},
    #   "security_level": "advanced",
    #   "enable_telemetry": false,
    #   "include_source_code": false
    # }

    # Job status
    status = Column(SQLEnum(ExportStatus, name="export_status", values_callable=lambda x: [e.value for e in x]), default=ExportStatus.PENDING, nullable=False, index=True)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    current_step = Column(String(255), nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Results
    export_package_id = Column(UUID(as_uuid=True), ForeignKey('export_packages.id'), nullable=True)
    package_path = Column(Text, nullable=True)
    package_size_bytes = Column(Integer, nullable=True)

    # Statistics
    stats = Column(JSON, nullable=True)
    # {
    #   "documents_exported": 145,
    #   "embeddings_exported": 4500,
    #   "total_chunks": 4500,
    #   "configuration_items": 45,
    #   "processing_time_seconds": 245
    # }

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Audit
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ExportJob(id={self.id}, name={self.job_name}, status={self.status})>"


class ExportPackage(Base):
    """
    Exported package metadata.

    Represents a complete export package ready for customer deployment.
    """
    __tablename__ = "export_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Package metadata
    package_name = Column(String(255), nullable=False, unique=True)
    version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Source information
    tenant_id = Column(String(255), nullable=False, index=True)
    module_name = Column(String(255), nullable=False)
    export_job_id = Column(UUID(as_uuid=True), ForeignKey('export_jobs.id'), nullable=False)

    # Package details
    deployment_type = Column(SQLEnum(DeploymentType, name="deployment_type", values_callable=lambda x: [e.value for e in x]), nullable=False)
    package_path = Column(Text, nullable=False)
    package_size_bytes = Column(Integer, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)

    # Contents manifest
    manifest = Column(JSON, nullable=False)
    # {
    #   "documents": [...],
    #   "embeddings_count": 4500,
    #   "configuration_files": [...],
    #   "infrastructure_files": [...],
    #   "docker_images": [...],
    #   "scripts": [...]
    # }

    # License information
    license_key = Column(Text, nullable=False)  # RSA-4096 signed
    license_tier = Column(SQLEnum(LicenseTier, name="license_tier", values_callable=lambda x: [e.value for e in x]), nullable=False)
    license_issued_at = Column(DateTime, default=datetime.utcnow)
    license_expires_at = Column(DateTime, nullable=True)

    # Customer information
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    max_users = Column(Integer, nullable=True)

    # Download tracking
    download_count = Column(Integer, default=0, nullable=False)
    last_downloaded_at = Column(DateTime, nullable=True)

    # Deployment tracking
    deployed = Column(Boolean, default=False, nullable=False)
    deployment_url = Column(String(512), nullable=True)
    deployed_at = Column(DateTime, nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ["production", "customer-acme", "v1.0"]

    def __repr__(self):
        return f"<ExportPackage(id={self.id}, name={self.package_name}, version={self.version})>"


class ExportTemplate(Base):
    """
    Export templates for common configurations.

    Predefined templates for different use cases and industries.
    """
    __tablename__ = "export_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Template metadata
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # "finance", "healthcare", "retail", etc.

    # Template configuration
    deployment_type = Column(SQLEnum(DeploymentType, name="deployment_type", values_callable=lambda x: [e.value for e in x]), nullable=False)
    license_tier = Column(SQLEnum(LicenseTier, name="license_tier", values_callable=lambda x: [e.value for e in x]), nullable=False)

    # Default options
    default_options = Column(JSON, nullable=False, default=dict)
    # {
    #   "include_embeddings": true,
    #   "include_monitoring": true,
    #   "security_level": "advanced",
    #   "enable_telemetry": false,
    #   ...
    # }

    # Infrastructure settings
    infrastructure_config = Column(JSON, nullable=False, default=dict)
    # {
    #   "replicas": 3,
    #   "resource_limits": {...},
    #   "auto_scaling": {...},
    #   ...
    # }

    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ExportTemplate(id={self.id}, name={self.name})>"


class DeploymentInstance(Base):
    """
    Track deployed instances of exported packages.

    Monitors where packages are deployed and their health status.
    """
    __tablename__ = "deployment_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Instance metadata
    instance_name = Column(String(255), nullable=False)
    export_package_id = Column(UUID(as_uuid=True), ForeignKey('export_packages.id'), nullable=False)

    # Deployment details
    deployment_type = Column(SQLEnum(DeploymentType, name="deployment_type", values_callable=lambda x: [e.value for e in x]), nullable=False)
    deployment_url = Column(String(512), nullable=True)
    environment = Column(String(50), nullable=True)  # "production", "staging", "dev"

    # Infrastructure information
    cloud_provider = Column(String(50), nullable=True)  # "aws", "azure", "gcp", "on-prem"
    region = Column(String(100), nullable=True)
    cluster_info = Column(JSON, nullable=True)

    # Health status
    status = Column(String(50), default="unknown", nullable=False)
    last_health_check = Column(DateTime, nullable=True)
    health_data = Column(JSON, nullable=True)
    # {
    #   "api_healthy": true,
    #   "database_healthy": true,
    #   "vector_db_healthy": true,
    #   "uptime_seconds": 345600,
    #   "version": "1.0.0"
    # }

    # Telemetry (if enabled)
    telemetry_enabled = Column(Boolean, default=False, nullable=False)
    telemetry_data = Column(JSON, nullable=True)
    # {
    #   "total_queries": 15420,
    #   "active_users": 45,
    #   "avg_response_time_ms": 342,
    #   "error_rate": 0.02
    # }

    # Timing
    deployed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, nullable=True)
    decommissioned_at = Column(DateTime, nullable=True)

    # Contact
    contact_email = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<DeploymentInstance(id={self.id}, name={self.instance_name}, status={self.status})>"


class ExportAuditLog(Base):
    """
    Audit log for export wizard operations.

    Tracks all significant events in the export lifecycle.
    """
    __tablename__ = "export_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Event metadata
    event_type = Column(String(100), nullable=False, index=True)
    # "export_initiated", "export_completed", "export_failed",
    # "package_downloaded", "deployment_created", etc.

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Related entities
    export_job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    export_package_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    deployment_instance_id = Column(UUID(as_uuid=True), nullable=True)

    # User information
    user_id = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Event details
    details = Column(JSON, nullable=True)
    # {
    #   "action": "initiated_export",
    #   "module": "british_council",
    #   "deployment_type": "kubernetes",
    #   "options": {...}
    # }

    # Status
    status = Column(String(50), nullable=False)  # "success", "failure", "warning"
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ExportAuditLog(id={self.id}, event={self.event_type}, timestamp={self.timestamp})>"
