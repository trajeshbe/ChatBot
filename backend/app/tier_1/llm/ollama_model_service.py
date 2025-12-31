"""
Ollama Model Management Service

This service provides functionality to manage Ollama models via the Ollama HTTP API.
Supports listing installed models, getting model details, and checking running models.

Phase 1: Read-Only Operations
- List installed models
- Get model details
- Get running models

Phase 2: Model Management (Future)
- Pull/install new models
- Remove models
- Monitor download progress

Author: AI Assistant
Date: 2025-11-20
"""

import logging
import json
from typing import List, Dict, Optional, Any, AsyncIterator
from datetime import datetime
import httpx
from pydantic import BaseModel, Field

from app.tier_1.infrastructure.config import Settings

logger = logging.getLogger(__name__)


# Pydantic models for request/response validation
class OllamaModel(BaseModel):
    """Represents an installed Ollama model."""
    name: str = Field(..., description="Model name (e.g., 'llama2:latest')")
    model: str = Field(..., description="Full model identifier")
    modified_at: str = Field(..., description="Last modification timestamp")
    size: int = Field(..., description="Model size in bytes")
    digest: str = Field(..., description="Model digest/hash")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional model details")

    @property
    def size_gb(self) -> float:
        """Get model size in GB."""
        return round(self.size / (1024 ** 3), 2)

    @property
    def size_mb(self) -> float:
        """Get model size in MB."""
        return round(self.size / (1024 ** 2), 2)

    @property
    def family(self) -> str:
        """Extract model family from name (e.g., 'llama2' from 'llama2:latest')."""
        return self.name.split(":")[0] if ":" in self.name else self.name

    @property
    def tag(self) -> str:
        """Extract model tag from name (e.g., 'latest' from 'llama2:latest')."""
        return self.name.split(":")[1] if ":" in self.name else "latest"


class RunningModel(BaseModel):
    """Represents a currently running Ollama model."""
    name: str = Field(..., description="Model name")
    model: str = Field(..., description="Full model identifier")
    size: int = Field(..., description="Model size in bytes")
    digest: str = Field(..., description="Model digest")
    expires_at: str = Field(..., description="When the model will be unloaded")
    size_vram: int = Field(..., description="VRAM usage in bytes")


class ModelDetails(BaseModel):
    """Detailed information about a specific model."""
    modelfile: Optional[str] = Field(None, description="Modelfile content")
    parameters: Optional[str] = Field(None, description="Model parameters")
    template: Optional[str] = Field(None, description="Prompt template")
    details: Optional[Dict[str, Any]] = Field(None, description="Model architecture details")
    license: Optional[str] = Field(None, description="Model license information")
    system: Optional[str] = Field(None, description="System prompt")
    model_info: Optional[Dict[str, Any]] = Field(None, description="Additional model information")


