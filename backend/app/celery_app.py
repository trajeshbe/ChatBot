"""
Celery Application Configuration

Configures Celery for distributed task queue with Redis backend.
"""

from celery import Celery
import os

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Create Celery app
celery_app = Celery(
    "finetuning",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.finetuning_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=86400,  # 24 hours max
    task_soft_time_limit=82800,  # 23 hours soft limit
    worker_prefetch_multiplier=1,  # One task at a time for GPU jobs
    worker_max_tasks_per_child=1,  # Restart worker after each task to free GPU memory
)

# Optional: Configure result expiration
celery_app.conf.result_expires = 86400  # Results expire after 24 hours
