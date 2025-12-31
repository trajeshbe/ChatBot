"""
Trainer Factory

Routes training jobs to the appropriate trainer implementation based on fine-tuning method.

Supported methods:
- peft: LoRA/QLoRA with PEFT
- sft: Supervised Fine-Tuning with TRL
- unsloth: Unsloth optimized LoRA (2-5x faster, 70% less memory)
- rlhf-ppo: RLHF with Proximal Policy Optimization
- rlhf-grpo: RLHF with Group Relative Policy Optimization
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TrainerFactory:
    """
    Factory for creating and executing trainers

    Maps finetuning_method to trainer script
    """

    # Mapping of method to trainer script
    TRAINER_SCRIPTS = {
        "peft": "peft_trainer.py",
        "sft": "sft_trainer.py",
        "unsloth": "unsloth_trainer.py",
        "rlhf-ppo": "rlhf_ppo_trainer.py",
        "rlhf-grpo": "rlhf_grpo_trainer.py",
    }

    @staticmethod
    def get_trainer_script(finetuning_method: str) -> str:
        """
        Get trainer script name for a fine-tuning method

        Args:
            finetuning_method: Method name (peft, sft, rlhf-ppo, rlhf-grpo)

        Returns:
            Trainer script filename

        Raises:
            ValueError: If method is not supported
        """
        if finetuning_method not in TrainerFactory.TRAINER_SCRIPTS:
            raise ValueError(
                f"Unsupported fine-tuning method: {finetuning_method}. "
                f"Supported methods: {list(TrainerFactory.TRAINER_SCRIPTS.keys())}"
            )

        return TrainerFactory.TRAINER_SCRIPTS[finetuning_method]

    @staticmethod
    def validate_config(
        finetuning_method: str,
        config: Dict[str, Any]
    ) -> bool:
        """
        Validate configuration for a fine-tuning method

        Args:
            finetuning_method: Method name
            config: Training configuration

        Returns:
            True if valid, raises ValueError otherwise
        """
        # Required base config
        required_base = ["base_model", "hyperparameters"]
        for key in required_base:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")

        hyperparams = config["hyperparameters"]

        # Method-specific validation
        if finetuning_method == "peft" or finetuning_method == "unsloth":
            # PEFT and Unsloth require LoRA parameters
            required_peft = ["lora_r", "lora_alpha"]
            for key in required_peft:
                if key not in hyperparams:
                    logger.warning(f"Missing recommended PEFT parameter: {key}, using default")

        elif finetuning_method == "sft":
            # SFT requires max_seq_length
            if "max_seq_length" not in hyperparams:
                logger.warning("Missing max_seq_length for SFT, using default 2048")
                hyperparams["max_seq_length"] = 2048

        elif finetuning_method == "rlhf-ppo":
            # RLHF-PPO requires PPO-specific parameters
            recommended_ppo = ["ppo_epochs", "init_kl_coef", "target_kl"]
            for key in recommended_ppo:
                if key not in hyperparams:
                    logger.warning(f"Missing recommended PPO parameter: {key}, using default")

        elif finetuning_method == "rlhf-grpo":
            # RLHF-GRPO requires group_size
            if "group_size" not in hyperparams:
                logger.warning("Missing group_size for GRPO, using default 4")
                hyperparams["group_size"] = 4

        return True

    @staticmethod
    def get_default_hyperparameters(finetuning_method: str) -> Dict[str, Any]:
        """
        Get default hyperparameters for a fine-tuning method

        Args:
            finetuning_method: Method name

        Returns:
            Dictionary of default hyperparameters
        """
        defaults = {
            "peft": {
                "learning_rate": 2e-4,
                "num_epochs": 3,
                "batch_size": 4,
                "gradient_accumulation_steps": 4,
                "warmup_steps": 100,
                "logging_steps": 10,
                "save_steps": 100,
                "lora_r": 16,
                "lora_alpha": 32,
                "lora_dropout": 0.05,
                "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
            },
            "unsloth": {
                "learning_rate": 2e-4,
                "num_epochs": 3,
                "batch_size": 4,
                "gradient_accumulation_steps": 4,
                "warmup_steps": 100,
                "logging_steps": 10,
                "save_steps": 100,
                "lora_r": 16,
                "lora_alpha": 32,
                "lora_dropout": 0.05,
                "max_seq_length": 2048,
                "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
            },
            "sft": {
                "learning_rate": 2e-4,
                "num_epochs": 3,
                "batch_size": 4,
                "gradient_accumulation_steps": 4,
                "warmup_steps": 100,
                "logging_steps": 10,
                "save_steps": 100,
                "max_seq_length": 2048,
                "packing": False
            },
            "rlhf-ppo": {
                "learning_rate": 1.41e-5,
                "batch_size": 4,
                "mini_batch_size": 1,
                "ppo_epochs": 4,
                "gradient_accumulation_steps": 4,
                "warmup_steps": 100,
                "init_kl_coef": 0.2,
                "target_kl": 6.0,
                "adap_kl_ctrl": True,
                "max_grad_norm": 1.0,
                "max_new_tokens": 128
            },
            "rlhf-grpo": {
                "learning_rate": 1e-5,
                "num_epochs": 3,
                "batch_size": 4,
                "gradient_accumulation_steps": 4,
                "warmup_steps": 100,
                "group_size": 4,
                "kl_coef": 0.1,
                "clip_range": 0.2,
                "value_clip_range": 0.2,
                "max_new_tokens": 128,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }

        return defaults.get(finetuning_method, {})

    @staticmethod
    def merge_with_defaults(
        finetuning_method: str,
        user_hyperparameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge user hyperparameters with defaults

        Args:
            finetuning_method: Method name
            user_hyperparameters: User-provided hyperparameters

        Returns:
            Complete hyperparameters with defaults filled in
        """
        defaults = TrainerFactory.get_default_hyperparameters(finetuning_method)

        # Merge: user values override defaults
        merged = {**defaults, **user_hyperparameters}

        return merged

    @staticmethod
    def get_recommended_resources(
        finetuning_method: str,
        base_model: str,
        quantization: str = "4bit"
    ) -> Dict[str, Any]:
        """
        Get recommended resource allocation for a training configuration

        Args:
            finetuning_method: Training method
            base_model: Base model name
            quantization: Quantization level (4bit, 8bit, none)

        Returns:
            Recommended resources (GPUs, memory, CPU)
        """
        # Estimate model size from name
        if "7B" in base_model or "7b" in base_model:
            base_memory_gb = 7
        elif "13B" in base_model or "13b" in base_model:
            base_memory_gb = 13
        elif "70B" in base_model or "70b" in base_model:
            base_memory_gb = 70
        else:
            base_memory_gb = 7  # Default estimate

        # Adjust for quantization
        if quantization == "4bit":
            memory_multiplier = 0.4  # 4-bit uses ~40% of full precision
        elif quantization == "8bit":
            memory_multiplier = 0.6  # 8-bit uses ~60% of full precision
        else:
            memory_multiplier = 2.0  # Full precision + gradients

        # Calculate required memory
        required_memory_gb = base_memory_gb * memory_multiplier + 4  # +4GB for activation/batch

        # Determine GPU count
        if required_memory_gb <= 16:
            gpu_count = 1
        elif required_memory_gb <= 32:
            gpu_count = 2
        elif required_memory_gb <= 64:
            gpu_count = 4
        else:
            gpu_count = 8

        # CPU and RAM recommendations
        cpu_cores = min(8, gpu_count * 4)
        ram_gb = min(64, required_memory_gb * 2)

        return {
            "gpu_count": gpu_count,
            "min_gpu_memory_gb": max(12, required_memory_gb / gpu_count),
            "recommended_memory_gb": ram_gb,
            "recommended_cpu_cores": cpu_cores,
            "estimated_training_hours": get_estimated_training_time(
                finetuning_method,
                base_memory_gb,
                gpu_count
            )
        }


def get_estimated_training_time(
    finetuning_method: str,
    model_size_gb: float,
    gpu_count: int
) -> float:
    """
    Estimate training time in hours

    Args:
        finetuning_method: Training method
        model_size_gb: Model size in GB
        gpu_count: Number of GPUs

    Returns:
        Estimated training time in hours
    """
    # Base time estimates (very rough)
    base_times = {
        "peft": 2.0,  # PEFT is fastest
        "unsloth": 0.5,  # Unsloth is 2-5x faster than PEFT
        "sft": 4.0,   # SFT is moderate
        "rlhf-ppo": 8.0,  # RLHF is slowest
        "rlhf-grpo": 6.0  # GRPO is faster than PPO
    }

    base_time = base_times.get(finetuning_method, 4.0)

    # Adjust for model size
    size_multiplier = model_size_gb / 7.0  # Relative to 7B model

    # Adjust for GPU count (not perfectly linear)
    gpu_multiplier = 1.0 / (gpu_count ** 0.8)

    estimated_hours = base_time * size_multiplier * gpu_multiplier

    return round(estimated_hours, 1)


# Singleton instance
trainer_factory = TrainerFactory()
