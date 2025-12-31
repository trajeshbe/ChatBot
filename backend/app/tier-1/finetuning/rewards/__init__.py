"""
Reasoning Reward Functions Framework

Multi-reward system for reasoning model training (GRPO/RLHF).
Supports custom reward functions, weighted combinations, and real-time tracking.
"""

from .base import RewardFunction, RewardConfig
from .calculator import ReasoningRewardCalculator
from .builtin_rewards import (
    CorrectnessReward,
    ReasoningClarityReward,
    StepByStepReward,
    EfficiencyReward,
    MathematicalNotationReward,
    CoherenceReward
)

__all__ = [
    "RewardFunction",
    "RewardConfig",
    "ReasoningRewardCalculator",
    "CorrectnessReward",
    "ReasoningClarityReward",
    "StepByStepReward",
    "EfficiencyReward",
    "MathematicalNotationReward",
    "CoherenceReward",
]
