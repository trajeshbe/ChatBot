"""
GPU Pool Manager

Manages GPU allocation for concurrent fine-tuning jobs.
Prevents over-allocation and provides fair resource distribution.

Features:
- Automatic GPU detection
- Resource tracking (VRAM, utilization)
- Job queuing when GPUs busy
- Health monitoring
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """GPU device information"""
    device_id: str
    name: str
    total_memory_gb: float
    free_memory_gb: float
    utilization_percent: float
    temperature_celsius: Optional[float] = None
    is_available: bool = True


@dataclass
class GPUAllocation:
    """GPU allocation record"""
    job_id: str
    gpu_ids: List[str]
    allocated_at: datetime
    memory_reserved_gb: float


class GPUPoolManager:
    """
    Manages GPU resources for training jobs

    Responsibilities:
    - Track available GPUs
    - Allocate GPUs to jobs
    - Monitor GPU health
    - Handle allocation conflicts
    """

    def __init__(self, gpu_pool: Optional[List[str]] = None):
        """
        Initialize GPU pool manager

        Args:
            gpu_pool: List of GPU IDs to manage (e.g., ["0", "1"])
                     If None, auto-detect all GPUs
        """
        self.gpu_pool = gpu_pool or self._detect_gpus()
        self.allocations: Dict[str, GPUAllocation] = {}  # job_id -> allocation
        self.gpu_to_jobs: Dict[str, Set[str]] = defaultdict(set)  # gpu_id -> set of job_ids
        self._lock = asyncio.Lock()

        logger.info(f"🎮 GPU Pool Manager initialized with {len(self.gpu_pool)} GPUs: {self.gpu_pool}")

    def _detect_gpus(self) -> List[str]:
        """
        Auto-detect available GPUs

        Returns:
            List of GPU device IDs
        """
        try:
            import pynvml
            pynvml.nvmlInit()

            gpu_count = pynvml.nvmlDeviceGetCount()
            gpus = [str(i) for i in range(gpu_count)]

            logger.info(f"✅ Detected {gpu_count} GPUs")

            # Get GPU info
            for i in range(gpu_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                logger.info(f"  GPU {i}: {name} - {memory.total / 1024**3:.1f} GB")

            pynvml.nvmlShutdown()
            return gpus

        except ImportError:
            logger.warning("⚠️ pynvml not available, GPU detection disabled")
            return []
        except Exception as e:
            logger.error(f"❌ GPU detection failed: {e}")
            return []

    async def get_gpu_info(self, gpu_id: str) -> Optional[GPUInfo]:
        """
        Get detailed information about a GPU

        Args:
            gpu_id: GPU device ID

        Returns:
            GPUInfo or None if unavailable
        """
        try:
            import pynvml
            pynvml.nvmlInit()

            device_index = int(gpu_id)
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)

            # Get GPU info
            name = pynvml.nvmlDeviceGetName(handle)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

            try:
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temperature = None

            info = GPUInfo(
                device_id=gpu_id,
                name=name,
                total_memory_gb=memory.total / 1024**3,
                free_memory_gb=memory.free / 1024**3,
                utilization_percent=utilization.gpu,
                temperature_celsius=temperature,
                is_available=gpu_id not in self.gpu_to_jobs or len(self.gpu_to_jobs[gpu_id]) == 0
            )

            pynvml.nvmlShutdown()
            return info

        except Exception as e:
            logger.error(f"Failed to get GPU info for {gpu_id}: {e}")
            return None

    async def allocate_gpu(
        self,
        job_id: str,
        count: int = 1,
        memory_required_gb: float = 6.0  # 🆕 Reduced from 12GB to 6GB (safe for 7B models on 8GB GPU)
    ) -> Optional[List[str]]:
        """
        Allocate GPUs for a training job

        Args:
            job_id: Job identifier
            count: Number of GPUs to allocate
            memory_required_gb: Minimum free memory required per GPU

        Returns:
            List of allocated GPU IDs, or None if unavailable
        """
        async with self._lock:
            # Check if job already has allocation
            if job_id in self.allocations:
                logger.warning(f"Job {job_id} already has GPU allocation")
                return self.allocations[job_id].gpu_ids

            # Find available GPUs with sufficient memory
            available_gpus = []

            for gpu_id in self.gpu_pool:
                # Check if GPU is already allocated
                if gpu_id in self.gpu_to_jobs and len(self.gpu_to_jobs[gpu_id]) > 0:
                    continue

                # Check memory availability
                gpu_info = await self.get_gpu_info(gpu_id)
                if gpu_info and gpu_info.free_memory_gb >= memory_required_gb:
                    available_gpus.append(gpu_id)

                if len(available_gpus) >= count:
                    break

            if len(available_gpus) < count:
                logger.warning(
                    f"❌ Not enough GPUs available. "
                    f"Need {count}, have {len(available_gpus)} with >={memory_required_gb}GB free"
                )
                return None

            # Allocate GPUs
            allocated_gpus = available_gpus[:count]

            allocation = GPUAllocation(
                job_id=job_id,
                gpu_ids=allocated_gpus,
                allocated_at=datetime.utcnow(),
                memory_reserved_gb=memory_required_gb * count
            )

            self.allocations[job_id] = allocation

            for gpu_id in allocated_gpus:
                self.gpu_to_jobs[gpu_id].add(job_id)

            logger.info(
                f"✅ Allocated GPU {allocated_gpus} to job {job_id} "
                f"({memory_required_gb}GB reserved per GPU)"
            )

            return allocated_gpus

    async def release_gpu(self, job_id: str):
        """
        Release GPUs allocated to a job

        Args:
            job_id: Job identifier
        """
        async with self._lock:
            if job_id not in self.allocations:
                logger.warning(f"No GPU allocation found for job {job_id}")
                return

            allocation = self.allocations.pop(job_id)

            for gpu_id in allocation.gpu_ids:
                if job_id in self.gpu_to_jobs[gpu_id]:
                    self.gpu_to_jobs[gpu_id].remove(job_id)

            logger.info(f"🔓 Released GPU {allocation.gpu_ids} from job {job_id}")

    async def get_available_gpus(self) -> List[GPUInfo]:
        """
        Get list of available (unallocated) GPUs

        Returns:
            List of GPUInfo for available GPUs
        """
        available = []

        for gpu_id in self.gpu_pool:
            if gpu_id not in self.gpu_to_jobs or len(self.gpu_to_jobs[gpu_id]) == 0:
                gpu_info = await self.get_gpu_info(gpu_id)
                if gpu_info:
                    available.append(gpu_info)

        return available

    async def get_all_gpus_status(self) -> List[GPUInfo]:
        """
        Get status of all GPUs in pool

        Returns:
            List of GPUInfo for all GPUs
        """
        status = []

        for gpu_id in self.gpu_pool:
            gpu_info = await self.get_gpu_info(gpu_id)
            if gpu_info:
                # Mark as unavailable if allocated
                gpu_info.is_available = (
                    gpu_id not in self.gpu_to_jobs or
                    len(self.gpu_to_jobs[gpu_id]) == 0
                )
                status.append(gpu_info)

        return status

    async def get_allocation_for_job(self, job_id: str) -> Optional[GPUAllocation]:
        """
        Get GPU allocation for a specific job

        Args:
            job_id: Job identifier

        Returns:
            GPUAllocation or None
        """
        return self.allocations.get(job_id)

    async def wait_for_gpu(
        self,
        job_id: str,
        count: int = 1,
        memory_required_gb: float = 6.0,  # 🆕 Reduced from 12GB to 6GB (safe for 7B models on 8GB GPU)
        timeout_seconds: int = 3600
    ) -> Optional[List[str]]:
        """
        Wait for GPU to become available (with timeout)

        Args:
            job_id: Job identifier
            count: Number of GPUs needed
            memory_required_gb: Memory required per GPU
            timeout_seconds: Max wait time

        Returns:
            List of allocated GPU IDs, or None if timeout
        """
        start_time = datetime.utcnow()

        while True:
            # Try to allocate
            gpus = await self.allocate_gpu(job_id, count, memory_required_gb)

            if gpus:
                return gpus

            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= timeout_seconds:
                logger.error(f"❌ GPU allocation timeout for job {job_id} after {timeout_seconds}s")
                return None

            # Wait before retry
            logger.info(f"⏳ Waiting for GPU availability (job {job_id})...")
            await asyncio.sleep(30)  # Check every 30 seconds

    def get_stats(self) -> Dict[str, any]:
        """
        Get GPU pool statistics

        Returns:
            Statistics dictionary
        """
        return {
            "total_gpus": len(self.gpu_pool),
            "allocated_gpus": len([
                gpu_id for gpu_id in self.gpu_pool
                if gpu_id in self.gpu_to_jobs and len(self.gpu_to_jobs[gpu_id]) > 0
            ]),
            "available_gpus": len([
                gpu_id for gpu_id in self.gpu_pool
                if gpu_id not in self.gpu_to_jobs or len(self.gpu_to_jobs[gpu_id]) == 0
            ]),
            "active_jobs": len(self.allocations),
            "allocations": {
                job_id: {
                    "gpu_ids": alloc.gpu_ids,
                    "allocated_at": alloc.allocated_at.isoformat(),
                    "memory_reserved_gb": alloc.memory_reserved_gb
                }
                for job_id, alloc in self.allocations.items()
            }
        }


# Singleton instance
gpu_pool_manager = GPUPoolManager()
