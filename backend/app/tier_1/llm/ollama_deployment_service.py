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

    async def _merge_adapter_to_base(
        self,
        adapter_path: str,
        base_model: str,
        output_path: str
    ) -> bool:
        """
        Merge LoRA adapter into base model

        Args:
            adapter_path: Path to adapter weights
            base_model: Base model identifier (e.g., Qwen/Qwen2.5-1.5B-Instruct)
            output_path: Where to save merged model

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🔄 Merging adapter into base model...")
            logger.info(f"   Adapter: {adapter_path}")
            logger.info(f"   Base: {base_model}")
            logger.info(f"   Output: {output_path}")

            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel
            import gc

            # Load base model
            logger.info("Loading base model (this may take 2-3 minutes)...")
            base_model_obj = AutoModelForCausalLM.from_pretrained(
                base_model,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )

            # Load adapter
            logger.info("Loading adapter...")
            peft_model = PeftModel.from_pretrained(
                base_model_obj,
                adapter_path,
                is_trainable=False
            )

            # Merge
            logger.info("Merging (this may take 2-3 minutes)...")
            merged_model = peft_model.merge_and_unload()

            # Cleanup memory
            del peft_model, base_model_obj
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Save merged model
            logger.info(f"Saving merged model to {output_path}...")
            Path(output_path).mkdir(parents=True, exist_ok=True)
            merged_model.save_pretrained(output_path)

            # Save tokenizer
            tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
            tokenizer.save_pretrained(output_path)

            logger.info("✅ Merge completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Merge failed: {e}", exc_info=True)
            return False

    async def _convert_to_gguf(
        self,
        model_path: str,
        output_path: str,
        quantization: str = "q4_K_M"
    ) -> Optional[str]:
        """
        Convert HuggingFace model to GGUF format

        Args:
            model_path: Path to HuggingFace model
            output_path: Output directory for GGUF file
            quantization: Quantization type (q4_K_M, q5_K_M, q8_0, etc.)

        Returns:
            Path to GGUF file if successful, None otherwise
        """
        try:
            logger.info(f"🔄 Converting to GGUF format...")
            logger.info(f"   Input: {model_path}")
            logger.info(f"   Quantization: {quantization}")

            import subprocess
            import tempfile

            # Check if llama.cpp is available
            llama_cpp_dir = Path("/tmp/llama.cpp")

            if not llama_cpp_dir.exists():
                logger.info("📥 Cloning llama.cpp...")
                result = subprocess.run(
                    ["git", "clone", "https://github.com/ggerganov/llama.cpp", str(llama_cpp_dir)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode != 0:
                    logger.error(f"Failed to clone llama.cpp: {result.stderr}")
                    return None

                # Install requirements
                logger.info("📦 Installing llama.cpp requirements...")
                subprocess.run(
                    ["pip", "install", "-q", "-r", str(llama_cpp_dir / "requirements.txt")],
                    timeout=300
                )

            # Convert to GGUF
            Path(output_path).mkdir(parents=True, exist_ok=True)
            gguf_file = Path(output_path) / f"model-{quantization}.gguf"

            logger.info(f"Converting to GGUF (this may take 5-10 minutes)...")

            # Note: convert_hf_to_gguf.py only supports f32,f16,bf16,q8_0,tq1_0,tq2_0,auto
            # K-quants (q4_K_M, q5_K_M) require 2-step process: convert to f16, then quantize
            # For now, we use f16 directly (works but larger ~2.9GB vs ~900MB)
            # TODO: Add llama-quantize step for K-quants after initial conversion

            if quantization in ["q4_K_M", "q5_K_M", "q6_K"]:
                logger.warning(f"⚠️  K-quant {quantization} not yet supported, using f16 (~2.9GB)")
                logger.warning(f"   TODO: Implement 2-step quantization with llama-quantize")
                outtype = "f16"
                gguf_file = Path(output_path) / "model-f16.gguf"  # Use actual type in filename
            else:
                outtype = quantization

            result = subprocess.run(
                [
                    "python",
                    str(llama_cpp_dir / "convert_hf_to_gguf.py"),
                    model_path,
                    "--outfile", str(gguf_file),
                    "--outtype", outtype
                ],
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes max
                cwd=str(llama_cpp_dir)
            )

            if result.returncode != 0:
                logger.error(f"GGUF conversion failed: {result.stderr}")
                logger.error(f"Stdout: {result.stdout}")
                return None

            if gguf_file.exists():
                size_mb = gguf_file.stat().st_size / (1024 ** 2)
                logger.info(f"✅ GGUF created: {size_mb:.1f} MB at {gguf_file}")
                return str(gguf_file)
            else:
                logger.error("GGUF file not created")
                return None

        except Exception as e:
            logger.error(f"❌ GGUF conversion failed: {e}", exc_info=True)
            return None

    async def deploy_model(
        self,
        model_name: str,
        model_path: str,
        base_model: str = "llama2",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deploy a fine-tuned model to Ollama with automatic merge + GGUF conversion

        Args:
            model_name: Name for the deployed model in Ollama
            model_path: Path to the fine-tuned model weights (minio:// URL, local path, adapter, or GGUF)
            base_model: Base model to use (e.g., Qwen/Qwen2.5-1.5B-Instruct)
            parameters: Optional model parameters (temperature, top_p, etc.)

        Returns:
            Deployment result with status and details
        """
        try:
            logger.info(f"🚀 Deploying model {model_name} to Ollama")
            logger.info(f"   Model path: {model_path}")
            logger.info(f"   Base model: {base_model}")

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

            # STEP 1: Check if this is an adapter that needs merging
            adapter_config_path = Path(local_model_path) / "adapter_config.json"
            merged_model_path = None
            gguf_path = None

            if adapter_config_path.exists():
                logger.info("📦 Detected LoRA adapter - merge required for Ollama")

                # Check if merged model already exists
                job_dir = Path(local_model_path).parent.parent  # Go up from adapter_model/
                potential_merged = job_dir / "output" / "merged_model"

                if potential_merged.exists() and (potential_merged / "config.json").exists():
                    logger.info(f"✅ Found existing merged model at {potential_merged}")
                    merged_model_path = str(potential_merged)
                else:
                    # Need to merge
                    logger.info("🔄 Merged model not found, starting merge process...")
                    merged_output = job_dir / "output" / "merged_model"

                    merge_success = await self._merge_adapter_to_base(
                        adapter_path=local_model_path,
                        base_model=base_model,
                        output_path=str(merged_output)
                    )

                    if not merge_success:
                        raise RuntimeError("Failed to merge adapter into base model")

                    merged_model_path = str(merged_output)

                # STEP 2: Convert merged model to GGUF
                logger.info("🔄 Converting merged model to GGUF for Ollama...")
                gguf_output_dir = job_dir / "output" / "gguf"

                # Check if GGUF already exists
                existing_gguf = list(Path(gguf_output_dir).glob("*.gguf")) if gguf_output_dir.exists() else []
                if existing_gguf:
                    logger.info(f"✅ Found existing GGUF at {existing_gguf[0]}")
                    gguf_path = str(existing_gguf[0])
                else:
                    gguf_path = await self._convert_to_gguf(
                        model_path=merged_model_path,
                        output_path=str(gguf_output_dir),
                        quantization="q4_K_M"
                    )

                    if not gguf_path:
                        raise RuntimeError("Failed to convert model to GGUF format")

                # Use GGUF for Ollama deployment
                local_model_path = gguf_path
                logger.info(f"✅ Using GGUF model: {gguf_path}")

            elif str(local_model_path).endswith(".gguf"):
                logger.info("✅ Model is already in GGUF format")
                gguf_path = local_model_path

            else:
                # Check if it's a HuggingFace merged model
                config_path = Path(local_model_path) / "config.json"
                if config_path.exists():
                    logger.info("📦 Detected HuggingFace model - GGUF conversion required for Ollama")

                    # Convert to GGUF
                    job_dir = Path(local_model_path).parent
                    gguf_output_dir = job_dir / "gguf"

                    gguf_path = await self._convert_to_gguf(
                        model_path=local_model_path,
                        output_path=str(gguf_output_dir),
                        quantization="q4_K_M"
                    )

                    if not gguf_path:
                        raise RuntimeError("Failed to convert model to GGUF format")

                    local_model_path = gguf_path
                    logger.info(f"✅ Using GGUF model: {gguf_path}")

            # Generate Modelfile for GGUF
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
                "merged_model_path": merged_model_path,
                "gguf_path": gguf_path,
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
            model_path: Path to model weights (GGUF or HuggingFace directory)
            base_model: Base model identifier
            parameters: Model parameters

        Returns:
            Path to generated Modelfile
        """
        # Check if GGUF file
        is_gguf = str(model_path).endswith(".gguf")

        if is_gguf:
            logger.info(f"✅ Generating Modelfile for GGUF: {model_path}")
            gguf_size = Path(model_path).stat().st_size / (1024**2)
            logger.info(f"   GGUF size: {gguf_size:.1f} MB")

            modelfile_content = f"""# Modelfile for {model_name} (GGUF Fine-tuned)
