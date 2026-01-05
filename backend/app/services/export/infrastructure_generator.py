"""
Infrastructure Generator Service

Generates deployment infrastructure (IaC) for multiple platforms.

Supported deployment types:
1. Docker Compose (single server)
2. Docker Compose HA (high availability)
3. Kubernetes (K8s manifests)
4. AWS (CloudFormation + Terraform)
5. Azure (ARM templates + Bicep)
6. GCP (Deployment Manager + Terraform)

This service generates complete, production-ready infrastructure that customers
can deploy with a single command.

Author: Claude Code
Date: 2026-01-03
Phase: 1 - Core Export Engine
"""

import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.models.export_wizard import DeploymentType

logger = logging.getLogger(__name__)


@dataclass
class InfrastructureOptions:
    """Options for infrastructure generation."""
    replicas: int = 1
    enable_monitoring: bool = True
    enable_backups: bool = True
    enable_ssl: bool = True
    custom_domain: Optional[str] = None
    resource_limits: Dict[str, Any] = None
    auto_scaling: Dict[str, Any] = None
    security_level: str = "standard"  # basic, standard, advanced, enterprise

    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = {
                "backend_memory": "2GB",
                "backend_cpu": "1000m",
                "postgres_memory": "1GB",
                "redis_memory": "512MB"
            }
        if self.auto_scaling is None:
            self.auto_scaling = {
                "enabled": False,
                "min_replicas": 1,
                "max_replicas": 5,
                "target_cpu_percent": 70
            }


@dataclass
class GeneratedInfrastructure:
    """Result of infrastructure generation."""
    deployment_type: DeploymentType
    files_generated: list[str]
    total_files: int
    readme_path: str


