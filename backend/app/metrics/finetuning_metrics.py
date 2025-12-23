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

# ============================================================================
# MULTI-REWARD METRICS (for reasoning model training)
# ============================================================================

# Total reward score (weighted average of all reward functions)
reward_total_score = Gauge(
    'reward_total_score',
    'Total weighted reward score (0.0 - 1.0)',
    ['job_id', 'job_name', 'batch', 'response_idx']
)

# Individual reward function scores
reward_correctness_score = Gauge(
    'reward_correctness_score',
    'Correctness reward score (answer accuracy)',
    ['job_id', 'job_name', 'batch', 'response_idx']
)

reward_reasoning_clarity_score = Gauge(
    'reward_reasoning_clarity_score',
    'Reasoning clarity reward score (logical flow)',
    ['job_id', 'job_name', 'batch', 'response_idx']
)

reward_step_by_step_score = Gauge(
    'reward_step_by_step_score',
    'Step-by-step reward score (granularity)',
    ['job_id', 'job_name', 'batch', 'response_idx']
)

reward_efficiency_score = Gauge(
    'reward_efficiency_score',
    'Efficiency reward score (conciseness)',
    ['job_id', 'job_name', 'batch', 'response_idx']
)

reward_mathematical_notation_score = Gauge(
    'reward_mathematical_notation_score',
    'Mathematical notation reward score (domain-specific)',
    ['job_id', 'job_name', 'batch', 'response_idx']
)

reward_coherence_score = Gauge(
    'reward_coherence_score',
    'Coherence reward score (no contradictions)',
    ['job_id', 'job_name', 'batch', 'response_idx']
)

# Average reward scores per batch (aggregated)
reward_batch_avg_total = Gauge(
    'reward_batch_avg_total',
    'Average total reward per batch',
    ['job_id', 'job_name', 'batch']
)

reward_batch_avg_correctness = Gauge(
    'reward_batch_avg_correctness',
    'Average correctness reward per batch',
    ['job_id', 'job_name', 'batch']
)

reward_batch_avg_clarity = Gauge(
    'reward_batch_avg_clarity',
    'Average clarity reward per batch',
    ['job_id', 'job_name', 'batch']
)

# Reasoning quality metrics
reasoning_avg_steps_count = Gauge(
    'reasoning_avg_steps_count',
    'Average number of reasoning steps per response',
    ['job_id', 'job_name', 'batch']
)

reasoning_avg_tokens_per_step = Gauge(
    'reasoning_avg_tokens_per_step',
    'Average tokens per reasoning step',
    ['job_id', 'job_name', 'batch']
)

# Reward weights (for tracking configuration)
reward_weight_correctness = Gauge(
    'reward_weight_correctness',
    'Weight for correctness reward',
    ['job_id', 'job_name']
)

reward_weight_clarity = Gauge(
    'reward_weight_clarity',
    'Weight for reasoning clarity reward',
    ['job_id', 'job_name']
)

reward_weight_step_by_step = Gauge(
    'reward_weight_step_by_step',
    'Weight for step-by-step reward',
    ['job_id', 'job_name']
)

reward_weight_efficiency = Gauge(
    'reward_weight_efficiency',
    'Weight for efficiency reward',
    ['job_id', 'job_name']
)

reward_weight_math_notation = Gauge(
    'reward_weight_math_notation',
    'Weight for mathematical notation reward',
    ['job_id', 'job_name']
)

reward_weight_coherence = Gauge(
    'reward_weight_coherence',
    'Weight for coherence reward',
    ['job_id', 'job_name']
)
