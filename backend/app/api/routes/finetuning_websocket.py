"""
WebSocket endpoint for real-time fine-tuning metrics streaming

Provides live updates for:
- Training metrics (loss, accuracy, learning rate)
- Job status changes
- GPU utilization
- Progress updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Set
import asyncio
import json
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.finetuning_models import FineTuningJob, TrainingMetric
from app.services.finetuning.gpu_pool_manager import gpu_pool_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/finetuning", tags=["finetuning-websocket"])


class ConnectionManager:
    """
    Manages WebSocket connections for real-time metrics streaming

    Features:
    - Job-specific subscriptions
    - Broadcast to all subscribers
    - Connection cleanup
    """

    def __init__(self):
        # job_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> job_id
        self.connection_jobs: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        """Connect a websocket to a specific job"""
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        self.connection_jobs[websocket] = job_id

        logger.info(f"WebSocket connected for job {job_id}")

    def disconnect(self, websocket: WebSocket):
        """Disconnect and cleanup"""
        if websocket in self.connection_jobs:
            job_id = self.connection_jobs[websocket]

            if job_id in self.active_connections:
                self.active_connections[job_id].discard(websocket)

                # Cleanup empty job entries
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]

            del self.connection_jobs[websocket]

            logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_to_job(self, job_id: str, message: dict):
        """Send message to all subscribers of a job"""
        if job_id not in self.active_connections:
            return

        # Create copy to avoid modification during iteration
        connections = self.active_connections[job_id].copy()

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast to all connections"""
        all_websockets = set(self.connection_jobs.keys())

        for websocket in all_websockets:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                self.disconnect(websocket)


# Singleton instance
manager = ConnectionManager()


@router.websocket("/ws/jobs/{job_id}/metrics")
async def websocket_job_metrics(
    websocket: WebSocket,
    job_id: str
):
    """
    WebSocket endpoint for real-time job metrics

    Streams:
    - Training metrics (every N steps)
    - Job status changes
    - Progress updates
    - Error messages

    Message format:
    {
        "type": "metric" | "status" | "progress" | "error" | "gpu",
        "timestamp": "ISO datetime",
        "data": { ... }
    }
    """
    await manager.connect(websocket, job_id)

    try:
        # Send initial job status
        async for db in get_db():
            query = select(FineTuningJob).where(FineTuningJob.id == job_id)
            result = await db.execute(query)
            job = result.scalar_one_or_none()

            if job:
                await websocket.send_json({
                    "type": "status",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "job_id": str(job.id),
                        "status": job.status,
                        "name": job.name,
                        "base_model": job.base_model,
                        "finetuning_method": job.finetuning_method
                    }
                })

            break  # Exit async generator

        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for client messages (ping/pong)
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )

                # Handle ping
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({
                    "type": "keepalive",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


@router.websocket("/ws/gpu/status")
async def websocket_gpu_status(websocket: WebSocket):
    """
    WebSocket endpoint for real-time GPU status

    Streams GPU metrics every 5 seconds:
    - Memory usage
    - Utilization
    - Temperature
    - Allocation status
    """
    await websocket.accept()

    try:
        while True:
            try:
                # Get GPU status
                gpu_status = await gpu_pool_manager.get_all_gpus_status()
                gpu_stats = gpu_pool_manager.get_stats()

                await websocket.send_json({
                    "type": "gpu_status",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "gpus": [
                            {
                                "device_id": gpu.device_id,
                                "name": gpu.name,
                                "total_memory_gb": gpu.total_memory_gb,
                                "free_memory_gb": gpu.free_memory_gb,
                                "utilization_percent": gpu.utilization_percent,
                                "temperature_celsius": gpu.temperature_celsius,
                                "is_available": gpu.is_available
                            }
                            for gpu in gpu_status
                        ],
                        "stats": gpu_stats
                    }
                })

                # Update every 5 seconds
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in GPU status stream: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("GPU status WebSocket disconnected")
    except Exception as e:
        logger.error(f"GPU WebSocket error: {e}", exc_info=True)


# ============================================================================
# UTILITY FUNCTIONS FOR SENDING UPDATES
# ============================================================================

async def send_metric_update(job_id: str, metric: TrainingMetric):
    """Send training metric update to subscribers"""
    await manager.send_to_job(job_id, {
        "type": "metric",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "step": metric.step,
            "epoch": metric.epoch,
            "loss": metric.loss,
            "learning_rate": metric.learning_rate,
            "accuracy": metric.accuracy,
            "additional_metrics": metric.additional_metrics
        }
    })


async def send_status_update(job_id: str, status: str, message: str = None):
    """Send job status update to subscribers"""
    await manager.send_to_job(job_id, {
        "type": "status",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "job_id": job_id,
            "status": status,
            "message": message
        }
    })


async def send_progress_update(job_id: str, current_step: int, total_steps: int, eta_seconds: float = None):
    """Send progress update to subscribers"""
    progress_percent = (current_step / total_steps * 100) if total_steps > 0 else 0

    await manager.send_to_job(job_id, {
        "type": "progress",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "current_step": current_step,
            "total_steps": total_steps,
            "progress_percent": progress_percent,
            "eta_seconds": eta_seconds
        }
    })


async def send_error(job_id: str, error: str):
    """Send error message to subscribers"""
    await manager.send_to_job(job_id, {
        "type": "error",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "error": error
        }
    })
