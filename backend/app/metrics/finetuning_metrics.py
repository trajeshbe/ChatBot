"""
Prometheus metrics for fine-tuning training jobs.

This module defines Prometheus Gauge metrics that can be imported by both:
1. The backend (main.py) to register them in the metrics registry
2. The celery worker (finetuning_tasks.py) to update metric values during training

By keeping this separate from finetuning_tasks.py, we avoid importing Celery and
fine-tuning dependencies into the backend container.
"""

from prometheus_client import Gauge

# Training loss metric
finetuning_train_loss = Gauge(
    'finetuning_train_loss',
    'Current training loss',
    ['job_id', 'job_name', 'model']
)

# Evaluation loss metric
finetuning_eval_loss = Gauge(
    'finetuning_eval_loss',
    'Current evaluation loss',
    ['job_id', 'job_name', 'model']
)

# Current epoch metric
finetuning_current_epoch = Gauge(
    'finetuning_current_epoch',
    'Current training epoch',
    ['job_id', 'job_name']
)

# Progress percentage metric (0-100)
finetuning_progress_percent = Gauge(
    'finetuning_progress_percent',
    'Training progress percentage (0-100)',
    ['job_id', 'job_name']
)

# Total training steps metric
finetuning_total_steps = Gauge(
    'finetuning_total_steps',
    'Total training steps',
    ['job_id', 'job_name']
)

# Job status metric (1=training, 0=not training)
finetuning_job_status = Gauge(
    'finetuning_job_status',
    'Job status (1=training, 0=not training)',
    ['job_id', 'job_name', 'status']
)
