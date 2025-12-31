"""
Models API Routes - Safe Fallback Version

This provides a minimal models API that works without the enhanced LLM service.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("/")
async def list_models():
    """
    Get available models - fallback version
    Returns basic model info without requiring GPU detection
    """
    try:
        # Try to import enhanced service
        try:
            from app.services.llm_service import llm_service
            models_info = llm_service.get_available_models()
            return JSONResponse(content=models_info)
        except ImportError:
            # Fallback to basic response
            logger.info("Using fallback model list (enhanced service not available)")
            return {
                "models": [
                    {
                        "id": "gpt-4-turbo",
                        "name": "GPT-4 Turbo",
                        "provider": "openai",
                        "type": "proprietary",
                        "available": True,
                        "recommended": True
                    }
                ],
                "grouped": {
                    "proprietary": [
                        {
                            "id": "gpt-4-turbo",
                            "name": "GPT-4 Turbo",
                            "provider": "openai",
                            "type": "proprietary",
                            "available": True,
                            "recommended": True
                        }
                    ],
                    "local_gpu": [],
                    "local_cpu": []
                },
                "default": "gpt-4-turbo",
                "gpu_info": {
                    "available": False,
                    "type": "cpu",
                    "memory_gb": 0
                }
            }
    except Exception as e:
        logger.error(f"Error in models endpoint: {e}")
        return {
            "models": [],
            "grouped": {"proprietary": [], "local_gpu": [], "local_cpu": []},
            "default": None,
            "gpu_info": {"available": False, "type": "cpu", "memory_gb": 0}
        }


@router.get("/gpu-info")
async def get_gpu_info():
    """Get GPU info - fallback version"""
    try:
        from app.utils.gpu_detector import get_gpu_detector
        detector = get_gpu_detector()
        gpu_info = detector.detect()
        return {
            "available": gpu_info.available,
            "type": gpu_info.type,
            "count": gpu_info.count,
            "memory_gb": gpu_info.memory_gb,
        }
    except ImportError:
        return {
            "available": False,
            "type": "cpu",
            "count": 0,
            "memory_gb": 0
        }
