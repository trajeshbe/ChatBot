"""
GPU Detection Utility

Detects available GPU resources and determines optimal LLM backend.
Supports NVIDIA CUDA, AMD ROCm, and CPU fallback.
"""

import subprocess
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """GPU information"""
    available: bool
    type: str  # 'nvidia', 'amd', 'cpu'
    count: int
    memory_gb: float
    names: List[str]
    driver_version: Optional[str] = None


class GPUDetector:
    """Detects GPU availability and capabilities"""

    def __init__(self):
        self._gpu_info: Optional[GPUInfo] = None
        self._detection_attempted = False

    def detect(self, force_refresh: bool = False) -> GPUInfo:
        """
        Detect GPU availability and capabilities

        Args:
            force_refresh: Force re-detection even if already cached

        Returns:
            GPUInfo object with detection results
        """
        if self._gpu_info and not force_refresh and self._detection_attempted:
            return self._gpu_info

        self._detection_attempted = True

        # Try NVIDIA first
        nvidia_info = self._detect_nvidia()
        if nvidia_info.available:
            self._gpu_info = nvidia_info
            logger.info(f"✓ NVIDIA GPU detected: {nvidia_info.count}x {nvidia_info.names[0]} ({nvidia_info.memory_gb:.1f} GB)")
            return self._gpu_info

        # Try AMD ROCm
        amd_info = self._detect_amd()
        if amd_info.available:
            self._gpu_info = amd_info
            logger.info(f"✓ AMD GPU detected: {amd_info.count}x {amd_info.names[0]}")
            return self._gpu_info

        # Fallback to CPU
        cpu_info = GPUInfo(
            available=False,
            type='cpu',
            count=0,
            memory_gb=0.0,
            names=['CPU']
        )
        self._gpu_info = cpu_info
        logger.info("No GPU detected, using CPU fallback")
        return self._gpu_info

    def _detect_nvidia(self) -> GPUInfo:
        """Detect NVIDIA GPUs using nvidia-smi"""
        try:
            # Check if nvidia-smi exists
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return GPUInfo(available=False, type='nvidia', count=0, memory_gb=0.0, names=[])

            # Parse output
            lines = result.stdout.strip().split('\n')
            gpus = []
            total_memory = 0.0
            driver_version = None

            for line in lines:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:
                    name = parts[0]
                    memory_str = parts[1].replace(' MiB', '')
                    memory_gb = float(memory_str) / 1024
                    gpus.append(name)
                    total_memory += memory_gb

                    if len(parts) >= 3 and not driver_version:
                        driver_version = parts[2]

            if gpus:
                return GPUInfo(
                    available=True,
                    type='nvidia',
                    count=len(gpus),
                    memory_gb=total_memory,
                    names=gpus,
                    driver_version=driver_version
                )

        except FileNotFoundError:
            logger.debug("nvidia-smi not found")
        except subprocess.TimeoutExpired:
            logger.warning("nvidia-smi timeout")
        except Exception as e:
            logger.debug(f"NVIDIA detection failed: {e}")

        return GPUInfo(available=False, type='nvidia', count=0, memory_gb=0.0, names=[])

    def _detect_amd(self) -> GPUInfo:
        """Detect AMD GPUs using rocm-smi"""
        try:
            result = subprocess.run(
                ['rocm-smi', '--showproductname'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return GPUInfo(available=False, type='amd', count=0, memory_gb=0.0, names=[])

            # Parse output (basic detection)
            lines = [l.strip() for l in result.stdout.split('\n') if l.strip()]
            gpus = [l for l in lines if 'GPU' in l]

            if gpus:
                return GPUInfo(
                    available=True,
                    type='amd',
                    count=len(gpus),
                    memory_gb=0.0,  # ROCm detection is more complex
                    names=['AMD GPU'] * len(gpus)
                )

        except FileNotFoundError:
            logger.debug("rocm-smi not found")
        except subprocess.TimeoutExpired:
            logger.warning("rocm-smi timeout")
        except Exception as e:
            logger.debug(f"AMD detection failed: {e}")

        return GPUInfo(available=False, type='amd', count=0, memory_gb=0.0, names=[])

    def get_recommended_backend(self) -> str:
        """
        Get recommended LLM backend based on available hardware

        Returns:
            'vllm' for GPU, 'llama.cpp' for CPU
        """
        info = self.detect()

        if info.available and info.type == 'nvidia' and info.memory_gb >= 4.0:
            return 'vllm'
        elif info.available and info.type == 'amd':
            return 'vllm'  # vLLM supports ROCm
        else:
            return 'llama.cpp'

    def get_optimal_model_for_memory(self, available_memory_gb: float) -> str:
        """
        Recommend optimal model size based on available GPU memory

        Args:
            available_memory_gb: Available GPU memory in GB

        Returns:
            Recommended model name
        """
        if available_memory_gb >= 80:
            return "meta-llama/Llama-3.1-70B-Instruct"
        elif available_memory_gb >= 40:
            return "meta-llama/Llama-3.1-8B-Instruct"
        elif available_memory_gb >= 16:
            return "meta-llama/Llama-3.2-3B-Instruct"
        elif available_memory_gb >= 8:
            return "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        else:
            return "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # CPU fallback

    def check_docker_gpu_support(self) -> bool:
        """Check if Docker has GPU support enabled"""
        try:
            result = subprocess.run(
                ['docker', 'info'],
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout.lower()
            return 'nvidia' in output or 'gpu' in output

        except Exception as e:
            logger.debug(f"Docker GPU check failed: {e}")
            return False

    def get_vllm_args(self) -> List[str]:
        """Get vLLM startup arguments based on detected hardware"""
        info = self.detect()

        args = []

        if info.available:
            # GPU-specific args
            args.extend([
                '--tensor-parallel-size', str(info.count),
                '--gpu-memory-utilization', '0.9',
            ])

            # Optimize for GPU memory
            if info.memory_gb < 16:
                args.extend([
                    '--max-model-len', '2048',
                    '--quantization', 'awq'  # Use quantization for small GPUs
                ])
            else:
                args.extend([
                    '--max-model-len', '4096',
                ])
        else:
            # CPU fallback (vLLM doesn't support CPU well)
            logger.warning("vLLM is not optimized for CPU, consider using llama.cpp")

        return args


# Global singleton
_gpu_detector: Optional[GPUDetector] = None


def get_gpu_detector() -> GPUDetector:
    """Get global GPU detector instance"""
    global _gpu_detector
    if _gpu_detector is None:
        _gpu_detector = GPUDetector()
    return _gpu_detector


def detect_gpu() -> GPUInfo:
    """Convenience function to detect GPU"""
    return get_gpu_detector().detect()


def get_recommended_backend() -> str:
    """Convenience function to get recommended backend"""
    return get_gpu_detector().get_recommended_backend()


# Auto-detect on import for logging
if os.getenv('DISABLE_GPU_DETECTION') != 'true':
    try:
        gpu_info = detect_gpu()
        if gpu_info.available:
            logger.info(f"🚀 GPU-accelerated inference enabled: {gpu_info.type.upper()}")
        else:
            logger.info("💻 CPU-only inference mode")
    except Exception as e:
        logger.warning(f"GPU detection failed during import: {e}")
