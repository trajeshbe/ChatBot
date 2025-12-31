"""
Celery Tasks Module

Contains asynchronous background tasks for:
- Model fine-tuning
- Long-running training jobs
- GPU-accelerated operations
"""

from app.celery_app import celery_app

__all__ = ["celery_app"]
