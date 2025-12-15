"""
Base Trainer Class - Modular and Extensible

This module provides the abstract base class for all fine-tuning trainers.
New training methods can be easily added by extending this class.

Design Philosophy:
- Plugin architecture: New trainers are independent modules
- Configuration-driven: All parameters in config objects
- Callback system: Extensible monitoring and logging
- Async-ready: Support for distributed and async training

To add a new training method:
1. Create a new class that extends BaseTrainer
2. Implement abstract methods: prepare_model(), prepare_data(), train()
3. Register in trainer_factory.py
4. Add configuration schema in schemas/finetuning_schemas.py
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """
    Base configuration for all training methods

    This dataclass holds all training configuration.
    Extend for method-specific configs.
    """
    # Model configuration
    base_model: str
    quantization: Optional[str] = "4bit"  # "4bit", "8bit", "none"

    # Training objective
    training_objective: str = "qa"  # "qa", "classification", "summarization", "instruction"

    # Dataset configuration
    dataset_path: str = ""
    train_split: float = 0.8
    max_samples: Optional[int] = None

    # Common hyperparameters
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    warmup_steps: int = 100
    max_seq_length: int = 2048

    # Output configuration
    output_dir: str = "./finetuned_models"
    checkpoint_dir: str = "./checkpoints"
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100

    # Resource configuration
    gpu_count: int = 1
    mixed_precision: str = "fp16"  # "fp16", "bf16", "no"

    # Method-specific parameters (stored as dict for flexibility)
    method_params: Dict[str, Any] = field(default_factory=dict)

    # Callbacks and hooks
    enable_mlflow: bool = True
    enable_tensorboard: bool = True
    enable_wandb: bool = False

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.train_split <= 0 or self.train_split >= 1:
            raise ValueError(f"train_split must be between 0 and 1, got {self.train_split}")
        if self.learning_rate <= 0:
            raise ValueError(f"learning_rate must be positive, got {self.learning_rate}")

        # Create output directories
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.checkpoint_dir).mkdir(parents=True, exist_ok=True)


class TrainingCallback(ABC):
    """
    Abstract base class for training callbacks

    Callbacks allow you to hook into different stages of training
    without modifying the trainer code.
    """

    def on_train_begin(self, trainer: 'BaseTrainer', **kwargs):
        """Called at the beginning of training"""
        pass

    def on_train_end(self, trainer: 'BaseTrainer', **kwargs):
        """Called at the end of training"""
        pass

    def on_epoch_begin(self, trainer: 'BaseTrainer', epoch: int, **kwargs):
        """Called at the beginning of each epoch"""
        pass

    def on_epoch_end(self, trainer: 'BaseTrainer', epoch: int, metrics: Dict[str, float], **kwargs):
        """Called at the end of each epoch"""
        pass

    def on_step(self, trainer: 'BaseTrainer', step: int, metrics: Dict[str, float], **kwargs):
        """Called after each training step"""
        pass

    def on_evaluate(self, trainer: 'BaseTrainer', metrics: Dict[str, float], **kwargs):
        """Called after evaluation"""
        pass


class BaseTrainer(ABC):
    """
    Abstract base class for all fine-tuning trainers

    This class defines the common interface and provides utility methods
    that all trainers can use. Specific training methods (PEFT, SFT, etc.)
    extend this class and implement the abstract methods.

    Usage:
        class MyCustomTrainer(BaseTrainer):
            def prepare_model(self):
                # Custom model preparation
                pass

            def prepare_data(self, dataset):
                # Custom data preparation
                pass

            def train(self):
                # Custom training loop
                pass
    """

    def __init__(
        self,
        config: TrainingConfig,
        callbacks: Optional[List[TrainingCallback]] = None
    ):
        """
        Initialize base trainer

        Args:
            config: Training configuration
            callbacks: List of training callbacks
        """
        self.config = config
        self.callbacks = callbacks or []

        # Training state
        self.model = None
        self.tokenizer = None
        self.dataset = None
        self.current_epoch = 0
        self.current_step = 0
        self.training_start_time = None
        self.training_end_time = None

        # Metrics history
        self.metrics_history: List[Dict[str, Any]] = []

        logger.info(f"Initialized {self.__class__.__name__} with config: {config}")

    @abstractmethod
    def prepare_model(self):
        """
        Prepare the model for training

        This method should:
        1. Load the base model
        2. Apply quantization if needed
        3. Apply method-specific modifications (LoRA, etc.)
        4. Move model to appropriate device

        Returns:
            Prepared model and tokenizer
        """
        pass

    @abstractmethod
    def prepare_data(self, dataset_path: str) -> Any:
        """
        Prepare the dataset for training

        This method should:
        1. Load the dataset from path
        2. Apply preprocessing and tokenization
        3. Split into train/val sets
        4. Create data loaders

        Args:
            dataset_path: Path to dataset file

        Returns:
            Prepared dataset(s)
        """
        pass

    @abstractmethod
    def train(self) -> Dict[str, Any]:
        """
        Execute the training loop

        This method should:
        1. Run training for specified epochs
        2. Log metrics using callbacks
        3. Save checkpoints
        4. Return final metrics

        Returns:
            Dictionary containing final metrics and model path
        """
        pass

    # ========================================================================
    # Utility methods (implemented in base class, available to all trainers)
    # ========================================================================

    def add_callback(self, callback: TrainingCallback):
        """Add a callback to the trainer"""
        self.callbacks.append(callback)
        logger.info(f"Added callback: {callback.__class__.__name__}")

    def _trigger_callback(self, event: str, **kwargs):
        """Trigger callbacks for a specific event"""
        for callback in self.callbacks:
            method = getattr(callback, event, None)
            if method and callable(method):
                try:
                    method(self, **kwargs)
                except Exception as e:
                    logger.error(f"Error in callback {callback.__class__.__name__}.{event}: {e}")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """
        Log metrics to all configured backends

        Args:
            metrics: Dictionary of metric name -> value
            step: Training step number
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step or self.current_step,
            "epoch": self.current_epoch,
            **metrics
        }

        self.metrics_history.append(log_entry)

        # Log to console
        logger.info(f"Step {log_entry['step']}, Epoch {log_entry['epoch']}: {metrics}")

        # Trigger callbacks
        self._trigger_callback("on_step", step=log_entry["step"], metrics=metrics)

    def save_checkpoint(self, checkpoint_path: str, **additional_info):
        """
        Save a training checkpoint

        Args:
            checkpoint_path: Path to save checkpoint
            additional_info: Additional information to save
        """
        checkpoint_data = {
            "epoch": self.current_epoch,
            "step": self.current_step,
            "config": self.config.__dict__,
            "metrics_history": self.metrics_history,
            **additional_info
        }

        logger.info(f"Saved checkpoint to {checkpoint_path}")
        return checkpoint_data

    def estimate_training_time(self) -> Optional[float]:
        """
        Estimate remaining training time based on current progress

        Returns:
            Estimated seconds remaining, or None if cannot estimate
        """
        if not self.training_start_time or self.current_step == 0:
            return None

        elapsed = (datetime.now() - self.training_start_time).total_seconds()
        steps_per_second = self.current_step / elapsed

        # Estimate total steps
        total_steps = self.config.num_epochs * 1000  # Placeholder
        remaining_steps = total_steps - self.current_step

        return remaining_steps / steps_per_second if steps_per_second > 0 else None

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if self.model is None:
            return {}

        try:
            # Try to get parameter count
            num_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

            return {
                "total_parameters": num_params,
                "trainable_parameters": trainable_params,
                "trainable_percentage": 100 * trainable_params / num_params if num_params > 0 else 0,
                "model_type": self.model.__class__.__name__
            }
        except Exception as e:
            logger.warning(f"Could not get model info: {e}")
            return {}

    def cleanup(self):
        """Clean up resources after training"""
        # Clear CUDA cache if using GPU
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("Cleared CUDA cache")
        except ImportError:
            pass

        self.training_end_time = datetime.now()

        if self.training_start_time:
            duration = (self.training_end_time - self.training_start_time).total_seconds()
            logger.info(f"Training completed in {duration:.2f} seconds ({duration/60:.2f} minutes)")