class OllamaModelService:
    """Service for managing Ollama models via HTTP API."""

    def __init__(self, settings: Settings = None):
        """
        Initialize Ollama model service.

        Args:
            settings: Application settings (uses default if not provided)
        """
        self.settings = settings or Settings()
        self.ollama_url = self.settings.OLLAMA_ENDPOINT
        self.timeout = 30.0  # Default timeout for API calls

        logger.info(f"Initialized OllamaModelService with endpoint: {self.ollama_url}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Ollama API.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint (e.g., '/api/tags')
            json_data: JSON data for request body
            timeout: Request timeout in seconds

        Returns:
            Response JSON as dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.ollama_url}{endpoint}"
        request_timeout = timeout or self.timeout

        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url)
                elif method.upper() == "POST":
                    response = await client.post(url, json=json_data)
                elif method.upper() == "DELETE":
                    response = await client.request(method="DELETE", url=url, json=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama at {url}: {e}")
            raise ConnectionError(
                f"Could not connect to Ollama service at {self.ollama_url}. "
                "Ensure Ollama is running and accessible."
            )
        except httpx.TimeoutException as e:
            logger.error(f"Request to {url} timed out: {e}")
            raise TimeoutError(f"Request to Ollama timed out after {request_timeout} seconds")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama API: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if Ollama service is running and accessible.

        Returns:
            True if Ollama is healthy, False otherwise
        """
        try:
            # Try to list models as a health check
            await self._make_request("GET", "/api/tags", timeout=5.0)
            logger.info("Ollama health check passed")
            return True
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def list_installed_models(self) -> List[OllamaModel]:
        """
        List all installed Ollama models.

        Returns:
            List of installed models with metadata

        Raises:
            ConnectionError: If Ollama service is not accessible
        """
        try:
            logger.info("Fetching installed Ollama models...")
            response = await self._make_request("GET", "/api/tags")

            models_data = response.get("models", [])
            models = [OllamaModel(**model_data) for model_data in models_data]

            logger.info(f"Found {len(models)} installed Ollama models")
            return models

        except Exception as e:
            logger.error(f"Failed to list installed models: {e}")
            raise

    async def get_model_details(self, model_name: str) -> ModelDetails:
        """
        Get detailed information about a specific model.

        Args:
            model_name: Name of the model (e.g., 'llama2:latest', 'qwen2.5:1.5b')

        Returns:
            Detailed model information

        Raises:
            ValueError: If model not found
            ConnectionError: If Ollama service is not accessible
        """
        try:
            logger.info(f"Fetching details for model: {model_name}")

            response = await self._make_request(
                "POST",
                "/api/show",
                json_data={"name": model_name}
            )

            details = ModelDetails(**response)
            logger.info(f"Successfully retrieved details for {model_name}")
            return details

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Model not found: {model_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to get model details for {model_name}: {e}")
            raise

    async def get_running_models(self) -> List[RunningModel]:
        """
        Get list of currently running/loaded models.

        Returns:
            List of running models with resource usage

        Raises:
            ConnectionError: If Ollama service is not accessible
        """
        try:
            logger.info("Fetching running Ollama models...")
            response = await self._make_request("GET", "/api/ps")

            models_data = response.get("models", [])
            running_models = [RunningModel(**model_data) for model_data in models_data]

            logger.info(f"Found {len(running_models)} running Ollama models")
            return running_models

        except Exception as e:
            logger.error(f"Failed to get running models: {e}")
            raise

    async def get_model_stats(self) -> Dict[str, Any]:
        """
        Get statistics about installed models.

        Returns:
            Dictionary containing:
            - total_models: Total number of installed models
            - total_size_gb: Total size of all models in GB
            - models_by_family: Count of models grouped by family
            - largest_model: Name and size of largest model
            - smallest_model: Name and size of smallest model
        """
        try:
            models = await self.list_installed_models()

            if not models:
                return {
                    "total_models": 0,
                    "total_size_gb": 0,
                    "models_by_family": {},
                    "largest_model": None,
                    "smallest_model": None
                }

            # Calculate statistics
            total_size = sum(model.size for model in models)
            total_size_gb = round(total_size / (1024 ** 3), 2)

            # Group by family
            models_by_family = {}
            for model in models:
                family = model.family
                models_by_family[family] = models_by_family.get(family, 0) + 1

            # Find largest and smallest
            largest = max(models, key=lambda m: m.size)
            smallest = min(models, key=lambda m: m.size)

            stats = {
                "total_models": len(models),
                "total_size_gb": total_size_gb,
                "total_size_bytes": total_size,
                "models_by_family": models_by_family,
                "largest_model": {
                    "name": largest.name,
                    "size_gb": largest.size_gb,
                    "size_bytes": largest.size
                },
                "smallest_model": {
                    "name": smallest.name,
                    "size_gb": smallest.size_gb,
                    "size_bytes": smallest.size
                }
            }

            logger.info(f"Calculated model statistics: {stats['total_models']} models, {total_size_gb} GB")
            return stats

        except Exception as e:
            logger.error(f"Failed to calculate model statistics: {e}")
            raise

    async def check_model_exists(self, model_name: str) -> bool:
        """
        Check if a specific model is installed.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model exists, False otherwise
        """
        try:
            models = await self.list_installed_models()
            return any(model.name == model_name for model in models)
        except Exception as e:
            logger.error(f"Failed to check if model exists: {e}")
            return False

    # -------------------------------------------------------------------------
    # Phase 2: Model Management Operations
    # -------------------------------------------------------------------------

    async def pull_model(self, model_name: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Pull/install a new model from Ollama library with streaming progress.

        Args:
            model_name: Name of the model to pull (e.g., 'llama2:latest', 'mistral:7b')

        Yields:
            Progress updates as dictionaries with status, progress, etc.

        Raises:
            ConnectionError: If Ollama service is not accessible
            ValueError: If model name is invalid
        """
        try:
            logger.info(f"Starting pull for model: {model_name}")

            url = f"{self.ollama_url}/api/pull"
            json_data = {"name": model_name}

            async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for large models
                async with client.stream("POST", url, json=json_data) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                progress_data = json.loads(line)
                                yield progress_data

                                # Log completion
                                if progress_data.get("status") == "success":
                                    logger.info(f"Successfully pulled model: {model_name}")

                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse progress line: {line}")
                                continue

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama at {self.ollama_url}: {e}")
            raise ConnectionError(
                f"Could not connect to Ollama service at {self.ollama_url}. "
                "Ensure Ollama is running and accessible."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error pulling model {model_name}: {e.response.status_code}")
            if e.response.status_code == 404:
                raise ValueError(f"Model not found in Ollama library: {model_name}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error pulling model {model_name}: {e}")
            raise

    async def delete_model(self, model_name: str) -> bool:
        """
        Delete an installed model.

        Args:
            model_name: Name of the model to delete (e.g., 'llama2:latest')

        Returns:
            True if deletion successful

        Raises:
            ConnectionError: If Ollama service is not accessible
            ValueError: If model not found
        """
        try:
            logger.info(f"Deleting model: {model_name}")

            url = f"{self.ollama_url}/api/delete"
            json_data = {"name": model_name}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method="DELETE",
                    url=url,
                    json=json_data
                )
                response.raise_for_status()

                logger.info(f"Successfully deleted model: {model_name}")
                return True

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama at {self.ollama_url}: {e}")
            raise ConnectionError(
                f"Could not connect to Ollama service at {self.ollama_url}. "
                "Ensure Ollama is running and accessible."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error deleting model {model_name}: {e.response.status_code}")
            if e.response.status_code == 404:
                raise ValueError(f"Model not found: {model_name}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting model {model_name}: {e}")
            raise


# Singleton instance for dependency injection
_ollama_service_instance: Optional[OllamaModelService] = None


def get_ollama_service(settings: Settings = None) -> OllamaModelService:
    """
    Get singleton instance of OllamaModelService.

    Args:
        settings: Application settings (optional)

    Returns:
        OllamaModelService instance
    """
    global _ollama_service_instance

    if _ollama_service_instance is None:
        _ollama_service_instance = OllamaModelService(settings)

    return _ollama_service_instance
