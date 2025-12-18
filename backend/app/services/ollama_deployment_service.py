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
            model_path: Path to the fine-tuned model weights (GGUF or safetensors)
            base_model: Base model to use (e.g., llama2, mistral)
            parameters: Optional model parameters (temperature, top_p, etc.)

        Returns:
            Deployment result with status and details
        """
        try:
            # Generate Modelfile
            modelfile_path = await self._generate_modelfile(
                model_name=model_name,
                model_path=model_path,
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
        Create model in Ollama using the Modelfile

        Args:
            model_name: Name for the model
            modelfile_path: Path to Modelfile

        Returns:
            Creation result
        """
        try:
            # Execute ollama create command
            cmd = [
                "ollama",
                "create",
                model_name,
                "-f",
                str(modelfile_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info(f"Successfully created Ollama model: {model_name}")
                return {
                    "success": True,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                logger.error(f"Failed to create Ollama model: {result.stderr}")
                raise RuntimeError(f"Ollama create failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout creating Ollama model: {model_name}")
            raise RuntimeError("Model creation timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Error executing ollama create: {e}")
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
