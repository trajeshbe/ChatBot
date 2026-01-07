"""
System Configuration Service

Provides easy access to database-driven system configuration.
Replaces hardcoded values with dynamic configuration from system_config table.

Features:
- Type-safe configuration retrieval
- Caching for performance
- Default values
- Type conversion (string, int, bool, json)

Author: AI Assistant
Date: 2026-01-07
Related: Phase 2 - Requirement #8 (Agent Runtime API from Database)
"""

import logging
import json
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import SystemConfig

logger = logging.getLogger(__name__)


class SystemConfigService:
    """Service for reading system configuration from database"""

    # Simple in-memory cache (TTL: 60 seconds)
    _cache: Dict[str, tuple[Any, datetime]] = {}
    _cache_ttl = 60  # seconds

    def __init__(self, db: AsyncSession):
        """
        Initialize system config service.

        Args:
            db: Database session
        """
        self.db = db

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Config key

        Returns:
            Cached value or None if not found/expired
        """
        if key in self._cache:
            value, cached_at = self._cache[key]
            if datetime.now() - cached_at < timedelta(seconds=self._cache_ttl):
                return value

            # Expired, remove from cache
            del self._cache[key]

        return None

    def _set_cache(self, key: str, value: Any):
        """
        Set value in cache.

        Args:
            key: Config key
            value: Value to cache
        """
        self._cache[key] = (value, datetime.now())

    async def get(
        self,
        key: str,
        default: Optional[Any] = None,
        use_cache: bool = True
    ) -> Optional[Any]:
        """
        Get configuration value as string.

        Args:
            key: Configuration key (e.g., 'agent.runtime.default_model')
            default: Default value if key not found
            use_cache: Whether to use cache (default: True)

        Returns:
            Configuration value or default
        """
        # Check cache first
        if use_cache:
            cached = self._get_from_cache(key)
            if cached is not None:
                return cached

        try:
            result = await self.db.execute(
                select(SystemConfig).where(
                    SystemConfig.config_key == key,
                    SystemConfig.is_active == True
                )
            )
            config = result.scalar_one_or_none()

            if config:
                value = config.config_value
                self._set_cache(key, value)
                return value

            return default

        except Exception as e:
            logger.error(f"Failed to get config '{key}': {e}")
            return default

    async def get_int(
        self,
        key: str,
        default: Optional[int] = None,
        use_cache: bool = True
    ) -> Optional[int]:
        """
        Get configuration value as integer.

        Args:
            key: Configuration key
            default: Default value if key not found or conversion fails
            use_cache: Whether to use cache

        Returns:
            Configuration value as int or default
        """
        value = await self.get(key, default=None, use_cache=use_cache)

        if value is None:
            return default

        try:
            return int(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert config '{key}' to int: {e}. Using default: {default}")
            return default

    async def get_float(
        self,
        key: str,
        default: Optional[float] = None,
        use_cache: bool = True
    ) -> Optional[float]:
        """
        Get configuration value as float.

        Args:
            key: Configuration key
            default: Default value if key not found or conversion fails
            use_cache: Whether to use cache

        Returns:
            Configuration value as float or default
        """
        value = await self.get(key, default=None, use_cache=use_cache)

        if value is None:
            return default

        try:
            return float(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert config '{key}' to float: {e}. Using default: {default}")
            return default

    async def get_bool(
        self,
        key: str,
        default: Optional[bool] = None,
        use_cache: bool = True
    ) -> Optional[bool]:
        """
        Get configuration value as boolean.

        Args:
            key: Configuration key
            default: Default value if key not found or conversion fails
            use_cache: Whether to use cache

        Returns:
            Configuration value as bool or default
        """
        value = await self.get(key, default=None, use_cache=use_cache)

        if value is None:
            return default

        if isinstance(value, bool):
            return value

        # Convert string to bool
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ('true', '1', 'yes', 'on', 't', 'y'):
                return True
            elif value_lower in ('false', '0', 'no', 'off', 'f', 'n'):
                return False

        logger.warning(f"Failed to convert config '{key}' to bool: {value}. Using default: {default}")
        return default

    async def get_json(
        self,
        key: str,
        default: Optional[Any] = None,
        use_cache: bool = True
    ) -> Optional[Any]:
        """
        Get configuration value as JSON (dict or list).

        Args:
            key: Configuration key
            default: Default value if key not found or JSON parse fails
            use_cache: Whether to use cache

        Returns:
            Configuration value as parsed JSON or default
        """
        value = await self.get(key, default=None, use_cache=use_cache)

        if value is None:
            return default

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse config '{key}' as JSON: {e}. Using default: {default}")
            return default

    async def get_by_category(
        self,
        category: str,
        active_only: bool = True
    ) -> List[SystemConfig]:
        """
        Get all configuration values for a category.

        Args:
            category: Category name (e.g., 'agent', 'ollama', 'embedding')
            active_only: Only return active configs (default: True)

        Returns:
            List of SystemConfig objects
        """
        try:
            query = select(SystemConfig).where(SystemConfig.category == category)

            if active_only:
                query = query.where(SystemConfig.is_active == True)

            result = await self.db.execute(query.order_by(SystemConfig.config_key))
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get configs for category '{category}': {e}")
            return []

    async def set(
        self,
        key: str,
        value: Any,
        config_type: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> bool:
        """
        Set configuration value (upsert).

        Args:
            key: Configuration key
            value: Configuration value
            config_type: Type of config (string, integer, boolean, json, url, api_key)
            description: Description of the config
            category: Category (agent, embedding, ollama, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert value to string
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
                config_type = config_type or 'json'
            elif isinstance(value, bool):
                value_str = str(value).lower()
                config_type = config_type or 'boolean'
            elif isinstance(value, int):
                value_str = str(value)
                config_type = config_type or 'integer'
            elif isinstance(value, float):
                value_str = str(value)
                config_type = config_type or 'string'
            else:
                value_str = str(value)
                config_type = config_type or 'string'

            # Check if exists
            result = await self.db.execute(
                select(SystemConfig).where(SystemConfig.config_key == key)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update
                existing.config_value = value_str
                if config_type:
                    existing.config_type = config_type
                if description:
                    existing.description = description
                if category:
                    existing.category = category
                existing.updated_at = datetime.now()
            else:
                # Insert
                new_config = SystemConfig(
                    config_key=key,
                    config_value=value_str,
                    config_type=config_type or 'string',
                    description=description,
                    category=category,
                    is_active=True
                )
                self.db.add(new_config)

            await self.db.commit()

            # Clear cache for this key
            if key in self._cache:
                del self._cache[key]

            return True

        except Exception as e:
            logger.error(f"Failed to set config '{key}': {e}")
            await self.db.rollback()
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete configuration (mark as inactive).

        Args:
            key: Configuration key

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.execute(
                select(SystemConfig).where(SystemConfig.config_key == key)
            )
            config = result.scalar_one_or_none()

            if config:
                config.is_active = False
                config.updated_at = datetime.now()
                await self.db.commit()

                # Clear cache
                if key in self._cache:
                    del self._cache[key]

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete config '{key}': {e}")
            await self.db.rollback()
            return False

    @classmethod
    def clear_cache(cls):
        """Clear all cached configuration values."""
        cls._cache.clear()
        logger.info("System config cache cleared")


# Dependency injection helper
async def get_system_config_service(db: AsyncSession) -> SystemConfigService:
    """
    Get instance of SystemConfigService.

    Args:
        db: Database session

    Returns:
        SystemConfigService instance
    """
    return SystemConfigService(db)
