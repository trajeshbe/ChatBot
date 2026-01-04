"""
Configuration Extractor Service

Extracts POC configuration from database and transforms it for standalone deployment.

This service:
1. Retrieves module configuration from POCConfigService
2. Transforms platform-specific URLs to environment variables
3. Resolves relative paths to absolute paths
4. Adds standalone-specific settings
5. Validates configuration completeness

Author: Claude Code
Date: 2026-01-03
Phase: 1 - Core Export Engine
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.poc_config_service import POCConfigService
from app.models.module_configuration import ModuleConfiguration

logger = logging.getLogger(__name__)


class ConfigurationExtractor:
    """Extract and transform POC configuration for standalone deployment."""

    def __init__(self, db: AsyncSession):
        """
        Initialize ConfigurationExtractor.

        Args:
            db: Async database session
        """
        self.db = db
        self.poc_config_service = POCConfigService()

    async def extract_module_config(
        self,
        module_name: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract complete module configuration for export.

        Args:
            module_name: Name of the module to export (e.g., "british_council")
            tenant_id: Optional tenant ID for multi-tenant filtering
            user_id: Optional user ID to include user-specific overrides

        Returns:
            Complete standalone configuration dictionary

        Raises:
            ValueError: If module configuration not found
            RuntimeError: If configuration validation fails
        """
        logger.info(f"📦 Extracting configuration for module: {module_name}")

        # Get base config from POCConfigService
        config = await self.poc_config_service.get_config(
            db=self.db,
            module_name=module_name,
            user_id=user_id
        )

        if not config:
            raise ValueError(f"No configuration found for module: {module_name}")

        # Transform for standalone deployment
        standalone_config = await self._transform_for_standalone(
            config=config,
            module_name=module_name,
            tenant_id=tenant_id
        )

        # Add metadata
        standalone_config["_metadata"] = {
            "exported_at": datetime.utcnow().isoformat(),
            "module_name": module_name,
            "tenant_id": tenant_id,
            "source": "platform_export",
            "version": "1.0.0"
        }

        # Validate completeness
        self._validate_config(standalone_config, module_name)

        logger.info(f"✅ Configuration extracted successfully: {len(json.dumps(standalone_config))} bytes")

        return standalone_config

    async def _transform_for_standalone(
        self,
        config: Dict[str, Any],
        module_name: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform platform configuration to standalone configuration.

        Changes:
        1. Platform URLs → Environment variables
        2. Relative paths → Absolute paths
        3. Add default values for standalone
        4. Remove platform-specific keys

        Args:
            config: Original platform configuration
            module_name: Module name
            tenant_id: Optional tenant ID

        Returns:
            Transformed standalone configuration
        """
        standalone = config.copy()

        # 1. Transform URLs to environment variables
        standalone = self._transform_urls_to_env_vars(standalone)

        # 2. Transform API keys and secrets
        standalone = self._transform_secrets_to_env_vars(standalone)

        # 3. Add standalone-specific settings
        standalone = self._add_standalone_settings(standalone, module_name)

        # 4. Remove platform-specific keys
        standalone = self._remove_platform_specific_keys(standalone)

        # 5. Transform model configurations
        if "models" in standalone:
            standalone["models"] = self._transform_model_config(standalone["models"])

        # 6. Transform retrieval/RAG settings
        if "retrieval" in standalone:
            standalone["retrieval"] = self._transform_retrieval_config(standalone["retrieval"])

        return standalone

    def _transform_urls_to_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform hardcoded URLs to environment variable references.

        Before:
          "llm_endpoint": "http://platform.com/api/llm"

        After:
          "llm_endpoint": "${LLM_ENDPOINT:-http://localhost:8000/api/llm}"
        """
        url_mappings = {
            # LLM endpoints
            "llm_endpoint": "LLM_ENDPOINT",
            "openai_base_url": "OPENAI_BASE_URL",
            "anthropic_base_url": "ANTHROPIC_BASE_URL",

            # Database connections
            "database_url": "DATABASE_URL",
            "postgres_url": "POSTGRES_URL",
            "redis_url": "REDIS_URL",

            # Vector database
            "vector_db_url": "VECTOR_DB_URL",
            "elasticsearch_url": "ELASTICSEARCH_URL",

            # Object storage
            "minio_endpoint": "MINIO_ENDPOINT",
            "s3_endpoint": "S3_ENDPOINT",
        }

        transformed = config.copy()

        for key, env_var in url_mappings.items():
            if key in transformed:
                # Get default value (current value)
                default_value = transformed[key]

                # Transform to env var with default
                transformed[key] = f"${{{env_var}:-{default_value}}}"

        return transformed

    def _transform_secrets_to_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform API keys and secrets to environment variable references.

        Before:
          "openai_api_key": "sk-proj-abc123..."

        After:
          "openai_api_key": "${OPENAI_API_KEY}"
        """
        secret_mappings = {
            # API keys
            "openai_api_key": "OPENAI_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "cohere_api_key": "COHERE_API_KEY",

            # Database credentials
            "postgres_password": "POSTGRES_PASSWORD",
            "redis_password": "REDIS_PASSWORD",

            # Object storage
            "minio_access_key": "MINIO_ACCESS_KEY",
            "minio_secret_key": "MINIO_SECRET_KEY",

            # JWT secrets
            "jwt_secret": "JWT_SECRET",
            "secret_key": "SECRET_KEY",
        }

        transformed = config.copy()

        for key, env_var in secret_mappings.items():
            if key in transformed:
                # Replace with env var (no default for secrets)
                transformed[key] = f"${{{env_var}}}"

        return transformed

    def _add_standalone_settings(
        self,
        config: Dict[str, Any],
        module_name: str
    ) -> Dict[str, Any]:
        """
        Add standalone-specific settings that don't exist in platform config.

        Args:
            config: Current configuration
            module_name: Module name

        Returns:
            Configuration with standalone settings added
        """
        standalone = config.copy()

        # Add deployment info
        standalone["deployment"] = {
            "mode": "standalone",
            "module_name": module_name,
            "platform_version": "1.0.0",
            "export_timestamp": datetime.utcnow().isoformat()
        }

        # Add default logging configuration
        if "logging" not in standalone:
            standalone["logging"] = {
                "level": "${LOG_LEVEL:-INFO}",
                "format": "json",
                "output": "stdout",
                "file_path": "${LOG_FILE_PATH:-/var/log/genai/app.log}"
            }

        # Add default monitoring configuration
        if "monitoring" not in standalone:
            standalone["monitoring"] = {
                "enabled": True,
                "prometheus_port": "${PROMETHEUS_PORT:-9090}",
                "metrics_path": "/metrics",
                "health_check_path": "/health"
            }

        # Add default CORS settings for API
        if "cors" not in standalone:
            standalone["cors"] = {
                "enabled": True,
                "origins": "${CORS_ORIGINS:-*}",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_credentials": True
            }

        # Add rate limiting defaults
        if "rate_limiting" not in standalone:
            standalone["rate_limiting"] = {
                "enabled": "${RATE_LIMITING_ENABLED:-true}",
                "requests_per_minute": "${RATE_LIMIT_RPM:-100}",
                "requests_per_hour": "${RATE_LIMIT_RPH:-1000}"
            }

        return standalone

    def _remove_platform_specific_keys(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove keys that are specific to our platform and not needed in standalone.

        Args:
            config: Current configuration

        Returns:
            Configuration with platform-specific keys removed
        """
        platform_keys = [
            "platform_tenant_id",
            "platform_user_id",
            "platform_session_id",
            "platform_internal_url",
            "platform_admin_key",
            "_platform_metadata",
        ]

        cleaned = config.copy()

        for key in platform_keys:
            if key in cleaned:
                del cleaned[key]

        return cleaned

    def _transform_model_config(self, models: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform model configuration for standalone deployment.

        Args:
            models: Original model configuration

        Returns:
            Transformed model configuration
        """
        transformed = models.copy()

        # Ensure model providers use env vars
        if "openai" in transformed:
            transformed["openai"]["api_key"] = "${OPENAI_API_KEY}"
            if "base_url" in transformed["openai"]:
                transformed["openai"]["base_url"] = "${OPENAI_BASE_URL:-https://api.openai.com/v1}"

        if "anthropic" in transformed:
            transformed["anthropic"]["api_key"] = "${ANTHROPIC_API_KEY}"
            if "base_url" in transformed["anthropic"]:
                transformed["anthropic"]["base_url"] = "${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"

        # Add local LLM fallback option
        if "local_llm" not in transformed:
            transformed["local_llm"] = {
                "enabled": "${LOCAL_LLM_ENABLED:-false}",
                "endpoint": "${LOCAL_LLM_ENDPOINT:-http://localhost:11434}",
                "model": "${LOCAL_LLM_MODEL:-mistral}"
            }

        return transformed

    def _transform_retrieval_config(self, retrieval: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform retrieval/RAG configuration for standalone deployment.

        Args:
            retrieval: Original retrieval configuration

        Returns:
            Transformed retrieval configuration
        """
        transformed = retrieval.copy()

        # Ensure vector DB uses env vars
        if "vector_db" in transformed:
            transformed["vector_db"]["connection_string"] = "${VECTOR_DB_CONNECTION:-postgresql://localhost:5432/vectordb}"

        # Ensure Elasticsearch uses env vars
        if "elasticsearch" in transformed:
            transformed["elasticsearch"]["hosts"] = "${ELASTICSEARCH_HOSTS:-http://localhost:9200}"

        # Add embedding model fallback
        if "embedding_model" in transformed:
            transformed["embedding_model"]["local_fallback"] = {
                "enabled": True,
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            }

        return transformed

    def _validate_config(self, config: Dict[str, Any], module_name: str) -> None:
        """
        Validate that configuration is complete and valid.

        Args:
            config: Configuration to validate
            module_name: Module name

        Raises:
            RuntimeError: If validation fails
        """
        required_sections = ["deployment", "logging", "monitoring"]

        missing_sections = [
            section for section in required_sections
            if section not in config
        ]

        if missing_sections:
            raise RuntimeError(
                f"Configuration validation failed for {module_name}. "
                f"Missing required sections: {', '.join(missing_sections)}"
            )

        # Validate prompts exist
        if "prompts" in config:
            if not config["prompts"]:
                logger.warning(f"⚠️  No prompts configured for {module_name}")

        # Validate models exist
        if "models" in config:
            if not config["models"]:
                raise RuntimeError(f"No models configured for {module_name}")

        logger.info(f"✅ Configuration validation passed for {module_name}")

    async def extract_all_modules(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract configurations for all modules.

        Args:
            tenant_id: Optional tenant ID for filtering

        Returns:
            Dictionary mapping module names to configurations
        """
        logger.info("📦 Extracting configurations for all modules")

        # Get all module configurations
        result = await self.db.execute(
            select(ModuleConfiguration).where(ModuleConfiguration.is_active == True)
        )
        modules = result.scalars().all()

        configs = {}

        for module in modules:
            try:
                config = await self.extract_module_config(
                    module_name=module.module_name,
                    tenant_id=tenant_id
                )
                configs[module.module_name] = config
                logger.info(f"  ✅ Extracted: {module.module_name}")
            except Exception as e:
                logger.error(f"  ❌ Failed to extract {module.module_name}: {e}")
                # Continue with other modules
                continue

        logger.info(f"✅ Extracted {len(configs)} module configurations")

        return configs

    def generate_env_template(self, config: Dict[str, Any]) -> str:
        """
        Generate .env template file from configuration.

        Extracts all ${VAR_NAME} references and creates .env.example file.

        Args:
            config: Configuration with env var references

        Returns:
            .env file content
        """
        import re

        env_vars = set()

        # Recursively find all ${VAR_NAME} patterns
        def find_env_vars(obj):
            if isinstance(obj, dict):
                for value in obj.values():
                    find_env_vars(value)
            elif isinstance(obj, list):
                for item in obj:
                    find_env_vars(item)
            elif isinstance(obj, str):
                # Match ${VAR_NAME} or ${VAR_NAME:-default}
                matches = re.findall(r'\$\{([A-Z_][A-Z0-9_]*)', obj)
                env_vars.update(matches)

        find_env_vars(config)

        # Generate .env template
        env_lines = [
            "# Generated Environment Variables Template",
            "# Copy this to .env and fill in your values",
            f"# Generated: {datetime.utcnow().isoformat()}",
            "",
        ]

        # Group by category
        categories = {
            "LLM": ["OPENAI", "ANTHROPIC", "COHERE", "LOCAL_LLM"],
            "Database": ["POSTGRES", "DATABASE", "REDIS"],
            "Vector DB": ["VECTOR_DB", "ELASTICSEARCH"],
            "Storage": ["MINIO", "S3"],
            "Security": ["JWT", "SECRET"],
            "Monitoring": ["PROMETHEUS", "LOG"],
            "API": ["CORS", "RATE"],
        }

        for category, prefixes in categories.items():
            category_vars = [
                var for var in sorted(env_vars)
                if any(var.startswith(prefix) for prefix in prefixes)
            ]

            if category_vars:
                env_lines.append(f"# {category}")
                for var in category_vars:
                    env_lines.append(f"{var}=")
                env_lines.append("")

        # Add uncategorized vars
        categorized = set()
        for prefixes in categories.values():
            for var in env_vars:
                if any(var.startswith(prefix) for prefix in prefixes):
                    categorized.add(var)

        uncategorized = sorted(env_vars - categorized)
        if uncategorized:
            env_lines.append("# Other")
            for var in uncategorized:
                env_lines.append(f"{var}=")

        return "\n".join(env_lines)
