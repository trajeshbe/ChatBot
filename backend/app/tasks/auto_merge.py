"""
Auto-Merge After Training

Merges LoRA adapters with base model immediately after training.
Runs in the finetuning-runtime container (has PEFT installed).

Date: 2025-12-22
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def auto_merge_lora_adapters(
    job_id: str,
    adapter_path: str,
    base_model_name: str,
    workspace_path: Path,
    force_cpu: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Automatically merge LoRA adapters with base model after training.

    This function is called immediately after training completes,
    in the same container that did the training (has PEFT installed).

    Args:
        job_id: Training job ID
        adapter_path: Path to LoRA adapter checkpoint (relative or absolute)
        base_model_name: HuggingFace base model name (e.g., "Qwen/Qwen2.5-1.5B-Instruct")
        workspace_path: Workspace directory for the job
        force_cpu: Force CPU-only merge (for testing/debugging)

    Returns:
        dict: Merge result with status, path, duration
        None: If merge fails (non-fatal, adapters still usable)

    Example:
        result = auto_merge_lora_adapters(
            job_id="abc-123",
            adapter_path="/workspace/finetuning/abc-123/output/final",
            base_model_name="Qwen/Qwen2.5-1.5B-Instruct",
            workspace_path=Path("/workspace/finetuning/abc-123")
        )
        # Returns: {"status": "success", "merged_path": "/workspace/...", "duration_seconds": 45.2}
    """
    import time

    start_time = time.time()

    try:
        # Lazy imports - only load when function is called (not at module level)
        # This allows celery-worker (backend container) to import this module
        # without needing PEFT/torch/transformers installed
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        logger.info(f"🔄 [AUTO-MERGE] Starting auto-merge for job {job_id}")
        logger.info(f"   Base model: {base_model_name}")
        logger.info(f"   Adapter path: {adapter_path}")

        # Convert adapter_path to Path object
        adapter_checkpoint = Path(adapter_path)

        # Check if container already merged (merged_model exists)
        merged_output_path = workspace_path / "output" / "merged_model"
        if merged_output_path.exists() and (merged_output_path / "config.json").exists():
            # Container already merged - just return the path
            duration = time.time() - start_time
            logger.info(f"✅ [AUTO-MERGE] Container already merged model")
            logger.info(f"📍 Using container-merged model: {merged_output_path}")
            return {
                "status": "success",
                "merged_path": str(merged_output_path),
                "duration_seconds": duration,
                "source": "container_merge"
            }

        # Check for adapter_model directory (alternative path)
        adapter_model_path = workspace_path / "output" / "adapter_model"
        if not adapter_checkpoint.exists():
            # Try alternative path
            if adapter_model_path.exists():
                logger.info(f"📁 [AUTO-MERGE] Using adapter_model path: {adapter_model_path}")
                adapter_checkpoint = adapter_model_path
            else:
                logger.error(f"❌ [AUTO-MERGE] Adapter not found at: {adapter_checkpoint}")
                logger.error(f"   Also checked: {adapter_model_path}")
                return None

        # Create merged output directory
        merged_output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"📁 [AUTO-MERGE] Merge output: {merged_output_path}")

        # Determine device
        if force_cpu:
            device = "cpu"
            logger.info("🖥️  [AUTO-MERGE] Using CPU (force_cpu=True)")
        elif torch.cuda.is_available():
            device = "cuda"
            logger.info(f"🎮 [AUTO-MERGE] Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            logger.info("🖥️  [AUTO-MERGE] Using CPU (no GPU available)")

        # Load base model
        logger.info(f"📦 [AUTO-MERGE] Loading base model: {base_model_name}")

        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True
        )

        # Load tokenizer
        logger.info(f"📝 [AUTO-MERGE] Loading tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            trust_remote_code=True
        )

        # Load LoRA adapters
        logger.info(f"🔗 [AUTO-MERGE] Loading LoRA adapters from: {adapter_checkpoint}")

        model = PeftModel.from_pretrained(base_model, str(adapter_checkpoint))

        # Merge adapters with base model
        logger.info(f"⚙️  [AUTO-MERGE] Merging adapters with base model...")

        merged_model = model.merge_and_unload()

        # Save merged model
        logger.info(f"💾 [AUTO-MERGE] Saving merged model to: {merged_output_path}")

        merged_model.save_pretrained(str(merged_output_path))
        tokenizer.save_pretrained(str(merged_output_path))

        # Calculate duration
        duration = time.time() - start_time

        logger.info(f"✅ [AUTO-MERGE] Merge completed successfully in {duration:.1f} seconds")
        logger.info(f"📍 [AUTO-MERGE] Merged model path: {merged_output_path}")

        # Clean up memory
        del base_model
        del model
        del merged_model
        if device == "cuda":
            torch.cuda.empty_cache()
            logger.info("🧹 [AUTO-MERGE] GPU memory cleared")

        return {
            "status": "success",
            "merged_path": str(merged_output_path),
            "duration_seconds": duration,
            "device": device
        }

    except ImportError as e:
        logger.error(f"❌ [AUTO-MERGE] Missing dependency: {e}")
        logger.error("   PEFT or transformers not installed in this container")
        return None

    except Exception as e:
        logger.error(f"❌ [AUTO-MERGE] Merge failed: {str(e)}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return None


def should_auto_merge() -> bool:
    """
    Check if auto-merge is enabled via environment variable.

    Returns:
        bool: True if auto-merge should run, False otherwise

    Example:
        # In .env:
        FINETUNING_AUTO_MERGE=true

        # In code:
        if should_auto_merge():
            auto_merge_lora_adapters(...)
    """
    auto_merge_enabled = os.getenv("FINETUNING_AUTO_MERGE", "true").lower()
    return auto_merge_enabled in ("true", "1", "yes", "on")


# Export functions
__all__ = ["auto_merge_lora_adapters", "should_auto_merge"]
