"""
Model Registry Sync Service

Automatically discovers and registers Ollama models in the database.
Syncs with Ollama API periodically to keep the models registry up-to-date.

Features:
- Auto-discovery of installed Ollama models
- Sync with database models table
- Mark models as auto_discovered
- Periodic sync (configurable interval via system_config)
- Model metadata extraction (size, modified date, etc.)

Author: AI Assistant
Date: 2026-01-07
Related: Phase 2 - Requirement #2 (Ollama Auto-Registration)
"""

import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.models.database import Model, SystemConfig
from app.services.ollama_model_service import OllamaModelService, OllamaModel
from app.core.database import get_db

logger = logging.getLogger(__name__)


class ModelRegistrySyncService:
    """Service for syncing Ollama models with database registry"""

    def __init__(self, db: AsyncSession):
        """
        Initialize model registry sync service.

        Args:
            db: Database session
        """
        self.db = db
        self.ollama_service = OllamaModelService()

    async def get_sync_interval(self) -> int:
        """
        Get sync interval from system config.

        Returns:
            Sync interval in seconds (default: 60)
        """
        try:
            result = await self.db.execute(
                select(SystemConfig).where(
                    SystemConfig.config_key == 'ollama.sync_interval_seconds',
                    SystemConfig.is_active == True
                )
            )
            config = result.scalar_one_or_none()

            if config:
                return int(config.config_value)

            return 60  # Default: 60 seconds

        except Exception as e:
            logger.warning(f"Failed to get sync interval from config: {e}. Using default 60s")
            return 60

    async def is_auto_discovery_enabled(self) -> bool:
        """
        Check if Ollama auto-discovery is enabled.

        Returns:
            True if enabled, False otherwise
        """
        try:
            result = await self.db.execute(
                select(SystemConfig).where(
                    SystemConfig.config_key == 'ollama.auto_discovery_enabled',
                    SystemConfig.is_active == True
                )
            )
            config = result.scalar_one_or_none()

            if config:
                return config.config_value.lower() in ('true', '1', 'yes', 'on')

            return True  # Default: enabled

        except Exception as e:
            logger.warning(f"Failed to check auto-discovery status: {e}. Defaulting to enabled")
            return True

    def _infer_model_type(self, model_name: str) -> str:
        """
        Infer model type from name.

        Args:
            model_name: Model name (e.g., 'llama2:latest', 'qwen2.5-coder:7b')

        Returns:
            Model type: 'code', 'vision', or 'text'
        """
        name_lower = model_name.lower()

        # Code models
        if any(keyword in name_lower for keyword in ['coder', 'code', 'deepseek', 'codellama', 'starcoder']):
            return 'code'

        # Vision models
        if any(keyword in name_lower for keyword in ['llava', 'bakllava', 'vision']):
            return 'vision'

        # Default to text
        return 'text'

    def _extract_display_name(self, ollama_model: OllamaModel) -> str:
        """
        Extract human-readable display name from Ollama model.

        Args:
            ollama_model: Ollama model object

        Returns:
            Display name
        """
        # Try to create a nice display name
        # e.g., "qwen2.5-coder:7b" → "Qwen 2.5 Coder 7B"
        name = ollama_model.name

        # Replace dashes and underscores with spaces
        display = name.replace('-', ' ').replace('_', ' ').replace(':', ' ')

        # Capitalize words
        display = ' '.join(word.capitalize() for word in display.split())

        return display

    async def sync_ollama_models(self) -> Dict[str, Any]:
        """
        Sync Ollama models with database registry.

        Fetches installed models from Ollama and upserts them into the models table.

        Returns:
            Dictionary with sync stats:
            - total_discovered: Total models found in Ollama
            - new_models: Newly added models
            - updated_models: Updated existing models
            - errors: List of errors encountered
        """
        stats = {
            'total_discovered': 0,
            'new_models': 0,
            'updated_models': 0,
            'errors': []
        }

        try:
            # Check if auto-discovery is enabled
            if not await self.is_auto_discovery_enabled():
                logger.info("Ollama auto-discovery is disabled in system config")
                return stats

            # Health check Ollama
            is_healthy = await self.ollama_service.health_check()
            if not is_healthy:
                error_msg = "Ollama service is not accessible"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                return stats

            # Fetch installed models from Ollama
            ollama_models = await self.ollama_service.list_installed_models()
            stats['total_discovered'] = len(ollama_models)

            logger.info(f"Found {len(ollama_models)} models in Ollama")

            # Sync each model
            for ollama_model in ollama_models:
                try:
                    model_type = self._infer_model_type(ollama_model.name)
                    display_name = self._extract_display_name(ollama_model)

                    # Build metadata
                    meta_info = {
                        'size_bytes': ollama_model.size,
                        'size_gb': ollama_model.size_gb,
                        'digest': ollama_model.digest,
                        'modified_at': ollama_model.modified_at,
                        'family': ollama_model.family,
                        'tag': ollama_model.tag
                    }

                    # Upsert into models table
                    stmt = insert(Model).values(
                        model_id=ollama_model.name,
                        display_name=display_name,
                        provider='ollama',
                        model_type=model_type,
                        is_active=True,
                        source='auto_discovered',
                        auto_discovered_at=datetime.now(timezone.utc),
                        last_verified_at=datetime.now(timezone.utc),
                        meta_info=meta_info,
                        supports_streaming=True  # Ollama models support streaming
                    )

                    # On conflict, update metadata and verification timestamp
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['model_id'],
                        set_={
                            'display_name': display_name,
                            'model_type': model_type,
                            'is_active': True,
                            'last_verified_at': datetime.now(timezone.utc),
                            'meta_info': meta_info,
                            'updated_at': datetime.now(timezone.utc)
                        }
                    )

                    result = await self.db.execute(stmt)

                    # Check if insert or update
                    if result.rowcount > 0:
                        # Query to see if this was a new insert
                        check_result = await self.db.execute(
                            select(Model).where(
                                Model.model_id == ollama_model.name,
                                Model.source == 'auto_discovered',
                                Model.auto_discovered_at >= datetime.now(timezone.utc).replace(microsecond=0)
                            )
                        )
                        if check_result.scalar_one_or_none():
                            stats['new_models'] += 1
                            logger.info(f"✅ New model discovered: {ollama_model.name}")
                        else:
                            stats['updated_models'] += 1
                            logger.debug(f"♻️  Updated model: {ollama_model.name}")

                except Exception as e:
                    error_msg = f"Failed to sync model {ollama_model.name}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

            # Commit transaction
            await self.db.commit()

            logger.info(
                f"Ollama sync completed: {stats['new_models']} new, "
                f"{stats['updated_models']} updated, {len(stats['errors'])} errors"
            )

        except Exception as e:
            error_msg = f"Unexpected error during Ollama sync: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            await self.db.rollback()

        return stats

    async def mark_missing_models_inactive(self) -> int:
        """
        Mark auto-discovered models as inactive if they're no longer in Ollama.

        Returns:
            Number of models marked inactive
        """
        try:
            # Get current Ollama models
            ollama_models = await self.ollama_service.list_installed_models()
            ollama_model_ids = {model.name for model in ollama_models}

            # Get all auto-discovered models from database
            result = await self.db.execute(
                select(Model).where(
                    Model.provider == 'ollama',
                    Model.source == 'auto_discovered',
                    Model.is_active == True
                )
            )
            db_models = result.scalars().all()

            # Find models in DB but not in Ollama
            missing_count = 0
            for db_model in db_models:
                if db_model.model_id not in ollama_model_ids:
                    db_model.is_active = False
                    db_model.updated_at = datetime.now(timezone.utc)
                    missing_count += 1
                    logger.warning(f"Model no longer in Ollama, marking inactive: {db_model.model_id}")

            if missing_count > 0:
                await self.db.commit()
                logger.info(f"Marked {missing_count} missing models as inactive")

            return missing_count

        except Exception as e:
            logger.error(f"Failed to mark missing models inactive: {e}")
            await self.db.rollback()
            return 0

    async def run_once(self) -> Dict[str, Any]:
        """
        Run a single sync cycle.

        Returns:
            Sync statistics
        """
        logger.info("Starting Ollama model registry sync (one-time)")

        stats = await self.sync_ollama_models()

        # Optionally mark missing models as inactive
        try:
            missing_count = await self.mark_missing_models_inactive()
            stats['models_marked_inactive'] = missing_count
        except Exception as e:
            logger.warning(f"Failed to mark missing models inactive: {e}")
            stats['models_marked_inactive'] = 0

        return stats

    async def run_continuous(self):
        """
        Run continuous background sync with configurable interval.

        This method runs indefinitely, syncing models at regular intervals.
        Should be run in a background task or separate process.
        """
        logger.info("Starting Ollama model registry continuous sync service")

        while True:
            try:
                # Get sync interval
                interval = await self.get_sync_interval()

                # Run sync
                stats = await self.run_once()
                logger.info(f"Sync completed. Next sync in {interval} seconds. Stats: {stats}")

                # Wait for next sync
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Model registry sync service cancelled")
                break
            except Exception as e:
                logger.error(f"Error in continuous sync: {e}. Retrying in 60 seconds...")
                await asyncio.sleep(60)


# Dependency injection helper
async def get_model_registry_sync_service(db: AsyncSession) -> ModelRegistrySyncService:
    """
    Get instance of ModelRegistrySyncService.

    Args:
        db: Database session

    Returns:
        ModelRegistrySyncService instance
    """
    return ModelRegistrySyncService(db)


# Standalone async function for background execution
async def run_background_sync():
    """
    Run model registry sync as a standalone background service.

    This function can be called from:
    1. Docker Compose service
    2. Celery task
    3. FastAPI background task
    4. Separate Python process
    """
    logger.info("Initializing standalone model registry sync service")

    # Get database session
    async for db in get_db():
        service = ModelRegistrySyncService(db)
        await service.run_continuous()


if __name__ == "__main__":
    """
    Run service standalone for testing:
    python -m app.services.model_registry_sync_service
    """
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )

    logger.info("Starting Model Registry Sync Service (standalone mode)")

    try:
        asyncio.run(run_background_sync())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service crashed: {e}")
        sys.exit(1)