# ============================================================================
# Pre-built Callbacks
# ============================================================================

class MetricsLoggerCallback(TrainingCallback):
    """Callback that logs metrics to a file"""

    def __init__(self, log_file: str):
        self.log_file = log_file

    def on_step(self, trainer: BaseTrainer, step: int, metrics: Dict[str, float], **kwargs):
        with open(self.log_file, "a") as f:
            f.write(f"Step {step}: {metrics}\n")


class CheckpointCallback(TrainingCallback):
    """Callback that saves checkpoints at regular intervals"""

    def __init__(self, checkpoint_dir: str, save_every_n_steps: int = 100):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.save_every_n_steps = save_every_n_steps
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def on_step(self, trainer: BaseTrainer, step: int, **kwargs):
        if step % self.save_every_n_steps == 0:
            checkpoint_path = self.checkpoint_dir / f"checkpoint-{step}.pt"
            trainer.save_checkpoint(str(checkpoint_path))


class EarlyStoppingCallback(TrainingCallback):
    """Callback that stops training if no improvement is seen"""

    def __init__(self, patience: int = 3, metric: str = "eval_loss", minimize: bool = True):
        self.patience = patience
        self.metric = metric
        self.minimize = minimize
        self.best_value = float('inf') if minimize else float('-inf')
        self.wait = 0

    def on_evaluate(self, trainer: BaseTrainer, metrics: Dict[str, float], **kwargs):
        current_value = metrics.get(self.metric)
        if current_value is None:
            return

        improved = (
            (self.minimize and current_value < self.best_value) or
            (not self.minimize and current_value > self.best_value)
        )

        if improved:
            self.best_value = current_value
            self.wait = 0
            logger.info(f"New best {self.metric}: {current_value}")
        else:
            self.wait += 1
            logger.info(f"No improvement for {self.wait} evaluations (patience: {self.patience})")

            if self.wait >= self.patience:
                logger.warning(f"Early stopping triggered after {self.wait} evaluations without improvement")
                # In a real implementation, we would need to signal the trainer to stop
                # This would require a more sophisticated architecture


# ============================================================================
# Helper Functions
# ============================================================================

def get_device():
    """Get the best available device for training"""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")
    except ImportError:
        return "cpu"


def count_parameters(model) -> Dict[str, int]:
    """Count total and trainable parameters in a model"""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {
        "total": total,
        "trainable": trainable,
        "frozen": total - trainable
    }
