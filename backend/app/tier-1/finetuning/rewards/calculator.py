"""
Reasoning Reward Calculator

Manages multiple reward functions and computes weighted total rewards.
"""

from typing import List, Optional, Dict, Any, Tuple
import logging

from .base import RewardFunction, RewardConfig, CompositeReward
from .builtin_rewards import (
    CorrectnessReward,
    ReasoningClarityReward,
    StepByStepReward,
    EfficiencyReward,
    MathematicalNotationReward,
    CoherenceReward
)

logger = logging.getLogger(__name__)


class ReasoningRewardCalculator:
    """
    Main calculator for reasoning model rewards

    Manages multiple reward functions and computes weighted total.
    Supports:
    - Default reward set (6 core functions)
    - Custom reward functions
    - Dynamic weight adjustment
    - Domain-specific filtering
    """

    def __init__(
        self,
        reward_functions: Optional[List[RewardFunction]] = None,
        use_defaults: bool = True
    ):
        """
        Initialize reward calculator

        Args:
            reward_functions: Custom reward functions to use
            use_defaults: Whether to include default reward set
        """
        self.reward_functions: List[RewardFunction] = []

        # Add default rewards if requested
        if use_defaults:
            self.reward_functions.extend(self._get_default_rewards())

        # Add custom rewards
        if reward_functions:
            self.reward_functions.extend(reward_functions)

        logger.info(
            f"ReasoningRewardCalculator initialized with {len(self.reward_functions)} reward functions"
        )

    def compute_total_reward(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Compute total weighted reward across all applicable functions

        Args:
            prompt: The input prompt/question
            response: The model's response
            ground_truth: Optional correct answer
            reasoning_steps: Optional list of reasoning steps
            metadata: Optional context (domain, difficulty, etc.)

        Returns:
            Total weighted reward score (0.0 to 1.0)
        """
        if not self.reward_functions:
            logger.warning("No reward functions configured, returning neutral score")
            return 0.5

        total_weight = 0.0
        weighted_sum = 0.0

        for reward_fn in self.reward_functions:
            # Check if reward applies to this context
            if not reward_fn.is_applicable(metadata):
                continue

            try:
                # Compute individual reward
                score = reward_fn.compute(
                    prompt=prompt,
                    response=response,
                    ground_truth=ground_truth,
                    reasoning_steps=reasoning_steps,
                    metadata=metadata
                )

                # Add to weighted sum
                weighted_sum += score * reward_fn.weight
                total_weight += reward_fn.weight

                logger.debug(
                    f"{reward_fn.name}: score={score:.3f}, weight={reward_fn.weight}, "
                    f"contribution={score * reward_fn.weight:.3f}"
                )

            except Exception as e:
                logger.error(f"Error computing reward {reward_fn.name}: {e}")
                continue

        # Return weighted average
        if total_weight > 0:
            total_reward = weighted_sum / total_weight
            logger.info(
                f"Total reward: {total_reward:.3f} "
                f"(weighted_sum={weighted_sum:.3f}, total_weight={total_weight:.3f})"
            )
            return total_reward
        else:
            logger.warning("No applicable reward functions, returning neutral score")
            return 0.5

    def compute_detailed_rewards(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[str, Dict[str, float]]]:
        """
        Compute total reward with detailed breakdown per reward function

        Args:
            prompt: The input prompt/question
            response: The model's response
            ground_truth: Optional correct answer
            reasoning_steps: Optional list of reasoning steps
            metadata: Optional context

        Returns:
            Tuple of (total_reward, breakdown_dict)
            breakdown_dict format:
            {
                "CorrectnessReward": {
                    "score": 0.9,
                    "weight": 2.0,
                    "contribution": 1.8,
                    "applicable": True
                },
                ...
            }
        """
        if not self.reward_functions:
            return 0.5, {}

        breakdown = {}
        total_weight = 0.0
        weighted_sum = 0.0

        for reward_fn in self.reward_functions:
            # Check applicability
            is_applicable = reward_fn.is_applicable(metadata)

            if is_applicable:
                try:
                    # Compute reward
                    score = reward_fn.compute(
                        prompt=prompt,
                        response=response,
                        ground_truth=ground_truth,
                        reasoning_steps=reasoning_steps,
                        metadata=metadata
                    )

                    contribution = score * reward_fn.weight
                    weighted_sum += contribution
                    total_weight += reward_fn.weight

                    breakdown[reward_fn.name] = {
                        "score": score,
                        "weight": reward_fn.weight,
                        "contribution": contribution,
                        "applicable": True
                    }

                except Exception as e:
                    logger.error(f"Error computing reward {reward_fn.name}: {e}")
                    breakdown[reward_fn.name] = {
                        "score": 0.0,
                        "weight": reward_fn.weight,
                        "contribution": 0.0,
                        "applicable": True,
                        "error": str(e)
                    }
            else:
                breakdown[reward_fn.name] = {
                    "score": 0.0,
                    "weight": reward_fn.weight,
                    "contribution": 0.0,
                    "applicable": False
                }

        # Compute total
        total_reward = weighted_sum / total_weight if total_weight > 0 else 0.5

        return total_reward, breakdown

    def add_reward_function(self, reward_fn: RewardFunction):
        """Add a new reward function"""
        self.reward_functions.append(reward_fn)
        logger.info(f"Added reward function: {reward_fn.name}")

    def remove_reward_function(self, name: str):
        """Remove a reward function by name"""
        original_count = len(self.reward_functions)
        self.reward_functions = [
            rf for rf in self.reward_functions if rf.name != name
        ]
        removed_count = original_count - len(self.reward_functions)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} reward function(s) named '{name}'")
        else:
            logger.warning(f"No reward function found with name '{name}'")

    def update_weights(self, weights: Dict[str, float]):
        """
        Update weights for multiple reward functions

        Args:
            weights: Dict mapping reward name to new weight
        """
        for reward_fn in self.reward_functions:
            if reward_fn.name in weights:
                old_weight = reward_fn.weight
                reward_fn.weight = weights[reward_fn.name]
                reward_fn.config.weight = weights[reward_fn.name]
                logger.info(
                    f"Updated weight for {reward_fn.name}: {old_weight} -> {reward_fn.weight}"
                )

    def get_reward_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of all configured reward functions

        Returns:
            List of reward function info dicts
        """
        return [
            {
                "name": rf.name,
                "weight": rf.weight,
                "domain": rf.domain,
                "enabled": rf.enabled,
                "type": rf.__class__.__name__
            }
            for rf in self.reward_functions
        ]

    def _get_default_rewards(self) -> List[RewardFunction]:
        """
        Get default set of reasoning reward functions

        Returns:
            List of 6 default reward functions with standard weights
        """
        return [
            CorrectnessReward(
                RewardConfig(name="Correctness", weight=2.0, domain="general")
            ),
            ReasoningClarityReward(
                RewardConfig(name="ReasoningClarity", weight=1.5, domain="general")
            ),
            StepByStepReward(
                RewardConfig(name="StepByStep", weight=1.0, domain="general")
            ),
            EfficiencyReward(
                RewardConfig(name="Efficiency", weight=0.8, domain="general")
            ),
            MathematicalNotationReward(
                RewardConfig(name="MathematicalNotation", weight=1.2, domain="math")
            ),
            CoherenceReward(
                RewardConfig(name="Coherence", weight=1.0, domain="general")
            )
        ]

    def __str__(self) -> str:
        """String representation"""
        return f"ReasoningRewardCalculator({len(self.reward_functions)} functions)"

    def __repr__(self) -> str:
        """Detailed representation"""
        functions_str = ", ".join([rf.name for rf in self.reward_functions])
        return f"ReasoningRewardCalculator([{functions_str}])"


# Convenience function for quick usage
def create_default_calculator() -> ReasoningRewardCalculator:
    """
    Create calculator with default reward functions

    Returns:
        ReasoningRewardCalculator with 6 default rewards
    """
    return ReasoningRewardCalculator(use_defaults=True)


# Convenience function for custom configurations
def create_custom_calculator(
    weights: Optional[Dict[str, float]] = None,
    disabled_rewards: Optional[List[str]] = None
) -> ReasoningRewardCalculator:
    """
    Create calculator with custom configuration

    Args:
        weights: Custom weights for reward functions
        disabled_rewards: List of reward names to disable

    Returns:
        Configured ReasoningRewardCalculator
    """
    calculator = ReasoningRewardCalculator(use_defaults=True)

    # Update weights
    if weights:
        calculator.update_weights(weights)

    # Disable specific rewards
    if disabled_rewards:
        for name in disabled_rewards:
            for rf in calculator.reward_functions:
                if rf.name == name:
                    rf.enabled = False
                    rf.config.enabled = False

    return calculator
