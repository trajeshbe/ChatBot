"""
Metrics Emitter for Multi-Reward Framework

Emits reward metrics to:
1. Prometheus (for Grafana dashboards)
2. WebSocket (for real-time frontend updates)
3. Database (for historical tracking)
4. TensorBoard (for training visualization)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RewardMetricsEmitter:
    """
    Emits reward metrics to multiple destinations

    Handles:
    - Prometheus metrics (via prometheus_client)
    - WebSocket streaming (via connection manager)
    - Database storage (via SQLAlchemy)
    - TensorBoard logging (via SummaryWriter)
    """

    def __init__(
        self,
        job_id: str,
        job_name: str,
        enable_prometheus: bool = True,
        enable_websocket: bool = True,
        enable_database: bool = True,
        enable_tensorboard: bool = True
    ):
        """
        Initialize metrics emitter

        Args:
            job_id: Unique job identifier
            job_name: Human-readable job name
            enable_prometheus: Enable Prometheus metrics export
            enable_websocket: Enable WebSocket streaming
            enable_database: Enable database storage
            enable_tensorboard: Enable TensorBoard logging
        """
        self.job_id = job_id
        self.job_name = job_name
        self.enable_prometheus = enable_prometheus
        self.enable_websocket = enable_websocket
        self.enable_database = enable_database
        self.enable_tensorboard = enable_tensorboard

        # Lazy-loaded components
        self._prometheus_metrics = None
        self._websocket_manager = None
        self._db_session = None
        self._tensorboard_writer = None

        # Batch tracking
        self.current_batch = 0

        logger.info(
            f"RewardMetricsEmitter initialized for job {job_id} "
            f"(prometheus={enable_prometheus}, websocket={enable_websocket}, "
            f"db={enable_database}, tensorboard={enable_tensorboard})"
        )

    def emit_reward_breakdown(
        self,
        total_reward: float,
        breakdown: Dict[str, Dict[str, float]],
        batch_idx: int,
        response_idx: int = 0,
        reasoning_steps: Optional[list] = None,
        step: Optional[int] = None
    ):
        """
        Emit reward breakdown to all enabled destinations

        Args:
            total_reward: Total weighted reward score
            breakdown: Dict of {reward_name: {score, weight, contribution, applicable}}
            batch_idx: Current batch index
            response_idx: Response index within batch (for GRPO group)
            reasoning_steps: Optional list of reasoning steps
            step: Optional global step count (for TensorBoard)
        """
        try:
            # Prometheus metrics
            if self.enable_prometheus:
                self._emit_to_prometheus(
                    total_reward, breakdown, batch_idx, response_idx
                )

            # WebSocket streaming
            if self.enable_websocket:
                self._emit_to_websocket(
                    total_reward, breakdown, batch_idx, response_idx, reasoning_steps
                )

            # Database storage
            if self.enable_database:
                self._emit_to_database(
                    total_reward, breakdown, batch_idx, response_idx, reasoning_steps
                )

            # TensorBoard logging
            if self.enable_tensorboard and step is not None:
                self._emit_to_tensorboard(
                    total_reward, breakdown, step, response_idx, reasoning_steps
                )

        except Exception as e:
            logger.error(f"Error emitting reward metrics: {e}")

    def emit_batch_aggregates(
        self,
        batch_idx: int,
        avg_total_reward: float,
        avg_rewards: Dict[str, float],
        avg_steps_count: float,
        avg_tokens_per_step: float
    ):
        """
        Emit batch-level aggregate metrics

        Args:
            batch_idx: Current batch index
            avg_total_reward: Average total reward for batch
            avg_rewards: Dict of {reward_name: avg_score}
            avg_steps_count: Average number of reasoning steps
            avg_tokens_per_step: Average tokens per step
        """
        try:
            if self.enable_prometheus:
                self._emit_batch_aggregates_to_prometheus(
                    batch_idx, avg_total_reward, avg_rewards,
                    avg_steps_count, avg_tokens_per_step
                )

            if self.enable_websocket:
                self._emit_batch_aggregates_to_websocket(
                    batch_idx, avg_total_reward, avg_rewards,
                    avg_steps_count, avg_tokens_per_step
                )

        except Exception as e:
            logger.error(f"Error emitting batch aggregates: {e}")

    def emit_reward_weights(self, weights: Dict[str, float]):
        """
        Emit current reward weights configuration

        Args:
            weights: Dict of {reward_name: weight}
        """
        try:
            if self.enable_prometheus:
                self._emit_weights_to_prometheus(weights)

            if self.enable_websocket:
                self._emit_weights_to_websocket(weights)

        except Exception as e:
            logger.error(f"Error emitting reward weights: {e}")

    def _emit_to_prometheus(
        self,
        total_reward: float,
        breakdown: Dict[str, Dict],
        batch_idx: int,
        response_idx: int
    ):
        """Emit metrics to Prometheus"""
        if self._prometheus_metrics is None:
            try:
                from app.metrics import finetuning_metrics
                self._prometheus_metrics = finetuning_metrics
            except ImportError:
                logger.warning("Prometheus metrics module not available")
                self.enable_prometheus = False
                return

        m = self._prometheus_metrics
        labels = {
            'job_id': self.job_id,
            'job_name': self.job_name,
            'batch': str(batch_idx),
            'response_idx': str(response_idx)
        }

        # Total reward
        m.reward_total_score.labels(**labels).set(total_reward)

        # Individual rewards
        reward_mapping = {
            'Correctness': m.reward_correctness_score,
            'ReasoningClarity': m.reward_reasoning_clarity_score,
            'StepByStep': m.reward_step_by_step_score,
            'Efficiency': m.reward_efficiency_score,
            'MathematicalNotation': m.reward_mathematical_notation_score,
            'Coherence': m.reward_coherence_score
        }

        for reward_name, details in breakdown.items():
            if details.get('applicable') and reward_name in reward_mapping:
                reward_mapping[reward_name].labels(**labels).set(details['score'])

    def _emit_batch_aggregates_to_prometheus(
        self,
        batch_idx: int,
        avg_total_reward: float,
        avg_rewards: Dict[str, float],
        avg_steps_count: float,
        avg_tokens_per_step: float
    ):
        """Emit batch aggregates to Prometheus"""
        if self._prometheus_metrics is None:
            return

        m = self._prometheus_metrics
        batch_labels = {
            'job_id': self.job_id,
            'job_name': self.job_name,
            'batch': str(batch_idx)
        }

        # Average total reward
        m.reward_batch_avg_total.labels(**batch_labels).set(avg_total_reward)

        # Average individual rewards
        if 'Correctness' in avg_rewards:
            m.reward_batch_avg_correctness.labels(**batch_labels).set(avg_rewards['Correctness'])

        if 'ReasoningClarity' in avg_rewards:
            m.reward_batch_avg_clarity.labels(**batch_labels).set(avg_rewards['ReasoningClarity'])

        # Reasoning quality
        m.reasoning_avg_steps_count.labels(**batch_labels).set(avg_steps_count)
        m.reasoning_avg_tokens_per_step.labels(**batch_labels).set(avg_tokens_per_step)

    def _emit_weights_to_prometheus(self, weights: Dict[str, float]):
        """Emit reward weights to Prometheus"""
        if self._prometheus_metrics is None:
            return

        m = self._prometheus_metrics
        weight_labels = {
            'job_id': self.job_id,
            'job_name': self.job_name
        }

        weight_mapping = {
            'Correctness': m.reward_weight_correctness,
            'ReasoningClarity': m.reward_weight_clarity,
            'StepByStep': m.reward_weight_step_by_step,
            'Efficiency': m.reward_weight_efficiency,
            'MathematicalNotation': m.reward_weight_math_notation,
            'Coherence': m.reward_weight_coherence
        }

        for reward_name, weight in weights.items():
            if reward_name in weight_mapping:
                weight_mapping[reward_name].labels(**weight_labels).set(weight)

    def _emit_to_websocket(
        self,
        total_reward: float,
        breakdown: Dict[str, Dict],
        batch_idx: int,
        response_idx: int,
        reasoning_steps: Optional[list]
    ):
        """Emit metrics to WebSocket for real-time updates"""
        # Lazy load websocket manager
        if self._websocket_manager is None:
            try:
                from app.api.routes.finetuning_websocket import send_metric_update
                self._websocket_manager = send_metric_update
            except ImportError:
                logger.warning("WebSocket module not available")
                self.enable_websocket = False
                return

        # Format reward breakdown for frontend
        metric_data = {
            "type": "multi_reward_breakdown",
            "timestamp": datetime.utcnow().isoformat(),
            "batch_idx": batch_idx,
            "response_idx": response_idx,
            "total_reward": total_reward,
            "breakdown": {
                name: {
                    "score": details.get("score", 0.0),
                    "weight": details.get("weight", 1.0),
                    "contribution": details.get("contribution", 0.0),
                    "applicable": details.get("applicable", True)
                }
                for name, details in breakdown.items()
            },
            "reasoning_steps_count": len(reasoning_steps) if reasoning_steps else 0
        }

        # Send to WebSocket
        try:
            self._websocket_manager(self.job_id, metric_data)
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")

    def _emit_batch_aggregates_to_websocket(
        self,
        batch_idx: int,
        avg_total_reward: float,
        avg_rewards: Dict[str, float],
        avg_steps_count: float,
        avg_tokens_per_step: float
    ):
        """Emit batch aggregates to WebSocket"""
        if self._websocket_manager is None:
            return

        metric_data = {
            "type": "batch_aggregate_rewards",
            "timestamp": datetime.utcnow().isoformat(),
            "batch_idx": batch_idx,
            "avg_total_reward": avg_total_reward,
            "avg_rewards": avg_rewards,
            "avg_steps_count": avg_steps_count,
            "avg_tokens_per_step": avg_tokens_per_step
        }

        try:
            self._websocket_manager(self.job_id, metric_data)
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")

    def _emit_weights_to_websocket(self, weights: Dict[str, float]):
        """Emit reward weights to WebSocket"""
        if self._websocket_manager is None:
            return

        metric_data = {
            "type": "reward_weights_config",
            "timestamp": datetime.utcnow().isoformat(),
            "weights": weights
        }

        try:
            self._websocket_manager(self.job_id, metric_data)
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")

    def _emit_to_database(
        self,
        total_reward: float,
        breakdown: Dict[str, Dict],
        batch_idx: int,
        response_idx: int,
        reasoning_steps: Optional[list]
    ):
        """Emit metrics to database for historical tracking"""
        # Database storage implementation
        # This would insert into a reward_metrics table
        # For now, we'll log it
        logger.debug(
            f"DB: Job {self.job_id}, Batch {batch_idx}, "
            f"Response {response_idx}, Total Reward: {total_reward:.3f}"
        )

    def _emit_to_tensorboard(
        self,
        total_reward: float,
        breakdown: Dict[str, Dict],
        step: int,
        response_idx: int,
        reasoning_steps: Optional[list]
    ):
        """Emit metrics to TensorBoard"""
        if self._tensorboard_writer is None:
            try:
                from torch.utils.tensorboard import SummaryWriter
                import os

                # TensorBoard log directory
                log_dir = os.path.join('/workspace/output/logs', self.job_id)
                self._tensorboard_writer = SummaryWriter(log_dir)
                logger.info(f"TensorBoard writer initialized: {log_dir}")

            except ImportError:
                logger.warning("TensorBoard not available")
                self.enable_tensorboard = False
                return

        writer = self._tensorboard_writer

        # Total reward
        writer.add_scalar(f'Rewards/Total/Response_{response_idx}', total_reward, step)

        # Individual rewards
        for reward_name, details in breakdown.items():
            if details.get('applicable'):
                writer.add_scalar(
                    f'Rewards/{reward_name}/Response_{response_idx}',
                    details['score'],
                    step
                )
                writer.add_scalar(
                    f'Rewards/{reward_name}_Contribution/Response_{response_idx}',
                    details['contribution'],
                    step
                )

        # Reasoning quality
        if reasoning_steps:
            writer.add_scalar(
                f'Reasoning/StepCount/Response_{response_idx}',
                len(reasoning_steps),
                step
            )

            avg_tokens = sum(len(step.split()) for step in reasoning_steps) / len(reasoning_steps)
            writer.add_scalar(
                f'Reasoning/AvgTokensPerStep/Response_{response_idx}',
                avg_tokens,
                step
            )

    def close(self):
        """Close TensorBoard writer"""
        if self._tensorboard_writer is not None:
            self._tensorboard_writer.close()
            logger.info("TensorBoard writer closed")