FROM {model_path}

# Model parameters
PARAMETER temperature {parameters.get('temperature', 0.7)}
PARAMETER top_p {parameters.get('top_p', 0.9)}
PARAMETER top_k {parameters.get('top_k', 40)}
PARAMETER num_ctx {parameters.get('num_ctx', 2048)}

# System prompt
SYSTEM You are a helpful assistant that provides accurate information about companies and products.
"""
        else:
            # HuggingFace directory
            if os.path.isdir(model_path):
                safetensors_path = os.path.join(model_path, "model.safetensors")
                config_path = os.path.join(model_path, "config.json")
                if os.path.exists(safetensors_path) and os.path.exists(config_path):
                    logger.info(f"✅ Found complete HuggingFace model in directory: {model_path}")
                    logger.info(f"   - model.safetensors: {os.path.getsize(safetensors_path) / (1024**3):.2f} GB")
                    logger.info(f"   - config.json: present")
                else:
                    logger.warning(f"⚠️  Directory {model_path} missing required files")

            modelfile_content = f"""# Modelfile for {model_name} (HuggingFace merged model)
FROM {model_path}

# Model parameters
PARAMETER temperature {parameters.get('temperature', 0.7)}
PARAMETER top_p {parameters.get('top_p', 0.9)}
PARAMETER top_k {parameters.get('top_k', 40)}
PARAMETER num_ctx {parameters.get('num_ctx', 2048)}

