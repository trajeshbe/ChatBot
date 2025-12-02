"""
Resource Checker - System Resource Monitoring

Checks available system resources (memory, GPU, CPU) to make
intelligent decisions about which tools/models to use.
"""

import logging
import subprocess
from typing import Dict, Optional
import psutil

logger = logging.getLogger(__name__)


class ResourceChecker:
    """
    Monitors system resources for intelligent tool selection

    Features:
    - Memory availability checking
    - GPU detection and memory checking
    - Model size vs available resource validation
    - Resource-aware tool recommendations
    """

    def __init__(self):
        """Initialize resource checker"""
        self._cached_gpu_info = None
        logger.info("ResourceChecker initialized")

    def get_memory_info(self) -> Dict[str, float]:
        """
        Get current memory information

        Returns:
            Dict with available_mb, total_mb, used_mb, percent_used
        """
        memory = psutil.virtual_memory()

        return {
            "available_mb": memory.available / (1024 * 1024),
            "total_mb": memory.total / (1024 * 1024),
            "used_mb": memory.used / (1024 * 1024),
            "percent_used": memory.percent,
            "available_gb": memory.available / (1024 * 1024 * 1024),
            "total_gb": memory.total / (1024 * 1024 * 1024)
        }

    def check_gpu_available(self) -> bool:
        """
        Check if GPU is available

        Returns:
            True if GPU detected, False otherwise
        """
        try:
            # Try nvidia-smi command
            result = subprocess.run(
                ['nvidia-smi'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"GPU check failed: {e}")
            return False

    def get_gpu_memory_info(self) -> Optional[Dict[str, float]]:
        """
        Get GPU memory information using nvidia-smi

        Returns:
            Dict with total_mb, used_mb, free_mb or None if no GPU
        """
        if self._cached_gpu_info is not None:
            return self._cached_gpu_info

        try:
            # Query GPU memory using nvidia-smi
            result = subprocess.run(
                [
                    'nvidia-smi',
                    '--query-gpu=memory.total,memory.used,memory.free',
                    '--format=csv,noheader,nounits'
                ],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                # Parse output (format: "total, used, free" in MB)
                lines = result.stdout.strip().split('\n')
                if lines:
                    # Take first GPU
                    total, used, free = map(float, lines[0].split(','))

                    gpu_info = {
                        "total_mb": total,
                        "used_mb": used,
                        "free_mb": free,
                        "percent_used": (used / total * 100) if total > 0 else 0
                    }

                    # Cache for 30 seconds (avoid repeated calls)
                    self._cached_gpu_info = gpu_info
                    return gpu_info

        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, Exception) as e:
            logger.debug(f"GPU memory check failed: {e}")

        return None

    def can_load_model(self, model_size_mb: int, use_gpu: bool = False) -> bool:
        """
        Check if model can be loaded with current resources

        Args:
            model_size_mb: Required memory in MB
            use_gpu: Whether model will use GPU

        Returns:
            True if sufficient resources available
        """
        if use_gpu:
            gpu_info = self.get_gpu_memory_info()
            if gpu_info:
                # Check if GPU has enough free memory (with 20% buffer)
                required_with_buffer = model_size_mb * 1.2
                can_load = gpu_info["free_mb"] >= required_with_buffer

                logger.info(
                    f"GPU memory check: {model_size_mb}MB model, "
                    f"{gpu_info['free_mb']:.0f}MB free → {'✅ OK' if can_load else '❌ Insufficient'}"
                )
                return can_load
            else:
                logger.warning(f"GPU requested but not available for {model_size_mb}MB model")
                return False
        else:
            # Check system RAM
            memory_info = self.get_memory_info()
            # Require 20% buffer for safety
            required_with_buffer = model_size_mb * 1.2
            can_load = memory_info["available_mb"] >= required_with_buffer

            logger.info(
                f"RAM check: {model_size_mb}MB model, "
                f"{memory_info['available_mb']:.0f}MB free → {'✅ OK' if can_load else '❌ Insufficient'}"
            )
            return can_load

    def get_recommended_vision_model(self) -> str:
        """
        Get recommended vision model based on available resources

        Returns:
            Model name string
        """
        memory_info = self.get_memory_info()
        available_gb = memory_info["available_gb"]

        # Model size requirements (approximate)
        models = [
            ("llama3.2-vision:11b", 5.5, "Best quality, highest resource"),
            ("llama3.2-vision:latest", 3.5, "Balanced quality and resource"),
            ("llava:7b", 4.0, "Good quality, moderate resource"),
            ("llava:13b", 7.0, "Excellent quality, high resource")
        ]

        # Find largest model that fits
        for model_name, required_gb, description in models:
            if available_gb >= required_gb * 1.2:  # 20% buffer
                logger.info(
                    f"Recommended vision model: {model_name} "
                    f"(requires {required_gb}GB, available {available_gb:.1f}GB) - {description}"
                )
                return model_name

        # Fallback to smallest model or disable vision
        logger.warning(
            f"Insufficient memory ({available_gb:.1f}GB) for vision models. "
            f"Recommend using OCR instead."
        )
        return "none"  # Indicates vision should be disabled

    def get_resource_summary(self) -> Dict[str, any]:
        """
        Get comprehensive resource summary

        Returns:
            Dict with memory, GPU, and recommendations
        """
        memory_info = self.get_memory_info()
        gpu_available = self.check_gpu_available()
        gpu_memory = self.get_gpu_memory_info() if gpu_available else None
        vision_model = self.get_recommended_vision_model()

        summary = {
            "memory": memory_info,
            "gpu": {
                "available": gpu_available,
                "memory": gpu_memory
            },
            "recommendations": {
                "vision_model": vision_model,
                "use_vision": vision_model != "none",
                "prefer_lightweight_models": memory_info["available_gb"] < 4.0
            }
        }

        return summary

    def log_resource_status(self):
        """Log current resource status for debugging"""
        summary = self.get_resource_summary()

        logger.info(
            f"📊 Resource Status:\n"
            f"   RAM: {summary['memory']['available_gb']:.1f}GB / {summary['memory']['total_gb']:.1f}GB "
            f"({summary['memory']['percent_used']:.1f}% used)\n"
            f"   GPU: {'Available' if summary['gpu']['available'] else 'Not available'}\n"
            f"   Vision Model: {summary['recommendations']['vision_model']}"
        )


# Global singleton
resource_checker = ResourceChecker()
