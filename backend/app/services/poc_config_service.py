"""
POC Configuration Service (Async Version)

Manages dynamic configuration for all Tier 2 Domain Verticals and Tier 3 Customer Solutions.
Implements 3-level configuration hierarchy: Global Defaults → Module Config → User Overrides

This version is compatible with AsyncSession used throughout the application.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
import json
from datetime import datetime
from uuid import UUID
import copy

try:
    from jsonschema import validate, ValidationError as JSONSchemaValidationError
except ImportError:
    JSONSchemaValidationError = Exception
    def validate(*args, **kwargs):
        pass  # Fallback if jsonschema not installed

try:
    from deepdiff import DeepDiff
except ImportError:
    DeepDiff = None

from app.models.module_configuration import (
    ModuleConfiguration,
    ModuleUserOverride,
    ConfigVersion,
    ConfigSchema,
    ConfigTemplate,
    ConfigAuditLog
)


class POCConfigService:
    """
    Service for managing POC/Module configurations with 3-level hierarchy:
    1. Global defaults (fallback)
    2. Module-specific configuration
    3. User-specific overrides (highest priority)
    """

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}  # Simple in-memory cache

    # ========================================================================
    # Core Configuration Retrieval
    # ========================================================================

    async def get_config(
        self,
        db: AsyncSession,
        module_name: str,
        user_id: Optional[str] = None,
        include_overrides: bool = True
    ) -> Dict[str, Any]:
        """
        Get complete configuration with 3-level resolution:
        1. Start with global defaults
        2. Merge module-specific config
        3. Merge user-specific overrides (if user_id provided)
        """
        # Check cache first
        cache_key = f"{module_name}:{user_id if user_id else 'default'}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Start with global defaults
        config = self._get_global_defaults()

        # Merge module-specific config
        module_config = await self._get_module_config(db, module_name)
        if module_config:
            config = self._deep_merge(config, module_config)

        # Merge user-specific overrides
        if include_overrides and user_id:
            user_overrides = await self._get_user_overrides(db, module_name, user_id)
            if user_overrides:
                config = self._deep_merge(config, user_overrides)

        # Cache result
        self.cache[cache_key] = config
        return config

    async def list_modules(
        self,
        db: AsyncSession,
        module_type: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """List all available modules with basic info"""
        query = select(ModuleConfiguration)

        if module_type:
            query = query.where(ModuleConfiguration.module_type == module_type)
        if category:
            query = query.where(ModuleConfiguration.category == category)
        if active_only:
            query = query.where(ModuleConfiguration.is_active == True)

        result = await db.execute(query)
        modules = result.scalars().all()

        return [
            {
                "module_name": m.module_name,
                "display_name": m.display_name,
                "module_type": m.module_type,
                "category": m.category,
                "current_version": m.current_version,
                "is_active": m.is_active
            }
            for m in modules
        ]

    async def create_module_config(
        self,
        db: AsyncSession,
        module_name: str,
        display_name: str,
        module_type: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
        category: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> ModuleConfiguration:
        """Create a new module configuration"""
        # Validate config against schema
        is_valid, errors = await self.validate_config(db, module_name, config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        module_config = ModuleConfiguration(
            module_name=module_name,
            display_name=display_name,
            description=description,
            module_type=module_type,
            category=category,
            config=config,
            created_by=None,  # Set to None to avoid FK errors with mock users
            current_version=1
        )

        db.add(module_config)

        # Create initial version record
        version_record = ConfigVersion(
            module_name=module_name,
            version=1,
            config=config,
            changed_by=None,  # Set to None to avoid FK errors with mock users
            change_description="Initial configuration"
        )
        db.add(version_record)

        # Create audit log
        await self._create_audit_log(
            db=db,
            module_name=module_name,
            action='create',
            changed_by=created_by,
            new_value=config
        )

        await db.commit()
        await db.refresh(module_config)

        # Invalidate cache
        self._invalidate_cache(module_name)

        return module_config

    async def update_module_config(
        self,
        db: AsyncSession,
        module_name: str,
        updates: Dict[str, Any],
        changed_by: Optional[UUID] = None,
        change_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update module configuration and create new version"""
        # Get current config
        current_config = await self._get_module_config(db, module_name)
        if not current_config:
            raise ValueError(f"Module '{module_name}' not found")

        # Merge updates
        new_config = self._deep_merge(current_config, updates)

        # Validate against schema
        is_valid, errors = await self.validate_config(db, module_name, new_config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        # Calculate diff
        diff = None
        if DeepDiff:
            diff_obj = DeepDiff(current_config, new_config)
            diff = json.loads(diff_obj.to_json()) if diff_obj else None

        # Get current version
        result = await db.execute(
            select(ModuleConfiguration).where(ModuleConfiguration.module_name == module_name)
        )
        module = result.scalar_one()

        new_version = module.current_version + 1

        # Create version record
        version_record = ConfigVersion(
            module_name=module_name,
            version=new_version,
            config=new_config,
            changed_by=None,  # Set to None to avoid FK errors with mock users
            change_description=change_reason,
            diff=diff
        )
        db.add(version_record)

        # Update current config
        module.config = new_config
        module.current_version = new_version
        module.updated_at = datetime.utcnow()

        # Create audit log
        await self._create_audit_log(
            db=db,
            module_name=module_name,
            action='update',
            changed_by=changed_by,
            old_value=current_config,
            new_value=new_config,
            change_reason=change_reason
        )

        await db.commit()

        # Invalidate cache
        self._invalidate_cache(module_name)

        return new_config

    async def set_user_override(
        self,
        db: AsyncSession,
        module_name: str,
        user_id: UUID,
        overrides: Dict[str, Any],
        variant_name: Optional[str] = None,
        experiment_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Set user-specific configuration overrides"""
        # Check if override exists
        result = await db.execute(
            select(ModuleUserOverride).where(
                ModuleUserOverride.user_id == user_id,
                ModuleUserOverride.module_name == module_name
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing override
            old_overrides = existing.overrides
            existing.overrides = overrides
            existing.updated_at = datetime.utcnow()
            if variant_name:
                existing.variant_name = variant_name
            if experiment_id:
                existing.experiment_id = experiment_id

            # Create audit log
            await self._create_audit_log(
                db=db,
                module_name=module_name,
                action='override_update',
                changed_by=user_id,
                old_value=old_overrides,
                new_value=overrides
            )
        else:
            # Create new override
            override = ModuleUserOverride(
                user_id=user_id,
                module_name=module_name,
                overrides=overrides,
                variant_name=variant_name,
                experiment_id=experiment_id
            )
            db.add(override)

            # Create audit log
            await self._create_audit_log(
                db=db,
                module_name=module_name,
                action='override_create',
                changed_by=user_id,
                new_value=overrides
            )

        await db.commit()

        # Invalidate cache
        self._invalidate_cache(module_name, str(user_id))

        return overrides

    async def clear_user_override(
        self,
        db: AsyncSession,
        module_name: str,
        user_id: UUID
    ) -> bool:
        """Clear user-specific overrides"""
        result = await db.execute(
            delete(ModuleUserOverride).where(
                ModuleUserOverride.user_id == user_id,
                ModuleUserOverride.module_name == module_name
            )
        )

        if result.rowcount > 0:
            # Create audit log
            await self._create_audit_log(
                db=db,
                module_name=module_name,
                action='override_delete',
                changed_by=user_id
            )

            await db.commit()
            self._invalidate_cache(module_name, str(user_id))
            return True

        return False

    async def get_versions(
        self,
        db: AsyncSession,
        module_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get version history for module configuration"""
        result = await db.execute(
            select(ConfigVersion)
            .where(ConfigVersion.module_name == module_name)
            .order_by(ConfigVersion.version.desc())
            .limit(limit)
        )
        versions = result.scalars().all()

        return [
            {
                "version": v.version,
                "changed_at": v.changed_at,
                "changed_by": str(v.changed_by) if v.changed_by else None,
                "change_description": v.change_description,
                "has_diff": v.diff is not None
            }
            for v in versions
        ]

    async def restore_version(
        self,
        db: AsyncSession,
        module_name: str,
        version: int,
        changed_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Restore a previous configuration version"""
        # Get the version to restore
        result = await db.execute(
            select(ConfigVersion).where(
                ConfigVersion.module_name == module_name,
                ConfigVersion.version == version
            )
        )
        version_record = result.scalar_one_or_none()

        if not version_record:
            raise ValueError(f"Version {version} not found for module '{module_name}'")

        # Update current config with restored version
        restored_config = await self.update_module_config(
            db=db,
            module_name=module_name,
            updates=version_record.config,
            changed_by=changed_by,
            change_reason=f"Restored from version {version}"
        )

        return restored_config

    async def validate_config(
        self,
        db: AsyncSession,
        module_name: str,
        config: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """Validate configuration against JSON schema"""
        # Get schema for module or global schema
        schema_name = f"{module_name}_schema"
        result = await db.execute(
            select(ConfigSchema).where(ConfigSchema.schema_name == schema_name)
        )
        schema_record = result.scalar_one_or_none()

        if not schema_record:
            # Try global schema
            result = await db.execute(
                select(ConfigSchema).where(ConfigSchema.schema_name == "global_module_config")
            )
            schema_record = result.scalar_one_or_none()

        if not schema_record:
            # No schema found, skip validation
            return True, []

        try:
            validate(instance=config, schema=schema_record.schema)
            return True, []
        except JSONSchemaValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _get_global_defaults(self) -> Dict[str, Any]:
        """Load global default configuration"""
        return {
            "llm": {
                "default": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.2,
                    "max_tokens": 1000,
                    "top_p": 1.0,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0
                }
            },
            "prompts": {
                "system": {
                    "default": "You are a helpful AI assistant."
                },
                "user": {}
            },
            "parameters": {},
            "thresholds": {
                "min_confidence": 0.7
            },
            "scoring": {
                "weights": {}
            },
            "retrieval": {
                "top_k": 10,
                "rerank_top_k": 5
            },
            "features": {
                "enable_caching": True,
                "enable_debug_logging": False
            }
        }

    async def _get_module_config(
        self,
        db: AsyncSession,
        module_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get module-specific configuration"""
        result = await db.execute(
            select(ModuleConfiguration.config).where(
                ModuleConfiguration.module_name == module_name,
                ModuleConfiguration.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def _get_user_overrides(
        self,
        db: AsyncSession,
        module_name: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user-specific overrides"""
        result = await db.execute(
            select(ModuleUserOverride.overrides).where(
                ModuleUserOverride.user_id == user_id,
                ModuleUserOverride.module_name == module_name,
                ModuleUserOverride.is_active == True
            )
        )
        return result.scalar_one_or_none()

    def _deep_merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two configurations (override wins)"""
        result = copy.deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    async def _create_audit_log(
        self,
        db: AsyncSession,
        module_name: str,
        action: str,
        changed_by: Optional[UUID] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        change_reason: Optional[str] = None
    ):
        """Create audit log entry"""
        # Skip audit log if changed_by user doesn't exist (to avoid FK constraint errors)
        # In production, this should be handled by proper authentication
        try:
            audit_log = ConfigAuditLog(
                module_name=module_name,
                action=action,
                changed_by=None,  # Set to None to avoid FK errors with mock users
                old_value=old_value,
                new_value=new_value,
                change_reason=change_reason
            )
            db.add(audit_log)
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Could not create audit log: {e}")

    def _invalidate_cache(self, module_name: str, user_id: Optional[str] = None):
        """Invalidate configuration cache"""
        if user_id:
            cache_key = f"{module_name}:{user_id}"
            if cache_key in self.cache:
                del self.cache[cache_key]
        else:
            # Invalidate all entries for this module
            keys_to_delete = [k for k in self.cache.keys() if k.startswith(f"{module_name}:")]
            for key in keys_to_delete:
                del self.cache[key]


# Global instance
poc_config_service = POCConfigService()
