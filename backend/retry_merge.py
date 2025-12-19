#!/usr/bin/env python3
"""
Retry merging PEFT adapters for failed training jobs.

This script loads trained adapter weights and merges them back into
the base model to create a standalone fine-tuned model.
"""

import os
import sys
import json
import torch
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge_adapter(adapter_dir: str, base_model: str, output_dir: str):
    """
    Merge PEFT adapter with base model.

    Args:
        adapter_dir: Path to adapter weights directory
        base_model: Base model identifier (e.g., 'Qwen/Qwen2.5-7B-Instruct')
        output_dir: Where to save merged model
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        import gc

        logger.info(f"🔄 Starting merge process...")
        logger.info(f"  Adapter dir: {adapter_dir}")
        logger.info(f"  Base model: {base_model}")
        logger.info(f"  Output dir: {output_dir}")

        # 1. Load tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)

        # 2. Load base model in full precision (BF16)
        logger.info(f"Loading base model: {base_model}")
        logger.info("  Using torch.bfloat16 precision")
        logger.info("  This will take 15-30 seconds...")

        base_model_full = AutoModelForCausalLM.from_pretrained(
            base_model,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True
        )

        logger.info(f"✅ Base model loaded successfully")

        # 3. Load adapter weights
        logger.info(f"Loading PEFT adapters from {adapter_dir}")
        peft_model = PeftModel.from_pretrained(
            base_model_full,
            adapter_dir,
            is_trainable=False  # Important for inference/merge
        )

        logger.info("✅ Adapters loaded successfully")

        # 4. Merge adapters into base model
        logger.info("🔀 Merging adapters into base model...")
        logger.info("  This may take 1-2 minutes...")
        merged_model = peft_model.merge_and_unload()

        logger.info("✅ Merge completed successfully")

        # 5. Clean up memory
        del peft_model
        del base_model_full
        gc.collect()
        torch.cuda.empty_cache()

        # 6. Save merged model
        output_path = Path(output_dir) / "merged_model"
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"💾 Saving merged model to {output_path}")
        merged_model.save_pretrained(output_path)
        tokenizer.save_pretrained(output_path)

        logger.info(f"✅ Merged model saved successfully")

        # 7. Update result.json
        result_file = Path(output_dir) / "result.json"
        if result_file.exists():
            with open(result_file, 'r') as f:
                result = json.load(f)

            result["has_merged_model"] = True
            result["merged_dir"] = str(output_path)
            result["status"] = "completed"
            result["message"] = "Training and merge completed successfully"
            if "merge_error" in result:
                result["previous_merge_error"] = result.pop("merge_error")

            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)

            logger.info(f"✅ Updated result.json")

        return str(output_path)

    except Exception as e:
        logger.error(f"❌ Merge failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python retry_merge.py <job_id>")
        print("Example: python retry_merge.py fb4aa59e-9f2a-46ea-906c-f079e58ede48")
        sys.exit(1)

    job_id = sys.argv[1]
    workspace_dir = Path("/workspace/finetuning") / job_id

    if not workspace_dir.exists():
        logger.error(f"Job directory not found: {workspace_dir}")
        sys.exit(1)

    adapter_dir = workspace_dir / "output" / "adapter_model"
    output_dir = workspace_dir / "output"

    if not adapter_dir.exists():
        logger.error(f"Adapter directory not found: {adapter_dir}")
        sys.exit(1)

    # Read result.json to get base model
    result_file = output_dir / "result.json"
    if not result_file.exists():
        logger.error(f"result.json not found: {result_file}")
        sys.exit(1)

    with open(result_file, 'r') as f:
        result = json.load(f)

    # Try to find base model from training_config.json
    base_model = None
    config_file = workspace_dir / "input" / "training_config.json"
    if config_file.exists():
        logger.info(f"Reading config from {config_file}")
        with open(config_file, 'r') as f:
            config = json.load(f)
            base_model = config.get("base_model")
    else:
        # Try adapter_config.json as fallback
        adapter_config_file = adapter_dir / "adapter_config.json"
        if adapter_config_file.exists():
            logger.info(f"Reading base model from adapter config: {adapter_config_file}")
            with open(adapter_config_file, 'r') as f:
                adapter_config = json.load(f)
                base_model = adapter_config.get("base_model_name_or_path")

    if not base_model:
        logger.error("Could not determine base model. Please specify manually.")
        logger.error(f"Checked: {config_file} and {adapter_config_file}")
        sys.exit(1)

    logger.info(f"Starting merge for job: {job_id}")
    logger.info(f"Base model: {base_model}")

    try:
        merged_path = merge_adapter(str(adapter_dir), base_model, str(output_dir))
        logger.info(f"🎉 SUCCESS! Merged model saved to: {merged_path}")
    except Exception as e:
        logger.error(f"💥 FAILED: {e}")
        sys.exit(1)