# System prompt
SYSTEM You are a helpful assistant that provides accurate information about companies and products.
"""

        logger.info(f"✅ Generated Modelfile ({'GGUF' if is_gguf else 'HuggingFace'})")

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
        Create model in Ollama using the Modelfile via Docker exec + CLI

        This approach is more reliable than the HTTP API which has issues
        parsing the Modelfile content. We write the Modelfile to a temp location
        in the Ollama container and use `ollama create -f`.

        Args:
            model_name: Name for the model
            modelfile_path: Path to Modelfile (in backend container)

        Returns:
            Creation result
        """
        try:
            # Read the Modelfile content
            with open(modelfile_path, 'r') as f:
                modelfile_content = f.read()

            # Write Modelfile to temp location in Ollama container
            temp_modelfile = f"/tmp/{model_name}.Modelfile"

            logger.info(f"Creating Ollama model '{model_name}' via Docker exec")
            logger.info(f"   Modelfile: {temp_modelfile}")

            # Write Modelfile to Ollama container
            write_cmd = [
                "docker", "exec", "-i", "rag-ollama",
                "sh", "-c", f"cat > {temp_modelfile}"
            ]

            write_result = subprocess.run(
                write_cmd,
                input=modelfile_content.encode(),
                capture_output=True,
                timeout=30
            )

            if write_result.returncode != 0:
                raise RuntimeError(f"Failed to write Modelfile: {write_result.stderr.decode()}")

            logger.info(f"✅ Modelfile written to Ollama container")

            # Create model using ollama CLI
            create_cmd = [
                "docker", "exec", "rag-ollama",
                "ollama", "create", model_name,
                "-f", temp_modelfile
            ]

            logger.info(f"🚀 Creating model in Ollama (this may take 1-2 minutes)...")

            create_result = subprocess.run(
                create_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )

            if create_result.returncode == 0:
                logger.info(f"✅ Successfully created Ollama model: {model_name}")
                logger.info(f"   Output: {create_result.stdout.strip()}")

                # Clean up temp Modelfile
                subprocess.run(
                    ["docker", "exec", "rag-ollama", "rm", "-f", temp_modelfile],
                    capture_output=True,
                    timeout=10
                )

                return {
                    "success": True,
                    "response": create_result.stdout
                }
            else:
                error_msg = f"Ollama create failed: {create_result.stderr}"
                logger.error(f"Failed to create Ollama model: {error_msg}")
                raise RuntimeError(error_msg)

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout creating Ollama model: {model_name}")
            raise RuntimeError("Model creation timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Error creating Ollama model: {e}", exc_info=True)
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