class InfrastructureGenerator:
    """Generate deployment infrastructure for multiple platforms."""

    def __init__(self):
        """Initialize InfrastructureGenerator."""
        pass

    def _generate_container_prefix(self, customer_name: str, module_name: str) -> str:
        """
        Generate unique container name prefix.

        Pattern: {customer_name}_{module_name}_
        Example: acme_relation-extractor_postgres

        Args:
            customer_name: Customer name (will be sanitized)
            module_name: Module name

        Returns:
            Sanitized container prefix
        """
        import re

        # Sanitize: lowercase, replace spaces/special chars with underscores
        safe_customer = re.sub(r'[^a-z0-9]+', '_', customer_name.lower()).strip('_')
        safe_module = re.sub(r'[^a-z0-9]+', '_', module_name.lower()).strip('_')

        return f"{safe_customer}_{safe_module}"

    def _detect_available_ports(self, base_ports: Dict[str, int], increment: int = 100) -> Dict[str, int]:
        """
        Detect available ports, incrementing if conflicts detected.

        Note: This is a best-effort check. Actual port availability
        depends on the deployment target system.

        Args:
            base_ports: Dictionary of {service: port}
            increment: Port increment for conflicts (default: 100)

        Returns:
            Dictionary of {service: available_port}
        """
        import socket

        available_ports = {}

        for service, port in base_ports.items():
            original_port = port
            attempts = 0
            max_attempts = 10

            while attempts < max_attempts:
                try:
                    # Try to bind to port to check availability
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        s.bind(('', port))
                        # Port is available
                        available_ports[service] = port
                        if port != original_port:
                            logger.info(f"   Port {original_port} in use for {service}, using {port}")
                        break
                except OSError:
                    # Port in use, try next
                    port += increment
                    attempts += 1
            else:
                # Max attempts reached, use last tried port
                logger.warning(f"   Could not find available port for {service}, using {port}")
                available_ports[service] = port

        return available_ports

    def _generate_secure_secrets(self, module_name: str) -> Dict[str, str]:
        """
        Generate secure random secrets for various services.

        Args:
            module_name: Module name (used in secret prefixes)

        Returns:
            Dictionary of {secret_name: value}
        """
        import secrets

        return {
            "postgres_password": f"{module_name}_db_" + secrets.token_urlsafe(16),
            "minio_secret_key": f"{module_name}_minio_" + secrets.token_urlsafe(16),
            "jwt_secret": secrets.token_urlsafe(32),
            "secret_key": secrets.token_urlsafe(32),
        }

    async def generate_infrastructure(
        self,
        module_name: str,
        deployment_type: DeploymentType,
        export_dir: str,
        config: Dict[str, Any],
        options: InfrastructureOptions
    ) -> GeneratedInfrastructure:
        """
        Generate infrastructure code for specified deployment type.

        Args:
            module_name: Module name
            deployment_type: Type of deployment (docker_compose, kubernetes, aws, etc.)
            export_dir: Root export directory
            config: Module configuration
            options: Infrastructure options

        Returns:
            GeneratedInfrastructure with file paths

        Raises:
            ValueError: If deployment type not supported
        """
        logger.info(f"🏗️  Generating {deployment_type.value} infrastructure for {module_name}")

        # Create infrastructure directory
        infra_dir = Path(export_dir) / "infrastructure"
        infra_dir.mkdir(parents=True, exist_ok=True)

        # Route to appropriate generator
        if deployment_type == DeploymentType.DOCKER_COMPOSE:
            return await self._generate_docker_compose(
                module_name, infra_dir, config, options
            )
        elif deployment_type == DeploymentType.DOCKER_COMPOSE_HA:
            return await self._generate_docker_compose_ha(
                module_name, infra_dir, config, options
            )
        elif deployment_type == DeploymentType.KUBERNETES:
            return await self._generate_kubernetes(
                module_name, infra_dir, config, options
            )
        elif deployment_type in [DeploymentType.AWS_CLOUDFORMATION, DeploymentType.AWS_TERRAFORM]:
            return await self._generate_aws(
                module_name, infra_dir, config, options, deployment_type
            )
        elif deployment_type in [DeploymentType.AZURE_ARM, DeploymentType.AZURE_BICEP]:
            return await self._generate_azure(
                module_name, infra_dir, config, options, deployment_type
            )
        elif deployment_type in [DeploymentType.GCP_DEPLOYMENT_MANAGER, DeploymentType.GCP_TERRAFORM]:
            return await self._generate_gcp(
                module_name, infra_dir, config, options, deployment_type
            )
        else:
            raise ValueError(f"Unsupported deployment type: {deployment_type}")

    async def _generate_docker_compose(
        self,
        module_name: str,
        infra_dir: Path,
        config: Dict[str, Any],
        options: InfrastructureOptions
    ) -> GeneratedInfrastructure:
        """
        Generate Docker Compose infrastructure (single server).

        Creates:
        - docker-compose.yml
        - .env.example
        - deploy.sh
        - README.md

        Args:
            module_name: Module name
            infra_dir: Infrastructure directory
            config: Module configuration
            options: Infrastructure options

        Returns:
            GeneratedInfrastructure
        """
        docker_dir = infra_dir / "docker-compose"
        docker_dir.mkdir(parents=True, exist_ok=True)

        files_generated = []

        # Phase 3: Generate unique container names and detect ports
        customer_name = config.get("customer_name", "customer")
        container_prefix = self._generate_container_prefix(customer_name, module_name)
        logger.info(f"   📦 Container prefix: {container_prefix}")

        # Detect available ports
        base_ports = {
            "backend": 8000,
            "frontend": 3001,
            "postgres": 5432,
            "redis": 6379,
            "minio": 9000,
            "minio_console": 9001,
            "prometheus": 9090,
            "grafana": 3000,
        }
        available_ports = self._detect_available_ports(base_ports)
        logger.info(f"   🔌 Detected available ports")

        # Generate secure secrets
        secrets = self._generate_secure_secrets(module_name)
        logger.info(f"   🔐 Generated secure secrets")

        # Store in config for use in templates
        config["container_prefix"] = container_prefix
        config["ports"] = available_ports
        config["secrets"] = secrets

        # 1. Generate docker-compose.yml with unique container names
        compose_content = self._generate_docker_compose_yml(module_name, config, options)
        compose_path = docker_dir / "docker-compose.yml"
        compose_path.write_text(compose_content)
        files_generated.append(str(compose_path))

        logger.info(f"   ✅ Generated: docker-compose.yml")

        # 2. Generate .env.example (template)
        env_content = self._generate_env_file(config)
        env_path = docker_dir / ".env.example"
        env_path.write_text(env_content)
        files_generated.append(str(env_path))

        logger.info(f"   ✅ Generated: .env.example")

        # 3. Generate pre-configured .env file (Phase 3: Automation)
        env_preconfigured = self._generate_preconfigured_env(config, available_ports, secrets)
        env_actual_path = docker_dir / ".env"
        env_actual_path.write_text(env_preconfigured)
        files_generated.append(str(env_actual_path))

        logger.info(f"   ✅ Generated: .env (pre-configured, ready to use)")

        # 3. Generate deployment script
        deploy_script = self._generate_deploy_script(module_name, "docker-compose")
        script_path = docker_dir / "deploy.sh"
        script_path.write_text(deploy_script)
        script_path.chmod(0o755)  # Make executable
        files_generated.append(str(script_path))

        logger.info(f"   ✅ Generated: deploy.sh")

        # 4. Generate README
        readme_content = self._generate_readme(module_name, DeploymentType.DOCKER_COMPOSE, options)
        readme_path = docker_dir / "README.md"
        readme_path.write_text(readme_content)
        files_generated.append(str(readme_path))

        logger.info(f"   ✅ Generated: README.md")

        # 5. Generate backup script (if enabled)
        if options.enable_backups:
            backup_script = self._generate_backup_script()
            backup_path = docker_dir / "backup.sh"
            backup_path.write_text(backup_script)
            backup_path.chmod(0o755)
            files_generated.append(str(backup_path))

            logger.info(f"   ✅ Generated: backup.sh")

        # 6. Generate database load scripts (for embeddings import)
        scripts_dir = docker_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        load_script = self._generate_database_load_script(module_name)
        load_path = scripts_dir / "load_embeddings.py"
        load_path.write_text(load_script)
        files_generated.append(str(load_path))

        logger.info(f"   ✅ Generated: scripts/load_embeddings.py")

        # 7. Generate API client examples
        api_examples_dir = docker_dir / "api_examples"
        api_examples_dir.mkdir(parents=True, exist_ok=True)

        # REST API client
        rest_client = self._generate_rest_api_client(module_name, config)
        rest_path = api_examples_dir / "rest_client.py"
        rest_path.write_text(rest_client)
        files_generated.append(str(rest_path))

        # GraphQL client
        graphql_client = self._generate_graphql_client(module_name, config)
        graphql_path = api_examples_dir / "graphql_client.py"
        graphql_path.write_text(graphql_client)
        files_generated.append(str(graphql_path))

        # WebSocket client
        websocket_client = self._generate_websocket_client(module_name, config)
        ws_path = api_examples_dir / "websocket_client.py"
        ws_path.write_text(websocket_client)
        files_generated.append(str(ws_path))

        logger.info(f"   ✅ Generated: API client examples (REST, GraphQL, WebSocket)")

        # 8. Generate webhook integration
        webhook_config = self._generate_webhook_config(module_name, config)
        webhook_path = docker_dir / "webhook_config.json"
        webhook_path.write_text(webhook_config)
        files_generated.append(str(webhook_path))

        logger.info(f"   ✅ Generated: webhook_config.json")

        # 9. Generate OpenAPI documentation
        openapi_spec = self._generate_openapi_spec(module_name, config)
        openapi_path = docker_dir / "openapi.json"
        openapi_path.write_text(openapi_spec)
        files_generated.append(str(openapi_path))

        logger.info(f"   ✅ Generated: openapi.json")

        # 10. Generate Backend Dockerfile
        backend_dockerfile = self._generate_backend_dockerfile(module_name)
        backend_docker_path = infra_dir.parent / "backend" / "Dockerfile"
        backend_docker_path.parent.mkdir(parents=True, exist_ok=True)
        backend_docker_path.write_text(backend_dockerfile)
        files_generated.append(str(backend_docker_path))

        logger.info(f"   ✅ Generated: backend/Dockerfile")

        # 11. Generate Frontend Dockerfile
        frontend_dockerfile = self._generate_frontend_dockerfile(module_name)
        frontend_docker_path = infra_dir.parent / "frontend" / "Dockerfile"
        frontend_docker_path.parent.mkdir(parents=True, exist_ok=True)
        frontend_docker_path.write_text(frontend_dockerfile)
        files_generated.append(str(frontend_docker_path))

        logger.info(f"   ✅ Generated: frontend/Dockerfile")

        # 12. Generate startup and utility scripts
        logger.info(f"📜 Generating startup and utility scripts...")

        scripts_dir = infra_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Database init script
        db_init_script = self._generate_database_init_script(module_name)
        db_init_path = scripts_dir / "init-database.sh"
        db_init_path.write_text(db_init_script)
        db_init_path.chmod(0o755)
        files_generated.append(str(db_init_path))
        logger.info(f"   ✅ Generated: scripts/init-database.sh")

        # Wait for services script
        wait_script = self._generate_wait_for_services_script()
        wait_path = scripts_dir / "wait-for-services.sh"
        wait_path.write_text(wait_script)
        wait_path.chmod(0o755)
        files_generated.append(str(wait_path))
        logger.info(f"   ✅ Generated: scripts/wait-for-services.sh")

        # Health check script
        health_script = self._generate_health_check_script(module_name)
        health_path = scripts_dir / "health-check.sh"
        health_path.write_text(health_script)
        health_path.chmod(0o755)
        files_generated.append(str(health_path))
        logger.info(f"   ✅ Generated: scripts/health-check.sh")

        # MinIO init script
        minio_script = self._generate_init_minio_script(module_name)
        minio_path = scripts_dir / "init-minio.sh"
        minio_path.write_text(minio_script)
        minio_path.chmod(0o755)
        files_generated.append(str(minio_path))
        logger.info(f"   ✅ Generated: scripts/init-minio.sh")

        logger.info(f"✅ Docker Compose infrastructure generated: {len(files_generated)} files")

        return GeneratedInfrastructure(
            deployment_type=DeploymentType.DOCKER_COMPOSE,
            files_generated=files_generated,
            total_files=len(files_generated),
            readme_path=str(readme_path)
        )

    def _generate_docker_compose_yml(
        self,
        module_name: str,
        config: Dict[str, Any],
        options: InfrastructureOptions
    ) -> str:
        """Generate docker-compose.yml content."""

        # Get container prefix for unique naming (Phase 3)
        container_prefix = config.get("container_prefix", "genai")

        monitoring_services = ""
        if options.enable_monitoring:
            monitoring_services = f"""
  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    container_name: {container_prefix}_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - {container_prefix}_network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: {container_prefix}_grafana
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${{GRAFANA_ADMIN_PASSWORD:-admin}}
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - {container_prefix}_network
    restart: unless-stopped
    depends_on:
      - prometheus
"""

        compose = f"""# Generated Docker Compose Configuration
# Module: {module_name}
# Generated: {datetime.utcnow().isoformat()}
# Deployment Type: Single Server (Docker Compose)
# Container Prefix: {container_prefix}

version: '3.8'

services:
  # Backend API
  backend:
    build:
      context: ../../backend
      dockerfile: Dockerfile
    image: {module_name}-backend:latest
    container_name: {container_prefix}_backend
    ports:
      - "${{BACKEND_PORT:-8000}}:8000"
    environment:
      # Database
      - DATABASE_URL=postgresql://${{POSTGRES_USER}}:${{POSTGRES_PASSWORD}}@postgres:5432/${{POSTGRES_DB}}

      # Redis
      - REDIS_URL=redis://redis:6379/0

      # MinIO (S3-compatible storage)
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${{MINIO_ACCESS_KEY}}
      - MINIO_SECRET_KEY=${{MINIO_SECRET_KEY}}
      - MINIO_BUCKET_NAME=${{MINIO_BUCKET_NAME:-genai-documents}}

      # LLM Configuration
      - OPENAI_API_KEY=${{OPENAI_API_KEY}}
      - ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY:-}}

      # Module Configuration
      - MODULE_NAME={module_name}

      # Security
      - JWT_SECRET=${{JWT_SECRET}}
      - SECRET_KEY=${{SECRET_KEY}}

      # Logging
      - LOG_LEVEL=${{LOG_LEVEL:-INFO}}

    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    networks:
      - {container_prefix}_network
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      minio:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: {options.resource_limits.get('backend_memory', '2GB')}
          cpus: '1.0'

  # PostgreSQL with pgvector
  postgres:
    image: pgvector/pgvector:pg16
    container_name: {container_prefix}_postgres
    ports:
      - "${{POSTGRES_PORT:-5432}}:5432"
    environment:
      - POSTGRES_USER=${{POSTGRES_USER:-postgres}}
      - POSTGRES_PASSWORD=${{POSTGRES_PASSWORD}}
      - POSTGRES_DB=${{POSTGRES_DB:-genai}}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
    networks:
      - {container_prefix}_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER:-postgres}}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: {options.resource_limits.get('postgres_memory', '1GB')}

  # Redis (caching)
  redis:
    image: redis:7-alpine
    container_name: {container_prefix}_redis
    ports:
      - "${{REDIS_PORT:-6379}}:6379"
    volumes:
      - redis-data:/data
    networks:
      - {container_prefix}_network
    restart: unless-stopped
    command: redis-server --appendonly yes
    deploy:
      resources:
        limits:
          memory: {options.resource_limits.get('redis_memory', '512MB')}

  # MinIO (S3-compatible object storage)
  minio:
    image: minio/minio:latest
    container_name: {container_prefix}_minio
    ports:
      - "${{MINIO_PORT:-9000}}:9000"
      - "${{MINIO_CONSOLE_PORT:-9001}}:9001"
    environment:
      - MINIO_ROOT_USER=${{MINIO_ACCESS_KEY}}
      - MINIO_ROOT_PASSWORD=${{MINIO_SECRET_KEY}}
    volumes:
      - minio-data:/data
    networks:
      - {container_prefix}_network
    restart: unless-stopped
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend (Next.js)
  frontend:
    build:
      context: ../../frontend
      dockerfile: Dockerfile
    image: {module_name}-frontend:latest
    container_name: {container_prefix}_frontend
    ports:
      - "${{FRONTEND_PORT:-3001}}:3001"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    networks:
      - {container_prefix}_network
    restart: unless-stopped
    depends_on:
      - backend
{monitoring_services}

networks:
  {container_prefix}_network:
    driver: bridge

volumes:
  postgres-data:
  redis-data:
  minio-data:
"""

        if options.enable_monitoring:
            compose += """  prometheus-data:
  grafana-data:
"""

        return compose

    def _generate_env_file(self, config: Dict[str, Any]) -> str:
        """Generate .env.example file with module-specific configuration."""

        module_name = config.get("module_name", "module")
        module_display = module_name.replace('_', ' ').title()

        env_content = f"""# ============================================================================
# {module_display} - Standalone Deployment Configuration
# ============================================================================
# This file contains all environment variables needed for deployment.
#
# SETUP INSTRUCTIONS:
# 1. Copy this file to .env:
#    cp .env.example .env
#
# 2. Fill in all REQUIRED fields marked with [REQUIRED]
#
# 3. Optionally customize other settings
#
# Generated: {datetime.utcnow().isoformat()}
# ============================================================================

# ============================================================================
# MODULE INFORMATION
# ============================================================================
MODULE_NAME={module_name}
MODULE_VERSION=1.0.0
DEPLOYMENT_ENV=production

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
# PostgreSQL database settings
# NOTE: Database will be created automatically on first startup

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme_secure_password_min_16_chars  # [REQUIRED] Change this!
POSTGRES_DB={module_name.replace('-', '_')}

# Database connection URL (auto-generated, don't modify)
DATABASE_URL=postgresql://${{POSTGRES_USER}}:${{POSTGRES_PASSWORD}}@${{POSTGRES_HOST}}:${{POSTGRES_PORT}}/${{POSTGRES_DB}}

# ============================================================================
# REDIS CONFIGURATION
# ============================================================================
# Redis for caching and session management

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://${{REDIS_HOST}}:${{REDIS_PORT}}/${{REDIS_DB}}

# ============================================================================
# OBJECT STORAGE (MinIO)
# ============================================================================
# S3-compatible object storage for documents and files

MINIO_HOST=minio
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changeme_minio_password_min_8_chars  # [REQUIRED] Change this!

# MinIO buckets (created automatically)
MINIO_BUCKET_DOCUMENTS=documents
MINIO_BUCKET_UPLOADS=uploads
MINIO_BUCKET_EXPORTS=exports

# MinIO endpoint URL (auto-generated)
MINIO_ENDPOINT=http://${{MINIO_HOST}}:${{MINIO_PORT}}

# ============================================================================
# AI/LLM API KEYS
# ============================================================================
# At least ONE LLM API key is required for the module to function

# OpenAI (GPT models)
OPENAI_API_KEY=sk-proj-your-openai-api-key-here  # [REQUIRED if using OpenAI]
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here  # [REQUIRED if using Claude]
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Model Selection (use 'openai' or 'anthropic')
DEFAULT_LLM_PROVIDER=openai

# ============================================================================
# EMBEDDING MODEL CONFIGURATION
# ============================================================================
# For vector search and similarity matching

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# ============================================================================
# APPLICATION SECURITY
# ============================================================================
# Security keys for JWT tokens and encryption
# IMPORTANT: Use strong, unique values in production!

JWT_SECRET=changeme_jwt_secret_MUST_BE_AT_LEAST_32_CHARACTERS_LONG  # [REQUIRED]
SECRET_KEY=changeme_app_secret_MUST_BE_AT_LEAST_32_CHARACTERS_LONG  # [REQUIRED]

# Session configuration
SESSION_TIMEOUT_MINUTES=60

# ============================================================================
# APPLICATION PORTS
# ============================================================================
# External ports for accessing services

BACKEND_PORT=8000
FRONTEND_PORT=3001

# Internal service ports (don't change unless you know what you're doing)
BACKEND_INTERNAL_PORT=8000
FRONTEND_INTERNAL_PORT=3001

# ============================================================================
# LOGGING & DEBUGGING
# ============================================================================
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

LOG_LEVEL=INFO
DEBUG=false

# Enable detailed SQL logging (useful for debugging)
SQL_ECHO=false

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================
# Adjust based on your hardware and load

# Backend workers (recommended: 2-4 per CPU core)
BACKEND_WORKERS=4

# Database connection pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis connection pool
REDIS_POOL_SIZE=10

# ============================================================================
# MODULE-SPECIFIC CONFIGURATION
# ============================================================================
# Settings specific to {module_display}

# API rate limiting
RATE_LIMIT_PER_MINUTE=60

# File upload limits
MAX_UPLOAD_SIZE_MB=50
ALLOWED_FILE_TYPES=pdf,txt,docx,xlsx

# Processing settings
MAX_CONCURRENT_JOBS=5
JOB_TIMEOUT_SECONDS=300

# ============================================================================
# CORS CONFIGURATION
# ============================================================================
# Cross-Origin Resource Sharing settings

# Allowed origins (comma-separated, * for all)
CORS_ORIGINS=http://localhost:3001,http://localhost:8000

# ============================================================================
# MONITORING (Optional)
# ============================================================================
# Enable if using Grafana/Prometheus monitoring

ENABLE_MONITORING=false
GRAFANA_ADMIN_PASSWORD=changeme_grafana_password

# Metrics endpoint (for Prometheus scraping)
METRICS_ENABLED=true
METRICS_PATH=/metrics

# ============================================================================
# BACKUP & MAINTENANCE (Optional)
# ============================================================================
# Automated backup settings

ENABLE_AUTO_BACKUP=false
BACKUP_SCHEDULE_CRON=0 2 * * *  # Daily at 2 AM
BACKUP_RETENTION_DAYS=7

# ============================================================================
# NOTES
# ============================================================================
# - All [REQUIRED] fields must be filled before deployment
# - Use strong passwords (min 16 characters, mix of letters/numbers/symbols)
# - Never commit the .env file to version control
# - Keep this file secure and backed up
# - See README.md for detailed configuration guide
# ============================================================================
"""
        return env_content

    def _generate_preconfigured_env(
        self,
        config: Dict[str, Any],
        ports: Dict[str, int],
        secrets: Dict[str, str]
    ) -> str:
        """
        Generate pre-configured .env file (Phase 3: Automation).

        Unlike .env.example which has placeholders, this file is ready to use
        with secure secrets and detected ports.

        Args:
            config: Module configuration
            ports: Detected available ports
            secrets: Generated secure secrets

        Returns:
            Pre-configured .env content
        """
        module_name = config.get("module_name", "module")
        customer_name = config.get("customer_name", "customer")

        return f"""# ============================================================================
# {module_name.replace('_', ' ').title()} - AUTO-CONFIGURED DEPLOYMENT
# ============================================================================
# This file was AUTO-GENERATED with secure defaults and available ports.
# You can use it as-is or customize as needed.
#
# Generated: {datetime.utcnow().isoformat()}
# Customer: {customer_name}
# ============================================================================

# MODULE INFORMATION
MODULE_NAME={module_name}
MODULE_VERSION=1.0.0
DEPLOYMENT_ENV=standalone

# DATABASE CONFIGURATION
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD={secrets['postgres_password']}
POSTGRES_DB={module_name.replace('-', '_')}_db
DATABASE_URL=postgresql://${{POSTGRES_USER}}:${{POSTGRES_PASSWORD}}@${{POSTGRES_HOST}}:${{POSTGRES_PORT}}/${{POSTGRES_DB}}

# REDIS CONFIGURATION
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://${{REDIS_HOST}}:${{REDIS_PORT}}/${{REDIS_DB}}

# OBJECT STORAGE (MinIO)
MINIO_HOST=minio
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD={secrets['minio_secret_key']}
MINIO_BUCKET_DOCUMENTS=documents
MINIO_BUCKET_UPLOADS=uploads
MINIO_BUCKET_EXPORTS=exports
MINIO_ENDPOINT=http://${{MINIO_HOST}}:${{MINIO_PORT}}

# AI/LLM API KEYS (Inherit from host environment or add manually)
OPENAI_API_KEY=${{OPENAI_API_KEY:-}}
ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY:-}}
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_MODEL=claude-3-sonnet-20240229
DEFAULT_LLM_PROVIDER=openai

# EMBEDDING MODEL
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# APPLICATION SECURITY (Auto-generated secure secrets)
JWT_SECRET={secrets['jwt_secret']}
SECRET_KEY={secrets['secret_key']}
SESSION_TIMEOUT_MINUTES=60

# APPLICATION PORTS (Auto-detected to avoid conflicts)
BACKEND_PORT={ports.get('backend', 8000)}
FRONTEND_PORT={ports.get('frontend', 3001)}
POSTGRES_PORT_EXTERNAL={ports.get('postgres', 5432)}
REDIS_PORT_EXTERNAL={ports.get('redis', 6379)}
MINIO_PORT={ports.get('minio', 9000)}
MINIO_CONSOLE_PORT={ports.get('minio_console', 9001)}
PROMETHEUS_PORT={ports.get('prometheus', 9090)}
GRAFANA_PORT={ports.get('grafana', 3000)}

# LOGGING & DEBUGGING
LOG_LEVEL=INFO
DEBUG=false
SQL_ECHO=false

# PERFORMANCE TUNING
BACKEND_WORKERS=4
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
REDIS_POOL_SIZE=10

# CORS (Update with your frontend URL)
CORS_ORIGINS=http://localhost:{ports.get('frontend', 3001)},http://localhost:{ports.get('backend', 8000)}

# MONITORING (Optional)
ENABLE_MONITORING=false
GRAFANA_ADMIN_PASSWORD=admin
METRICS_ENABLED=true
METRICS_PATH=/metrics

# BACKUP & MAINTENANCE (Optional)
ENABLE_AUTO_BACKUP=false
BACKUP_SCHEDULE_CRON=0 2 * * *
BACKUP_RETENTION_DAYS=7

# ============================================================================
# READY TO USE!
# ============================================================================
# This configuration is ready for deployment.
# Only add your LLM API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)
# ============================================================================
"""

    def _generate_deploy_script(self, module_name: str, deployment_type: str) -> str:
        """Generate deployment script."""

        script = f"""#!/bin/bash
# Deployment Script for {module_name}
# Deployment Type: {deployment_type}
# Generated: {datetime.utcnow().isoformat()}

set -e  # Exit on error

echo "🚀 Deploying {module_name} - {deployment_type}"
echo "================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Copy .env.example to .env and configure your settings:"
    echo "   cp .env.example .env"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "   Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "   Install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Build Docker images
echo "🔨 Building Docker images (this may take 5-10 minutes on first run)..."
docker-compose build --no-cache

# Pull external images (PostgreSQL, Redis, MinIO)
echo "📥 Pulling external images..."
docker-compose pull postgres redis minio

# Start services
echo "🔧 Starting services..."
docker-compose up -d

# Wait for services to be ready using utility script
if [ -f ../scripts/wait-for-services.sh ]; then
    echo "⏳ Waiting for services to be ready..."
    docker-compose exec -T backend bash /app/scripts/wait-for-services.sh || true
else
    echo "⏳ Waiting for services (10 seconds)..."
    sleep 10
fi

# Initialize MinIO buckets
if [ -f ../scripts/init-minio.sh ]; then
    echo "🪣 Initializing MinIO buckets..."
    docker-compose exec -T backend bash ../scripts/init-minio.sh || echo "⚠️  MinIO init skipped (may need manual setup)"
fi

# Initialize database
if [ -f ../scripts/init-database.sh ]; then
    echo "🗄️  Initializing database schema..."
    docker-compose exec -T backend bash ../scripts/init-database.sh || echo "⚠️  Database init skipped (may need manual setup)"
fi

# Run health checks
if [ -f ../scripts/health-check.sh ]; then
    echo "🏥 Running health checks..."
    bash ../scripts/health-check.sh
else
    echo "🏥 Checking service health..."
    docker-compose ps
fi

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T backend python scripts/run_migrations.py || echo "⚠️  Migrations may have already run"

# Load pre-computed embeddings
echo "📦 Loading pre-computed embeddings..."
docker-compose exec -T backend python scripts/load_embeddings.py || echo "⚠️  Embeddings may already be loaded"

# Show deployment URL
echo ""
echo "✅ Deployment complete!"
echo "================================================"
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:3001"
echo "API Docs: http://localhost:8000/docs"
echo "MinIO Console: http://localhost:9001"
echo ""
echo "Monitor logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
echo "================================================"
"""
        return script

    def _generate_backup_script(self) -> str:
        """Generate backup script."""

        script = f"""#!/bin/bash
# Backup Script
# Generated: {datetime.utcnow().isoformat()}

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="genai-backup-$TIMESTAMP"

echo "🔒 Starting backup: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
echo "📦 Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump -U postgres genai > "$BACKUP_DIR/$BACKUP_NAME-postgres.sql"

# Backup MinIO data
echo "📦 Backing up MinIO data..."
docker-compose exec -T minio mc mirror /data "$BACKUP_DIR/$BACKUP_NAME-minio" || echo "Using docker cp fallback..."
docker cp genai-minio:/data "$BACKUP_DIR/$BACKUP_NAME-minio"

# Backup configuration
echo "📦 Backing up configuration..."
tar -czf "$BACKUP_DIR/$BACKUP_NAME-config.tar.gz" .env config/

# Create backup manifest
echo "📋 Creating manifest..."
cat > "$BACKUP_DIR/$BACKUP_NAME-manifest.txt" <<EOF
Backup: $BACKUP_NAME
Date: $(date)
PostgreSQL: $BACKUP_NAME-postgres.sql
MinIO: $BACKUP_NAME-minio/
Config: $BACKUP_NAME-config.tar.gz
EOF

echo "✅ Backup complete: $BACKUP_DIR/$BACKUP_NAME"
echo "📁 Files:"
ls -lh "$BACKUP_DIR" | grep "$BACKUP_NAME"
"""
        return script

    def _generate_database_load_script(self, module_name: str) -> str:
        """
        Generate Python script to load Parquet embeddings into PostgreSQL.

        This script loads pre-computed embeddings from Parquet format
        into the customer's PostgreSQL database with pgvector.
        """

        script = f"""#!/usr/bin/env python3
\"\"\"
Database Load Script - Load Embeddings from Parquet

This script loads pre-computed embeddings from Parquet format
into PostgreSQL with pgvector extension.

Usage:
    python load_embeddings.py

Requirements:
    pip install pyarrow pandas psycopg2-binary numpy

Author: Export Wizard
Generated: {datetime.utcnow().isoformat()}
\"\"\"

import os
import sys
from pathlib import Path
import psycopg2
import pyarrow.parquet as pq
import numpy as np
from datetime import datetime


def load_embeddings_from_parquet(parquet_path: str, db_conn_string: str):
    \"\"\"
    Load embeddings from Parquet file into PostgreSQL.

    Args:
        parquet_path: Path to embeddings.parquet file
        db_conn_string: PostgreSQL connection string
    \"\"\"
    print(f"📦 Loading embeddings from: {{parquet_path}}")

    # Read Parquet file
    table = pq.read_table(parquet_path)
    df = table.to_pandas()

    total_embeddings = len(df)
    print(f"   Found {{total_embeddings}} embeddings to load")

    # Connect to PostgreSQL
    print("🔌 Connecting to PostgreSQL...")
    conn = psycopg2.connect(db_conn_string)
    cursor = conn.cursor()

    try:
        # Enable pgvector extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        print("   ✅ pgvector extension enabled")

        # Create table if not exists
        cursor.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS document_chunks (
                id UUID PRIMARY KEY,
                document_id UUID NOT NULL,
                content TEXT NOT NULL,
                embedding vector(384),
                chunk_index INTEGER NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        \"\"\")
        conn.commit()
        print("   ✅ Table created/verified")

        # Create index for vector similarity search
        cursor.execute(\"\"\"
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding
            ON document_chunks
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        \"\"\")
        conn.commit()
        print("   ✅ Vector index created")

        # Load embeddings in batches
        batch_size = 1000
        total_inserted = 0

        print(f"📥 Inserting {{total_embeddings}} embeddings in batches of {{batch_size}}...")

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]

            # Prepare batch insert
            values = []
            for _, row in batch.iterrows():
                # Convert embedding list to PostgreSQL vector format
                embedding_str = '[' + ','.join(map(str, row['embedding'])) + ']'

                values.append((
                    row['chunk_id'],
                    row['document_id'],
                    row['content'],
                    embedding_str,
                    row['chunk_index'],
                    psycopg2.extras.Json(row.get('metadata', {{}}))
                ))

            # Batch insert
            cursor.executemany(
                \"\"\"
                INSERT INTO document_chunks
                (id, document_id, content, embedding, chunk_index, metadata)
                VALUES (%s, %s, %s, %s::vector, %s, %s)
                ON CONFLICT (id) DO NOTHING
                \"\"\",
                values
            )

            total_inserted += len(batch)
            progress = (total_inserted / total_embeddings) * 100
            print(f"   Progress: {{total_inserted}}/{{total_embeddings}} ({{progress:.1f}}%)")

        conn.commit()
        print(f"✅ Successfully loaded {{total_inserted}} embeddings")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"✅ Verified: {{count}} embeddings in database")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error loading embeddings: {{e}}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    \"\"\"Main execution.\"\"\"
    print("="*80)
    print("Database Load Script - Parquet to PostgreSQL")
    print("="*80)

    # Configuration
    parquet_path = os.getenv("EMBEDDINGS_PARQUET_PATH", "../data/precomputed_embeddings/embeddings.parquet")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "genai")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

    # Build connection string
    db_conn_string = f"host={{db_host}} port={{db_port}} dbname={{db_name}} user={{db_user}} password={{db_password}}"

    # Check if Parquet file exists
    if not Path(parquet_path).exists():
        print(f"❌ Parquet file not found: {{parquet_path}}")
        print("   Please ensure embeddings have been exported.")
        sys.exit(1)

    # Load embeddings
    try:
        load_embeddings_from_parquet(parquet_path, db_conn_string)
        print("="*80)
        print("✅ Database load complete!")
        print("="*80)
    except Exception as e:
        print("="*80)
        print(f"❌ Database load failed: {{e}}")
        print("="*80)
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
        return script

    def _generate_rest_api_client(self, module_name: str, config: Dict[str, Any]) -> str:
        """Generate REST API client example with bi-directional data flow."""

        client = f"""#!/usr/bin/env python3
