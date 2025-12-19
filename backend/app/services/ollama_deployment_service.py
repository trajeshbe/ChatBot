"""
Ollama Deployment Service

Handles deployment of fine-tuned models to Ollama for local inference.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OllamaDeploymentService:
    """Service for deploying models to Ollama"""

    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.models_dir = Path("/app/models")  # Base directory for model files

    async def deploy_model(
        self,
        model_name: str,
        model_path: str,
        base_model: str = "llama2",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deploy a fine-tuned model to Ollama

        Args:
            model_name: Name for the deployed model in Ollama
            model_path: Path to the fine-tuned model weights (minio:// URL, local path, or GGUF)
            base_model: Base model to use (e.g., llama2, mistral)
            parameters: Optional model parameters (temperature, top_p, etc.)

        Returns:
            Deployment result with status and details
        """
        try:
            # OPTIMIZED: Try workspace first, then download from MinIO as fallback
            local_model_path = model_path
            if model_path.startswith("minio://"):
                # Extract job_id from MinIO path to check workspace
                # Format: minio://documents/.../job_id/...
                workspace_path = None
                try:
                    import re
                    job_id_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', model_path)
                    if job_id_match:
                        job_id = job_id_match.group(1)
                        # Check if merged model exists in workspace
                        workspace_merged = f"/workspace/finetuning/{job_id}/output/merged_model"
                        if os.path.exists(workspace_merged):
                            logger.info(f"✅ Using merged model from workspace: {workspace_merged}")
                            logger.info(f"   (Skipping MinIO download for efficiency)")
                            local_model_path = workspace_merged
                        else:
                            logger.warning(f"⚠️  Workspace not found at {workspace_merged}, falling back to MinIO download")
                            local_model_path = await self._download_from_minio(model_path)
                    else:
                        logger.warning("⚠️  Could not extract job_id from MinIO path, falling back to MinIO download")
                        local_model_path = await self._download_from_minio(model_path)
                except Exception as e:
                    logger.error(f"Error checking workspace: {e}, falling back to MinIO download")
                    local_model_path = await self._download_from_minio(model_path)

                if not local_model_path:
                    raise RuntimeError(f"Failed to locate model (checked workspace and MinIO): {model_path}")

            # Generate Modelfile
            modelfile_path = await self._generate_modelfile(
                model_name=model_name,
                model_path=local_model_path,
                base_model=base_model,
                parameters=parameters or {}
            )

            # Create model in Ollama
            result = await self._create_ollama_model(
                model_name=model_name,
                modelfile_path=modelfile_path
            )

            return {
                "status": "success",
                "model_name": model_name,
                "deployment_url": f"{self.ollama_host}/api/generate",
                "details": result
            }

        except Exception as e:
            logger.error(f"Error deploying model to Ollama: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def _download_from_minio(self, minio_url: str) -> Optional[str]:
        """
        Download model checkpoints from MinIO to local temporary directory

        Args:
            minio_url: MinIO URL in format minio://bucket/path/to/checkpoint

        Returns:
            Local path to downloaded checkpoint directory, or None if failed
        """
        try:
            from minio import Minio
            from app.core.config import settings
            import tempfile
            import asyncio

            # Parse MinIO URL: minio://bucket/path/to/file
            if not minio_url.startswith("minio://"):
                logger.error(f"Invalid MinIO URL: {minio_url}")
                return None

            # Extract bucket and object path
            url_parts = minio_url.replace("minio://", "").split("/", 1)
            if len(url_parts) != 2:
                logger.error(f"Invalid MinIO URL format: {minio_url}")
                return None

            bucket_name, object_prefix = url_parts

            # Initialize MinIO client
            minio_client = Minio(
                endpoint=settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_ENDPOINT.startswith("https://")
            )

            # Create temporary directory for checkpoints
            temp_dir = Path(tempfile.mkdtemp(prefix="ollama_model_"))
            logger.info(f"Downloading from MinIO to {temp_dir}")

            # List all objects with the prefix (to get all checkpoint files)
            objects = minio_client.list_objects(bucket_name, prefix=object_prefix, recursive=True)

            downloaded_files = []
            for obj in objects:
                # Skip directories
                if obj.object_name.endswith("/"):
                    continue

                # Create local file path maintaining directory structure
                relative_path = obj.object_name.replace(object_prefix, "").lstrip("/")

                # Handle case where object_prefix is a specific file (relative_path will be empty)
                if not relative_path:
                    # Extract filename from the object path
                    relative_path = Path(obj.object_name).name

                local_file = temp_dir / relative_path
                local_file.parent.mkdir(parents=True, exist_ok=True)

                # Download file
                logger.info(f"Downloading {obj.object_name} to {local_file}")
                await asyncio.to_thread(
                    minio_client.fget_object,
                    bucket_name=bucket_name,
                    object_name=obj.object_name,
                    file_path=str(local_file)
                )
                downloaded_files.append(local_file)

            if not downloaded_files:
                logger.error(f"No files found at {minio_url}")
                return None

            logger.info(f"Downloaded {len(downloaded_files)} files from MinIO to {temp_dir}")
            return str(temp_dir)

        except Exception as e:
            logger.error(f"Failed to download from MinIO: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def _generate_modelfile(
        self,
        model_name: str,
        model_path: str,
        base_model: str,
        parameters: Dict[str, Any]
    ) -> Path:
        """
        Generate an Ollama Modelfile for the fine-tuned model

        Args:
            model_name: Name for the model
            model_path: Path to model weights
            base_model: Base model identifier
            parameters: Model parameters

        Returns:
            Path to generated Modelfile
        """
        # Check if model_path contains merged_model (use it) or adapter_model (skip ADAPTER directive)
        use_adapter = False
        if "adapter_model" in model_path and "merged_model" not in model_path:
            logger.warning(f"⚠️ Using adapter_model path - this may not work correctly. Prefer using merged_model.")
            use_adapter = True

        # Keep model_path as directory - Ollama needs the whole directory with config files
        if os.path.isdir(model_path):
            safetensors_path = os.path.join(model_path, "model.safetensors")
            config_path = os.path.join(model_path, "config.json")
            if os.path.exists(safetensors_path) and os.path.exists(config_path):
                logger.info(f"✅ Found complete HuggingFace model in directory: {model_path}")
                logger.info(f"   - model.safetensors: {os.path.getsize(safetensors_path) / (1024**3):.2f} GB")
                logger.info(f"   - config.json: present")
                # Keep model_path as directory - Ollama expects directory with all model files
            else:
                logger.warning(f"⚠️  Directory {model_path} missing required files (model.safetensors or config.json)")

        if use_adapter:
            # Legacy: Try to use ADAPTER directive (may not work properly)
            modelfile_content = f"""# Modelfile for {model_name}
FROM {base_model}

# Load fine-tuned adapter weights (LEGACY - may not work)
ADAPTER {model_path}

# Model parameters
PARAMETER temperature {parameters.get('temperature', 0.7)}
PARAMETER top_p {parameters.get('top_p', 0.9)}
PARAMETER top_k {parameters.get('top_k', 40)}
PARAMETER num_ctx {parameters.get('num_ctx', 2048)}

# System prompt (optional)
SYSTEM You are a helpful AI assistant.
"""
        else:
            # Preferred: Use merged model directly (FROM points to merged model)
            modelfile_content = f"""# Modelfile for {model_name}
# Using merged fine-tuned model directly
FROM {model_path}

# Model parameters
PARAMETER temperature {parameters.get('temperature', 0.7)}
PARAMETER top_p {parameters.get('top_p', 0.9)}
PARAMETER top_k {parameters.get('top_k', 40)}
PARAMETER num_ctx {parameters.get('num_ctx', 2048)}

# System prompt (optional)
SYSTEM You are a helpful AI assistant.
"""
        logger.info(f"✅ Generated Modelfile (using {'ADAPTER' if use_adapter else 'FROM merged model'})")

        # Write Modelfile
        modelfile_path = self.models_dir / f"{model_name}.Modelfile"
        modelfile_path.parent.mkdir(parents=True, exist_ok=True)

        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)

        logger.info(f"Generated Modelfile at {modelfile_path}")
        return modelfile_path

    async def _create_ollama_model(
        self,
        model_name: str,
        modelfile_path: Path
    ) -> Dict[str, Any]:
        """
        Create model in Ollama using the Modelfile via HTTP API

        Args:
            model_name: Name for the model
            modelfile_path: Path to Modelfile

        Returns:
            Creation result
        """
        try:
            import httpx

            # Read the Modelfile content
            with open(modelfile_path, 'r') as f:
                modelfile_content = f.read()

            # Use Ollama HTTP API to create model
            # Note: OLLAMA_HOST can be set via environment variable
            ollama_url = os.getenv("OLLAMA_HOST", "http://ollama:11434")
            create_url = f"{ollama_url}/api/create"

            logger.info(f"Creating Ollama model '{model_name}' via API at {create_url}")

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    create_url,
                    json={
                        "name": model_name,
                        "modelfile": modelfile_content
                    },
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    logger.info(f"✅ Successfully created Ollama model: {model_name}")
                    return {
                        "success": True,
                        "response": response.text
                    }
                else:
                    error_msg = f"Ollama API returned {response.status_code}: {response.text}"
                    logger.error(f"Failed to create Ollama model: {error_msg}")
                    raise RuntimeError(error_msg)

        except httpx.TimeoutException:
            logger.error(f"Timeout creating Ollama model: {model_name}")
            raise RuntimeError("Model creation timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Error creating Ollama model via API: {e}", exc_info=True)
            raise

    async def list_deployed_models(self) -> Dict[str, Any]:
        """
        List all models available in Ollama

        Returns:
            List of deployed models
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "models": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def remove_model(self, model_name: str) -> Dict[str, Any]:
        """
        Remove a model from Ollama

        Args:
            model_name: Name of model to remove

        Returns:
            Removal result
        """
        try:
            result = subprocess.run(
                ["ollama", "rm", model_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"Successfully removed Ollama model: {model_name}")
                return {
                    "success": True,
                    "message": f"Model {model_name} removed"
                }
            else:
                logger.error(f"Failed to remove model: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            logger.error(f"Error removing Ollama model: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_model(self, model_name: str, prompt: str = "Hello, how are you?") -> Dict[str, Any]:
        """
        Test a deployed model with a simple prompt

        Args:
            model_name: Name of model to test
            prompt: Test prompt

        Returns:
            Test result
        """
        try:
            result = subprocess.run(
                ["ollama", "run", model_name, prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "prompt": prompt,
                    "response": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Model inference timed out"
            }
        except Exception as e:
            logger.error(f"Error testing Ollama model: {e}")
            return {
                "success": False,
                "error": str(e)
            }
