"""
Hyperparameter Tuning Service with Optuna

Automated hyperparameter optimization for fine-tuning jobs.
Uses Optuna for Bayesian optimization with early stopping.

Features:
- Method-specific search spaces
- Parallel trial execution
- Pruning of unpromising trials
- Integration with existing fine-tuning infrastructure
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

logger = logging.getLogger(__name__)


class HyperparameterTuningService:
    """
    Service for automated hyperparameter tuning

    Uses Optuna to find optimal hyperparameters for fine-tuning jobs.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_search_space(
        self,
        finetuning_method: str,
        user_constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get hyperparameter search space for a fine-tuning method

        Args:
            finetuning_method: Training method (peft, sft, rlhf-ppo, rlhf-grpo)
            user_constraints: Optional user-specified constraints

        Returns:
            Search space configuration
        """
        # Base search spaces for each method
        search_spaces = {
            "peft": {
                "learning_rate": {"type": "loguniform", "low": 1e-5, "high": 5e-4},
                "num_epochs": {"type": "int", "low": 1, "high": 5},
                "batch_size": {"type": "categorical", "choices": [2, 4, 8]},
                "gradient_accumulation_steps": {"type": "categorical", "choices": [2, 4, 8]},
                "warmup_steps": {"type": "int", "low": 50, "high": 500},
                "lora_r": {"type": "categorical", "choices": [8, 16, 32, 64]},
                "lora_alpha": {"type": "categorical", "choices": [16, 32, 64, 128]},
                "lora_dropout": {"type": "uniform", "low": 0.0, "high": 0.1},
            },
            "sft": {
                "learning_rate": {"type": "loguniform", "low": 1e-5, "high": 5e-4},
                "num_epochs": {"type": "int", "low": 1, "high": 5},
                "batch_size": {"type": "categorical", "choices": [2, 4, 8]},
                "gradient_accumulation_steps": {"type": "categorical", "choices": [2, 4, 8]},
                "warmup_steps": {"type": "int", "low": 50, "high": 500},
                "max_seq_length": {"type": "categorical", "choices": [512, 1024, 2048]},
                "packing": {"type": "categorical", "choices": [True, False]},
            },
            "rlhf-ppo": {
                "learning_rate": {"type": "loguniform", "low": 1e-6, "high": 1e-4},
                "batch_size": {"type": "categorical", "choices": [2, 4, 8]},
                "mini_batch_size": {"type": "categorical", "choices": [1, 2, 4]},
                "ppo_epochs": {"type": "int", "low": 2, "high": 8},
                "gradient_accumulation_steps": {"type": "categorical", "choices": [2, 4, 8]},
                "init_kl_coef": {"type": "uniform", "low": 0.05, "high": 0.5},
                "target_kl": {"type": "uniform", "low": 3.0, "high": 10.0},
                "max_grad_norm": {"type": "uniform", "low": 0.5, "high": 2.0},
            },
            "rlhf-grpo": {
                "learning_rate": {"type": "loguniform", "low": 1e-6, "high": 1e-4},
                "batch_size": {"type": "categorical", "choices": [2, 4, 8]},
                "num_epochs": {"type": "int", "low": 1, "high": 5},
                "gradient_accumulation_steps": {"type": "categorical", "choices": [2, 4, 8]},
                "group_size": {"type": "categorical", "choices": [2, 4, 8]},
                "kl_coef": {"type": "uniform", "low": 0.05, "high": 0.3},
                "clip_range": {"type": "uniform", "low": 0.1, "high": 0.3},
            }
        }

        base_space = search_spaces.get(finetuning_method, {})

        # Apply user constraints
        if user_constraints:
            for param, constraint in user_constraints.items():
                if param in base_space:
                    # User can fix a parameter or narrow the range
                    if "fixed_value" in constraint:
                        base_space[param] = {"type": "fixed", "value": constraint["fixed_value"]}
                    elif "min" in constraint or "max" in constraint:
                        # Narrow range
                        if base_space[param]["type"] in ["uniform", "loguniform"]:
                            base_space[param]["low"] = constraint.get("min", base_space[param]["low"])
                            base_space[param]["high"] = constraint.get("max", base_space[param]["high"])
                        elif base_space[param]["type"] == "int":
                            base_space[param]["low"] = constraint.get("min", base_space[param]["low"])
                            base_space[param]["high"] = constraint.get("max", base_space[param]["high"])

        return base_space

    async def suggest_hyperparameters(
        self,
        trial: "optuna.Trial",
        finetuning_method: str,
        user_constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Suggest hyperparameters for a trial using Optuna

        Args:
            trial: Optuna trial object
            finetuning_method: Training method
            user_constraints: Optional user constraints

        Returns:
            Dictionary of suggested hyperparameters
        """
        search_space = self.get_search_space(finetuning_method, user_constraints)

        hyperparameters = {}

        for param_name, param_config in search_space.items():
            param_type = param_config["type"]

            if param_type == "fixed":
                # User-fixed parameter
                hyperparameters[param_name] = param_config["value"]

            elif param_type == "uniform":
                # Continuous uniform distribution
                hyperparameters[param_name] = trial.suggest_float(
                    param_name,
                    param_config["low"],
                    param_config["high"]
                )

            elif param_type == "loguniform":
                # Log-uniform distribution (for learning rate, etc.)
                hyperparameters[param_name] = trial.suggest_float(
                    param_name,
                    param_config["low"],
                    param_config["high"],
                    log=True
                )

            elif param_type == "int":
                # Integer parameter
                hyperparameters[param_name] = trial.suggest_int(
                    param_name,
                    param_config["low"],
                    param_config["high"]
                )

            elif param_type == "categorical":
                # Categorical parameter
                hyperparameters[param_name] = trial.suggest_categorical(
                    param_name,
                    param_config["choices"]
                )

        return hyperparameters

    async def create_tuning_study(
        self,
        name: str,
        finetuning_method: str,
        base_model: str,
        dataset_id: uuid.UUID,
        training_objective: str,
        n_trials: int = 20,
        user_constraints: Optional[Dict[str, Any]] = None,
        optimization_metric: str = "loss",  # or "accuracy", "f1", etc.
        user_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Create a hyperparameter tuning study

        Args:
            name: Study name
            finetuning_method: Training method
            base_model: Base model to fine-tune
            dataset_id: Dataset to use
            training_objective: Training objective
            n_trials: Number of trials to run
            user_constraints: User-specified constraints
            optimization_metric: Metric to optimize
            user_id: User ID
            project_id: Project ID

        Returns:
            Study configuration
        """
        try:
            import optuna

            # Create Optuna study
            study = optuna.create_study(
                study_name=name,
                direction="minimize" if optimization_metric == "loss" else "maximize",
                sampler=optuna.samplers.TPESampler(seed=42),  # Bayesian optimization
                pruner=optuna.pruners.MedianPruner(  # Prune unpromising trials
                    n_startup_trials=5,
                    n_warmup_steps=10
                )
            )

            study_config = {
                "study_id": str(uuid.uuid4()),
                "name": name,
                "finetuning_method": finetuning_method,
                "base_model": base_model,
                "dataset_id": str(dataset_id),
                "training_objective": training_objective,
                "n_trials": n_trials,
                "user_constraints": user_constraints or {},
                "optimization_metric": optimization_metric,
                "status": "created",
                "trials": [],
                "best_hyperparameters": None,
                "best_score": None,
                "created_at": datetime.utcnow().isoformat()
            }

            # Store study config in database (could add a tuning_studies table)
            # For now, return configuration

            logger.info(f"Created tuning study: {name} with {n_trials} trials")

            return study_config

        except ImportError:
            logger.error("Optuna not installed. Install with: pip install optuna")
            raise

    def get_tuning_progress(self, study_id: str) -> Dict[str, Any]:
        """
        Get progress of a tuning study

        Args:
            study_id: Study ID

        Returns:
            Progress information
        """
        # TODO: Implement study progress tracking
        # Would query trials from database and return:
        # - Number of completed trials
        # - Best trial so far
        # - Optimization history
        # - Estimated time remaining

        return {
            "study_id": study_id,
            "completed_trials": 0,
            "total_trials": 0,
            "best_score": None,
            "best_params": None,
            "status": "running"
        }

    def get_recommended_hyperparameters(
        self,
        finetuning_method: str,
        dataset_size: int,
        available_memory_gb: float
    ) -> Dict[str, Any]:
        """
        Get recommended hyperparameters based on heuristics

        Args:
            finetuning_method: Training method
            dataset_size: Number of training samples
            available_memory_gb: Available GPU memory

        Returns:
            Recommended hyperparameters
        """
        # Heuristic recommendations based on dataset size and memory
        recommendations = {}

        # Adjust batch size based on memory
        if available_memory_gb >= 24:
            batch_size = 8
        elif available_memory_gb >= 16:
            batch_size = 4
        else:
            batch_size = 2

        # Adjust epochs based on dataset size
        if dataset_size < 100:
            num_epochs = 10
        elif dataset_size < 1000:
            num_epochs = 5
        else:
            num_epochs = 3

        # Method-specific recommendations
        if finetuning_method == "peft":
            recommendations = {
                "learning_rate": 2e-4,
                "num_epochs": num_epochs,
                "batch_size": batch_size,
                "gradient_accumulation_steps": max(4 // batch_size, 1),
                "warmup_steps": min(100, dataset_size // 10),
                "lora_r": 16,
                "lora_alpha": 32,
                "lora_dropout": 0.05
            }

        elif finetuning_method == "sft":
            recommendations = {
                "learning_rate": 2e-4,
                "num_epochs": num_epochs,
                "batch_size": batch_size,
                "gradient_accumulation_steps": max(4 // batch_size, 1),
                "warmup_steps": min(100, dataset_size // 10),
                "max_seq_length": 2048,
                "packing": dataset_size > 1000
            }

        elif finetuning_method == "rlhf-ppo":
            recommendations = {
                "learning_rate": 1.41e-5,
                "batch_size": batch_size,
                "mini_batch_size": 1,
                "ppo_epochs": 4,
                "gradient_accumulation_steps": max(4 // batch_size, 1),
                "init_kl_coef": 0.2,
                "target_kl": 6.0,
                "max_grad_norm": 1.0
            }

        elif finetuning_method == "rlhf-grpo":
            recommendations = {
                "learning_rate": 1e-5,
                "batch_size": batch_size,
                "num_epochs": num_epochs,
                "gradient_accumulation_steps": max(4 // batch_size, 1),
                "group_size": 4,
                "kl_coef": 0.1,
                "clip_range": 0.2
            }

        logger.info(f"Recommended hyperparameters for {finetuning_method}: {recommendations}")

        return recommendations

    async def optimize_hyperparameters(
        self,
        study_config: Dict[str, Any],
        objective_function: Callable
    ) -> Dict[str, Any]:
        """
        Run hyperparameter optimization

        Args:
            study_config: Study configuration
            objective_function: Function to evaluate trial (returns metric value)

        Returns:
            Best hyperparameters and optimization results
        """
        try:
            import optuna

            # Create study
            study = optuna.create_study(
                study_name=study_config["name"],
                direction="minimize" if study_config["optimization_metric"] == "loss" else "maximize",
                sampler=optuna.samplers.TPESampler(seed=42),
                pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=10)
            )

            # Run optimization
            study.optimize(
                objective_function,
                n_trials=study_config["n_trials"],
                timeout=None,  # Can set time limit
                n_jobs=1  # Parallel trials (if supported)
            )

            # Get best results
            best_trial = study.best_trial

            results = {
                "best_hyperparameters": best_trial.params,
                "best_score": best_trial.value,
                "n_trials": len(study.trials),
                "optimization_history": [
                    {
                        "trial_number": trial.number,
                        "value": trial.value,
                        "params": trial.params,
                        "state": str(trial.state)
                    }
                    for trial in study.trials
                ],
                "study_name": study_config["name"]
            }

            logger.info(f"Optimization complete. Best score: {best_trial.value}")
            logger.info(f"Best hyperparameters: {best_trial.params}")

            return results

        except ImportError:
            logger.error("Optuna not installed")
            raise