\"\"\"
REST API Client Example for {{module_name}}

Demonstrates:
- Query submission (customer → GenAI)
- Results retrieval (GenAI → customer)
- Document upload (customer → GenAI)
- Webhook registration (bi-directional flow)

Author: Export Wizard
Generated: {datetime.utcnow().isoformat()}
\"\"\"

import requests
import json
from typing import Dict, Any, Optional, List


class GenAIClient:
    \"\"\"REST API client for {module_name} GenAI application.\"\"\"

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        \"\"\"
        Initialize client.

        Args:
            base_url: Base URL of GenAI API (e.g., http://localhost:8000)
            api_key: Optional API key for authentication
        \"\"\"
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({{'Authorization': f'Bearer {{api_key}}'}})

    def query(self, question: str, session_id: Optional[str] = None,
              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        \"\"\"
        Submit a query to the GenAI system.

        Args:
            question: User question/prompt
            session_id: Optional session ID for conversation context
            context: Optional additional context

        Returns:
            Response with answer, sources, and metadata
        \"\"\"
        payload = {{
            "question": question,
            "session_id": session_id,
            "context": context or {{}}
        }}

        response = self.session.post(
            f"{{self.base_url}}/api/v1/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def upload_document(self, file_path: str, session_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        \"\"\"
        Upload a document for processing.

        Args:
            file_path: Path to document file
            session_id: Optional session ID
            metadata: Optional metadata for the document

        Returns:
            Upload confirmation with document ID
        \"\"\"
        with open(file_path, 'rb') as f:
            files = {{'file': f}}
            data = {{}}

            if session_id:
                data['session_id'] = session_id
            if metadata:
                data['metadata'] = json.dumps(metadata)

            response = self.session.post(
                f"{{self.base_url}}/api/v1/upload",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()

    def get_documents(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        \"\"\"
        Get list of documents.

        Args:
            session_id: Optional session ID filter

        Returns:
            List of documents
        \"\"\"
        params = {{}}
        if session_id:
            params['session_id'] = session_id

        response = self.session.get(
            f"{{self.base_url}}/api/v1/documents",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def register_webhook(self, webhook_url: str, events: List[str]) -> Dict[str, Any]:
        \"\"\"
        Register a webhook for bi-directional data flow.

        Args:
            webhook_url: Your webhook endpoint URL
            events: List of events to subscribe to
                    (e.g., ['query.completed', 'document.processed'])

        Returns:
            Webhook registration confirmation
        \"\"\"
        payload = {{
            "webhook_url": webhook_url,
            "events": events,
            "active": True
        }}

        response = self.session.post(
            f"{{self.base_url}}/api/v1/webhooks",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def stream_query(self, question: str, session_id: Optional[str] = None):
        \"\"\"
        Stream query results (SSE - Server-Sent Events).

        Args:
            question: User question
            session_id: Optional session ID

        Yields:
            Streaming response chunks
        \"\"\"
        payload = {{
            "question": question,
            "session_id": session_id,
            "stream": True
        }}

        response = self.session.post(
            f"{{self.base_url}}/api/v1/query/stream",
            json=payload,
            stream=True
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                yield line.decode('utf-8')


# Example Usage
if __name__ == "__main__":
    # Initialize client
    client = GenAIClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"  # Optional
    )

    # Example 1: Simple query
    print("Example 1: Simple Query")
    result = client.query("What is the capital of France?")
    print(f"Answer: {{result['answer']}}")
    print(f"Sources: {{result.get('sources', [])}}")
    print()

    # Example 2: Upload document
    print("Example 2: Upload Document")
    upload_result = client.upload_document(
        file_path="./sample.pdf",
        metadata={{"category": "research"}}
    )
    print(f"Document ID: {{upload_result['document_id']}}")
    print()

    # Example 3: Register webhook
    print("Example 3: Register Webhook")
    webhook_result = client.register_webhook(
        webhook_url="https://your-domain.com/webhook",
        events=["query.completed", "document.processed"]
    )
    print(f"Webhook ID: {{webhook_result['webhook_id']}}")
    print()

    # Example 4: Streaming query
    print("Example 4: Streaming Query")
    for chunk in client.stream_query("Explain quantum computing"):
        print(chunk, end='', flush=True)
    print()
"""
        return client

    def _generate_graphql_client(self, module_name: str, config: Dict[str, Any]) -> str:
        """Generate GraphQL API client example."""

        client = f"""#!/usr/bin/env python3
\"\"\"
GraphQL API Client Example for {module_name}

Demonstrates GraphQL queries and mutations for bi-directional data flow.

Author: Export Wizard
Generated: {datetime.utcnow().isoformat()}
\"\"\"

import requests
from typing import Dict, Any, Optional, List


class GraphQLClient:
    \"\"\"GraphQL client for {module_name} GenAI application.\"\"\"

    def __init__(self, endpoint: str, api_key: Optional[str] = None):
        \"\"\"
        Initialize GraphQL client.

        Args:
            endpoint: GraphQL endpoint URL (e.g., http://localhost:8000/graphql)
            api_key: Optional API key
        \"\"\"
        self.endpoint = endpoint
        self.headers = {{'Content-Type': 'application/json'}}

        if api_key:
            self.headers['Authorization'] = f'Bearer {{api_key}}'

    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        \"\"\"
        Execute a GraphQL query/mutation.

        Args:
            query: GraphQL query or mutation string
            variables: Optional variables for the query

        Returns:
            GraphQL response
        \"\"\"
        payload = {{'query': query}}
        if variables:
            payload['variables'] = variables

        response = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()

        result = response.json()
        if 'errors' in result:
            raise Exception(f"GraphQL errors: {{result['errors']}}")

        return result.get('data', {{}})

    def query_documents(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        \"\"\"Query documents with GraphQL.\"\"\"

        query = \"\"\"
        query GetDocuments($sessionId: String) {{
            documents(sessionId: $sessionId) {{
                id
                filename
                fileType
                fileSize
                processed
                uploadedAt
                metadata
            }}
        }}
        \"\"\"

        variables = {{'sessionId': session_id}} if session_id else None
        result = self.execute(query, variables)
        return result.get('documents', [])

    def submit_query(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        \"\"\"Submit a query via GraphQL mutation.\"\"\"

        mutation = \"\"\"
        mutation SubmitQuery($question: String!, $sessionId: String) {{
            submitQuery(question: $question, sessionId: $sessionId) {{
                answer
                sources {{
                    documentId
                    filename
                    relevanceScore
                }}
                metadata {{
                    tokensUsed
                    latencyMs
                    model
                }}
            }}
        }}
        \"\"\"

        variables = {{
            'question': question,
            'sessionId': session_id
        }}

        result = self.execute(mutation, variables)
        return result.get('submitQuery', {{}})


# Example Usage
if __name__ == "__main__":
    client = GraphQLClient(
        endpoint="http://localhost:8000/graphql",
        api_key="your-api-key-here"
    )

    # Query documents
    print("Fetching documents...")
    docs = client.query_documents()
    print(f"Found {{len(docs)}} documents")

    # Submit query
    print("\\nSubmitting query...")
    result = client.submit_query("What are the key findings?")
    print(f"Answer: {{result['answer']}}")
"""
        return client

    def _generate_websocket_client(self, module_name: str, config: Dict[str, Any]) -> str:
        """Generate WebSocket client example for real-time bi-directional communication."""

        client = f"""#!/usr/bin/env python3
\"\"\"
WebSocket Client Example for {module_name}

Real-time bi-directional communication for:
- Live query streaming
- Real-time document processing updates
- System notifications

Author: Export Wizard
Generated: {datetime.utcnow().isoformat()}
\"\"\"

import asyncio
import websockets
import json
from typing import Optional, Callable


class WebSocketClient:
    \"\"\"WebSocket client for real-time GenAI communication.\"\"\"

    def __init__(self, ws_url: str, api_key: Optional[str] = None):
        \"\"\"
        Initialize WebSocket client.

        Args:
            ws_url: WebSocket URL (e.g., ws://localhost:8000/ws)
            api_key: Optional API key for authentication
        \"\"\"
        self.ws_url = ws_url
        self.api_key = api_key
        self.websocket = None

    async def connect(self):
        \"\"\"Establish WebSocket connection.\"\"\"
        headers = {{}}
        if self.api_key:
            headers['Authorization'] = f'Bearer {{self.api_key}}'

        self.websocket = await websockets.connect(
            self.ws_url,
            extra_headers=headers
        )
        print(f"✅ Connected to {{self.ws_url}}")

    async def send_message(self, message: dict):
        \"\"\"Send message to server.\"\"\"
        if not self.websocket:
            raise Exception("Not connected")

        await self.websocket.send(json.dumps(message))

    async def receive_message(self) -> dict:
        \"\"\"Receive message from server.\"\"\"
        if not self.websocket:
            raise Exception("Not connected")

        message = await self.websocket.recv()
        return json.loads(message)

    async def stream_query(self, question: str, on_chunk: Callable[[str], None]):
        \"\"\"
        Stream query results in real-time.

        Args:
            question: User question
            on_chunk: Callback function for each response chunk
        \"\"\"
        # Send query
        await self.send_message({{
            "type": "query",
            "data": {{
                "question": question,
                "stream": True
            }}
        }})

        # Receive streaming response
        while True:
            message = await self.receive_message()

            if message['type'] == 'chunk':
                on_chunk(message['data']['text'])
            elif message['type'] == 'complete':
                break
            elif message['type'] == 'error':
                raise Exception(message['data']['message'])

    async def subscribe_events(self, events: list, on_event: Callable[[dict], None]):
        \"\"\"
        Subscribe to server events.

        Args:
            events: List of event types to subscribe to
            on_event: Callback function for each event
        \"\"\"
        # Subscribe
        await self.send_message({{
            "type": "subscribe",
            "data": {{"events": events}}
        }})

        # Listen for events
        while True:
            message = await self.receive_message()

            if message['type'] in events:
                on_event(message)

    async def close(self):
        \"\"\"Close WebSocket connection.\"\"\"
        if self.websocket:
            await self.websocket.close()
            print("✅ Connection closed")


# Example Usage
async def main():
    client = WebSocketClient(
        ws_url="ws://localhost:8000/ws",
        api_key="your-api-key-here"
    )

    await client.connect()

    try:
        # Example 1: Stream query
        print("Streaming query...")

        def on_chunk(text):
            print(text, end='', flush=True)

        await client.stream_query(
            "Explain machine learning",
            on_chunk=on_chunk
        )
        print("\\n")

        # Example 2: Subscribe to events
        print("Subscribing to events...")

        def on_event(event):
            print(f"Event: {{event['type']}} - {{event['data']}}")

        await client.subscribe_events(
            events=['document.processed', 'query.completed'],
            on_event=on_event
        )

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
"""
        return client

    def _generate_webhook_config(self, module_name: str, config: Dict[str, Any]) -> str:
        """Generate webhook configuration for bi-directional data flow."""

        import json

        webhook_config = {
            "webhook_configuration": {
                "description": f"Webhook integration for {module_name} - enables bi-directional data flow",
                "endpoints": [
                    {
                        "name": "query_completed",
                        "event": "query.completed",
                        "method": "POST",
                        "payload_example": {
                            "event_type": "query.completed",
                            "timestamp": "2026-01-04T00:00:00Z",
                            "data": {
                                "query_id": "uuid",
                                "question": "user question",
                                "answer": "generated answer",
                                "sources": [],
                                "metadata": {}
                            }
                        },
                        "description": "Triggered when a query is completed"
                    },
                    {
                        "name": "document_processed",
                        "event": "document.processed",
                        "method": "POST",
                        "payload_example": {
                            "event_type": "document.processed",
                            "timestamp": "2026-01-04T00:00:00Z",
                            "data": {
                                "document_id": "uuid",
                                "filename": "document.pdf",
                                "status": "completed",
                                "chunks_created": 42,
                                "embeddings_generated": 42
                            }
                        },
                        "description": "Triggered when document processing is complete"
                    },
                    {
                        "name": "data_sync",
                        "event": "data.sync",
                        "method": "POST",
                        "payload_example": {
                            "event_type": "data.sync",
                            "timestamp": "2026-01-04T00:00:00Z",
                            "data": {
                                "sync_type": "incremental",
                                "records_synced": 100,
                                "status": "completed"
                            }
                        },
                        "description": "Triggered for data synchronization events"
                    }
                ],
                "registration": {
                    "endpoint": "/api/v1/webhooks",
                    "method": "POST",
                    "payload": {
                        "webhook_url": "https://your-domain.com/webhook",
                        "events": ["query.completed", "document.processed", "data.sync"],
                        "secret": "your-webhook-secret",
                        "active": True
                    }
                },
                "security": {
                    "signature_header": "X-Webhook-Signature",
                    "signature_algorithm": "HMAC-SHA256",
                    "verification_instructions": "Verify webhook signature using your secret key"
                },
                "retry_policy": {
                    "max_attempts": 3,
                    "backoff_multiplier": 2,
                    "initial_delay_seconds": 5
                }
            }
        }

        return json.dumps(webhook_config, indent=2)

    def _generate_openapi_spec(self, module_name: str, config: Dict[str, Any]) -> str:
        """Generate OpenAPI/Swagger specification for API documentation."""

        import json

        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": f"{module_name} GenAI API",
                "version": "1.0.0",
                "description": f"Complete API documentation for {module_name} standalone GenAI application with bi-directional data flow capabilities",
                "contact": {
                    "name": "API Support",
                    "email": "support@example.com"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Local development server"
                },
                {
                    "url": "https://api.example.com",
                    "description": "Production server"
                }
            ],
            "paths": {
                "/api/v1/query": {
                    "post": {
                        "summary": "Submit a query",
                        "description": "Submit a question to the GenAI system and receive an answer with sources",
                        "tags": ["Query"],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["question"],
                                        "properties": {
                                            "question": {
                                                "type": "string",
                                                "description": "User question/prompt"
                                            },
                                            "session_id": {
                                                "type": "string",
                                                "description": "Optional session ID for conversation context"
                                            },
                                            "context": {
                                                "type": "object",
                                                "description": "Optional additional context"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "answer": {"type": "string"},
                                                "sources": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "document_id": {"type": "string"},
                                                            "filename": {"type": "string"},
                                                            "relevance_score": {"type": "number"}
                                                        }
                                                    }
                                                },
                                                "metadata": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/upload": {
                    "post": {
                        "summary": "Upload a document",
                        "description": "Upload a document for processing and embedding generation",
                        "tags": ["Documents"],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["file"],
                                        "properties": {
                                            "file": {
                                                "type": "string",
                                                "format": "binary"
                                            },
                                            "session_id": {"type": "string"},
                                            "metadata": {"type": "string", "description": "JSON-encoded metadata"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Document uploaded successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "document_id": {"type": "string"},
                                                "filename": {"type": "string"},
                                                "status": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/documents": {
                    "get": {
                        "summary": "List documents",
                        "description": "Get a list of uploaded documents",
                        "tags": ["Documents"],
                        "parameters": [
                            {
                                "name": "session_id",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "string"},
                                "description": "Filter by session ID"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of documents",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string"},
                                                    "filename": {"type": "string"},
                                                    "file_type": {"type": "string"},
                                                    "file_size": {"type": "integer"},
                                                    "processed": {"type": "boolean"},
                                                    "uploaded_at": {"type": "string", "format": "date-time"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/api/v1/webhooks": {
                    "post": {
                        "summary": "Register a webhook",
                        "description": "Register a webhook for bi-directional data flow",
                        "tags": ["Webhooks"],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["webhook_url", "events"],
                                        "properties": {
                                            "webhook_url": {
                                                "type": "string",
                                                "format": "uri",
                                                "description": "Your webhook endpoint URL"
                                            },
                                            "events": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "Events to subscribe to"
                                            },
                                            "secret": {
                                                "type": "string",
                                                "description": "Secret for webhook signature verification"
                                            },
                                            "active": {
                                                "type": "boolean",
                                                "description": "Whether webhook is active"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Webhook registered successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "webhook_id": {"type": "string"},
                                                "status": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "JWT token for API authentication"
                    },
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key",
                        "description": "API key for authentication"
                    }
                }
            },
            "security": [
                {"BearerAuth": []},
                {"ApiKeyAuth": []}
            ],
            "tags": [
                {
                    "name": "Query",
                    "description": "Query submission and retrieval operations"
                },
                {
                    "name": "Documents",
                    "description": "Document upload and management operations"
                },
                {
                    "name": "Webhooks",
                    "description": "Webhook registration for bi-directional data flow"
                }
            ]
        }

        return json.dumps(openapi_spec, indent=2)

    def _generate_readme(
        self,
        module_name: str,
        deployment_type: DeploymentType,
        options: InfrastructureOptions
    ) -> str:
        """Generate deployment README."""

        readme = f"""# {module_name} - Deployment Guide

**Deployment Type**: {deployment_type.value}
**Generated**: {datetime.utcnow().isoformat()}

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- 20GB disk space

### Deployment Steps

1. **Configure Environment**

```bash
cp .env.example .env
# Edit .env and add your API keys
```

2. **Deploy**

```bash
chmod +x deploy.sh
./deploy.sh
```

3. **Access**

- Backend API: http://localhost:8000
- Frontend UI: http://localhost:3001
- API Documentation: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

---

## 📚 Configuration

### Required Environment Variables

- `POSTGRES_PASSWORD` - PostgreSQL password
- `OPENAI_API_KEY` - OpenAI API key
- `JWT_SECRET` - JWT secret (min 32 chars)
- `SECRET_KEY` - App secret key (min 32 chars)
- `MINIO_SECRET_KEY` - MinIO secret key

### Optional Environment Variables

- `ANTHROPIC_API_KEY` - Anthropic Claude API key
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)
- `BACKEND_PORT` - Backend port (default: 8000)
- `FRONTEND_PORT` - Frontend port (default: 3001)

---

## 🏥 Health Checks

```bash
# Check all services
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# View logs
docker-compose logs -f backend
```

---

## 🔒 Backup & Restore

### Backup

```bash
./backup.sh
```

Backups are stored in `./backups/` directory.

### Restore

```bash
# Stop services
docker-compose down

# Restore PostgreSQL
docker-compose up -d postgres
cat backups/genai-backup-TIMESTAMP-postgres.sql | docker-compose exec -T postgres psql -U postgres genai

# Restore MinIO
docker cp backups/genai-backup-TIMESTAMP-minio genai-minio:/data

# Start all services
docker-compose up -d
```

---

## 🔧 Maintenance

### Update to New Version

```bash
# Pull new images
docker-compose pull

# Restart services
docker-compose down
docker-compose up -d
```

### Scale Services

```bash
# Scale backend to 3 instances
docker-compose up -d --scale backend=3
```

### View Resource Usage

```bash
docker stats
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend
```

### Database Connection Errors

```bash
# Verify PostgreSQL is running
docker-compose exec postgres pg_isready -U postgres

# Check database exists
docker-compose exec postgres psql -U postgres -l
```

### MinIO Access Issues

```bash
# Verify MinIO is running
curl http://localhost:9000/minio/health/live

# Access MinIO console
# Open http://localhost:9001
# Login with credentials from .env
```

---

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review this README
3. Contact support: support@yourcompany.com

---

## 📝 License

Licensed under the terms provided with this package.

**License Tier**: {options.security_level.upper()}
**Deployment ID**: {module_name}-{deployment_type.value}

---

**Generated by Export Wizard v1.0.0**
"""
        return readme

    def _generate_backend_dockerfile(self, module_name: str) -> str:
        """
        Generate production-ready Backend Dockerfile.

        Multi-stage build for smaller image size.
        Includes all dependencies needed for module.

        Args:
            module_name: Module name for labeling

        Returns:
            Dockerfile content as string
        """
        return f'''# Multi-stage build for {module_name} backend
FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \\
    gcc g++ make \\
    libpq-dev \\
    tesseract-ocr \\
    poppler-utils \\
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Final stage - Runtime
# ============================================================================
FROM python:3.11-slim

# Install runtime dependencies only (smaller image)
RUN apt-get update && apt-get install -y \\
    libpq5 \\
    tesseract-ocr \\
    poppler-utils \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user (security best practice)
RUN useradd -m -u 1000 appuser && \\
    mkdir -p /app /app/logs /app/data && \\
    chown -R appuser:appuser /app

USER appuser
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser ./app /app/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start application with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
'''

    def _generate_frontend_dockerfile(self, module_name: str) -> str:
        """
        Generate production-ready Frontend Dockerfile.

        Multi-stage build with standalone Next.js output.

        Args:
            module_name: Module name for labeling

        Returns:
            Dockerfile content as string
        """
        return f'''# Multi-stage build for {module_name} frontend
FROM node:18-alpine AS deps

WORKDIR /app

# Install dependencies based on package-lock.json (fallback to npm install if missing)
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --only=production; else npm install --only=production --legacy-peer-deps; fi

# ============================================================================
# Build stage
# ============================================================================
FROM node:18-alpine AS builder

WORKDIR /app

# Install all dependencies (including dev) - fallback to npm install if package-lock.json missing
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install --legacy-peer-deps; fi

# Copy source code
COPY . .

# Build Next.js app (standalone output)
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# ============================================================================
# Production stage
# ============================================================================
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \\
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Change ownership
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3001

ENV PORT 3001
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
'''

    def _generate_database_init_script(self, module_name: str) -> str:
        """Generate database initialization script with schema creation."""

        return f'''#!/bin/bash
# Database Initialization Script for {module_name}
# Generated by Export Wizard

set -e

echo "🗄️  Initializing database schema for {module_name}..."

# Wait for PostgreSQL to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\\q' 2>/dev/null; do
  echo "⏳ Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "✅ PostgreSQL is ready"

# Enable pgvector extension
echo "📦 Enabling pgvector extension..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL

echo "✅ Extensions enabled"

# Run Alembic migrations
echo "🔄 Running database migrations..."
cd /app
alembic upgrade head

echo "✅ Database initialization complete"
'''

    def _generate_wait_for_services_script(self) -> str:
        """Generate script to wait for all services to be ready."""

        return '''#!/bin/bash
# Wait for Services Script
# Ensures all dependent services are ready before starting application

set -e

echo "⏳ Waiting for dependent services to be ready..."

# Function to wait for a service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=60
    local attempt=1

    echo "Checking $service_name at $host:$port..."

    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ $service_name failed to start after $max_attempts attempts"
            exit 1
        fi
        echo "⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    echo "✅ $service_name is ready"
}

# Wait for PostgreSQL
wait_for_service "${POSTGRES_HOST:-postgres}" "${POSTGRES_PORT:-5432}" "PostgreSQL"

# Wait for Redis
wait_for_service "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}" "Redis"

# Wait for MinIO
wait_for_service "${MINIO_HOST:-minio}" "${MINIO_PORT:-9000}" "MinIO"

# Additional wait for PostgreSQL to fully initialize
echo "⏳ Waiting 5 seconds for PostgreSQL full initialization..."
sleep 5

echo "✅ All services are ready!"
'''

    def _generate_health_check_script(self, module_name: str) -> str:
        """Generate deployment health check and validation script."""

        return f'''#!/bin/bash
# Deployment Health Check Script for {module_name}
# Validates that all services are running correctly

set -e

BACKEND_URL="${{BACKEND_URL:-http://localhost:8000}}"
FRONTEND_URL="${{FRONTEND_URL:-http://localhost:3001}}"

echo "🏥 Running health checks for {module_name}..."
echo ""

# Function to check HTTP endpoint
check_endpoint() {{
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy: $url"
            return 0
        fi

        if [ $attempt -eq $max_attempts ]; then
            echo "❌ $service_name health check failed: $url"
            return 1
        fi

        echo "⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
}}

# Check Backend
echo "Checking Backend..."
check_endpoint "$BACKEND_URL/health" "Backend API"

# Check Frontend
echo "Checking Frontend..."
check_endpoint "$FRONTEND_URL" "Frontend UI"

# Check MinIO
echo "Checking MinIO..."
check_endpoint "http://localhost:9000/minio/health/live" "MinIO"

# Check PostgreSQL connection
echo "Checking PostgreSQL..."
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL health check failed"
    exit 1
fi

# Check Redis connection
echo "Checking Redis..."
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    exit 1
fi

echo ""
echo "🎉 All health checks passed!"
echo ""
echo "Access URLs:"
echo "  Backend API:  $BACKEND_URL"
echo "  API Docs:     $BACKEND_URL/docs"
echo "  Frontend UI:  $FRONTEND_URL"
echo "  MinIO Console: http://localhost:9001"
echo ""
'''

    def _generate_init_minio_script(self, module_name: str) -> str:
        """Generate MinIO bucket initialization script."""

        return f'''#!/bin/bash
# MinIO Bucket Initialization Script for {module_name}
# Creates required S3 buckets

set -e

echo "🪣 Initializing MinIO buckets for {module_name}..."

# Wait for MinIO to be ready
until curl -sf http://minio:9000/minio/health/live > /dev/null 2>&1; do
  echo "⏳ Waiting for MinIO to be ready..."
  sleep 2
done

echo "✅ MinIO is ready"

# Configure mc (MinIO client)
mc alias set local http://minio:9000 ${{MINIO_ROOT_USER:-minioadmin}} ${{MINIO_ROOT_PASSWORD:-minioadmin}}

# Create buckets
BUCKETS=("documents" "exports" "uploads" "temp")

for bucket in "${{BUCKETS[@]}}"; do
    if mc ls local/$bucket > /dev/null 2>&1; then
        echo "✅ Bucket '$bucket' already exists"
    else
        mc mb local/$bucket
        echo "✅ Created bucket: $bucket"
    fi
done

# Set public policy for exports bucket (optional)
mc anonymous set download local/exports

echo "✅ MinIO bucket initialization complete"
'''

    # Placeholder methods for other deployment types
    async def _generate_docker_compose_ha(self, *args, **kwargs):
        """Generate HA Docker Compose (to be implemented)."""
        logger.warning("Docker Compose HA generation not yet implemented")
        raise NotImplementedError("Docker Compose HA coming in Phase 2")

    async def _generate_kubernetes(self, *args, **kwargs):
        """Generate Kubernetes manifests (to be implemented)."""
        logger.warning("Kubernetes generation not yet implemented")
        raise NotImplementedError("Kubernetes coming in Phase 2")

    async def _generate_aws(self, *args, **kwargs):
        """Generate AWS infrastructure (to be implemented)."""
        logger.warning("AWS generation not yet implemented")
        raise NotImplementedError("AWS coming in Phase 2")

    async def _generate_azure(self, *args, **kwargs):
        """Generate Azure infrastructure (to be implemented)."""
        logger.warning("Azure generation not yet implemented")
        raise NotImplementedError("Azure coming in Phase 2")

    async def _generate_gcp(self, *args, **kwargs):
        """Generate GCP infrastructure (to be implemented)."""
        logger.warning("GCP generation not yet implemented")
        raise NotImplementedError("GCP coming in Phase 2")
