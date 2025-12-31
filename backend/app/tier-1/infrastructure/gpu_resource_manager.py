"""
GPU Resource Manager - Automatic GPU Memory Cleanup
Ensures GPU memory is freed after tasks complete
"""

import logging
import asyncio
import httpx
import os
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GPUResourceManager:
    """Manages GPU resources and automatic cleanup"""

    def __init__(self, ollama_base_url: str = None):
        self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self._active_models: Dict[str, datetime] = {}  # model_name -> last_used_time
        self._cleanup_threshold_seconds = int(os.getenv("GPU_CLEANUP_THRESHOLD", "60"))  # 1 minute default
        self._cleanup_task = None
        self._running = False

    async def start_cleanup_monitor(self):
        """Start background cleanup monitor"""
        if self._running:
            logger.warning("Cleanup monitor already running")
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"🧹 GPU cleanup monitor started (threshold: {self._cleanup_threshold_seconds}s)")

    async def stop_cleanup_monitor(self):
        """Stop background cleanup monitor"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 GPU cleanup monitor stopped")

    async def _cleanup_loop(self):
        """Background task to cleanup idle models"""
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._cleanup_idle_models()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_idle_models(self):
        """Unload models that haven't been used recently"""
        now = datetime.now()
        models_to_unload = []

        for model_name, last_used in list(self._active_models.items()):
            idle_seconds = (now - last_used).total_seconds()
            if idle_seconds > self._cleanup_threshold_seconds:
                models_to_unload.append(model_name)

        for model_name in models_to_unload:
            await self.unload_model(model_name)
            del self._active_models[model_name]

    async def register_model_use(self, model_name: str):
        """Register that a model is being used"""
        self._active_models[model_name] = datetime.now()
        logger.debug(f"📊 Registered model use: {model_name}")

    async def unload_model(self, model_name: str) -> bool:
        """
        Unload a specific Ollama model from GPU

        Returns:
            bool: True if successfully unloaded
        """
        try:
            logger.info(f"🧹 Unloading model from GPU: {model_name}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Ollama doesn't have explicit unload, but we can delete loaded instance
                # Alternative: Use keep_alive=0 in next request
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": "",  # Empty prompt
                        "keep_alive": 0  # Immediately unload after this request
                    }
                )

            logger.info(f"✅ Model unloaded: {model_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to unload model {model_name}: {e}")
            return False

    async def unload_all_models(self) -> int:
        """
        Unload all Ollama models from GPU

        Returns:
            int: Number of models unloaded
        """
        try:
            logger.info("🧹 Unloading ALL Ollama models from GPU...")

            # Get list of loaded models
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    models_data = response.json()
                    models = models_data.get("models", [])

                    count = 0
                    for model_info in models:
                        model_name = model_info.get("name")
                        if model_name and await self.unload_model(model_name):
                            count += 1

                    logger.info(f"✅ Unloaded {count} models from GPU")
                    return count

        except Exception as e:
            logger.error(f"❌ Failed to unload all models: {e}")
            return 0

    async def get_gpu_memory_info(self) -> Dict[str, Any]:
        """Get GPU memory usage information"""
        try:
            import pynvml
            pynvml.nvmlInit()

            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)

            return {
                "total_mb": info.total / (1024**2),
                "free_mb": info.free / (1024**2),
                "used_mb": info.used / (1024**2),
                "used_percent": (info.used / info.total) * 100
            }
        except Exception as e:
            logger.warning(f"Could not get GPU info: {e}")
            return {}

    @asynccontextmanager
    async def gpu_task(self, model_name: str, task_type: str = "inference"):
        """
        Context manager for GPU tasks - automatically cleans up after

        Usage:
            async with gpu_manager.gpu_task("llama3.2-vision", "vision"):
                # Your GPU task here
                result = await vision_service.process(...)
            # GPU automatically freed here
        """
        logger.info(f"🎯 Starting GPU task: {task_type} with model {model_name}")
        await self.register_model_use(model_name)

        gpu_info_before = await self.get_gpu_memory_info()
        if gpu_info_before:
            logger.info(f"   GPU before: {gpu_info_before['free_mb']:.0f}MB free / {gpu_info_before['total_mb']:.0f}MB total")

        try:
            yield  # Execute the task
        finally:
            # Cleanup after task
            logger.info(f"🧹 Cleaning up GPU after {task_type} task")
            await self.unload_model(model_name)

            # Remove from active models
            if model_name in self._active_models:
                del self._active_models[model_name]

            gpu_info_after = await self.get_gpu_memory_info()
            if gpu_info_after:
                freed_mb = gpu_info_after['free_mb'] - gpu_info_before.get('free_mb', 0)
                logger.info(f"   GPU after: {gpu_info_after['free_mb']:.0f}MB free (freed {freed_mb:.0f}MB)")


# Global instance
_gpu_manager = None

def get_gpu_manager() -> GPUResourceManager:
    """Get global GPU resource manager instance"""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUResourceManager()
    return _gpu_manager
