"""
Base classes for reward functions

Provides abstract base class and configuration for custom reward functions.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RewardConfig:
    """
    Configuration for a reward function

    Attributes:
        name: Unique identifier for the reward function
        weight: Weight for this reward in final score (default: 1.0)
        domain: Domain this reward applies to (general, math, physics, coding)
        enabled: Whether this reward is active
        config: Additional configuration parameters
    """
    name: str
    weight: float = 1.0
    domain: str = "general"
    enabled: bool = True
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class RewardFunction(ABC):
    """
    Abstract base class for reward functions

    All custom reward functions should inherit from this class
    and implement the compute() method.
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        """
        Initialize reward function

        Args:
            config: Optional configuration for this reward function
        """
        if config is None:
            config = RewardConfig(name=self.__class__.__name__)

        self.config = config
        self.name = config.name
        self.weight = config.weight
        self.domain = config.domain
        self.enabled = config.enabled

    @abstractmethod
    def compute(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Compute reward score for a response

        Args:
            prompt: The input prompt/question
            response: The model's response
            ground_truth: Optional correct answer for comparison
            reasoning_steps: Optional list of reasoning steps extracted from response
            metadata: Optional additional context (domain, difficulty, etc.)

        Returns:
            Reward score between 0.0 and 1.0

        Note:
            - Return value should be normalized to [0.0, 1.0] range
            - Higher score = better response
            - 0.0 = worst possible, 1.0 = perfect
        """
        pass

    def is_applicable(self, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if this reward function is applicable for given context

        Args:
            metadata: Context metadata (domain, task type, etc.)

        Returns:
            True if this reward should be computed, False otherwise
        """
        if not self.enabled:
            return False

        # Check domain applicability
        if metadata and "domain" in metadata:
            if self.domain != "general" and metadata["domain"] != self.domain:
                return False

        return True

    def __str__(self) -> str:
        return f"{self.name} (weight={self.weight}, domain={self.domain})"

    def __repr__(self) -> str:
        return f"RewardFunction(name='{self.name}', weight={self.weight}, domain='{self.domain}')"


class CompositeReward(RewardFunction):
    """
    Composite reward that combines multiple reward functions

    Useful for creating complex reward combinations.
    """

    def __init__(
        self,
        rewards: List[RewardFunction],
        config: Optional[RewardConfig] = None
    ):
        """
        Initialize composite reward

        Args:
            rewards: List of reward functions to combine
            config: Configuration (name, weight, etc.)
        """
        if config is None:
            config = RewardConfig(name="CompositeReward")

        super().__init__(config)
        self.rewards = rewards

    def compute(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Compute composite reward as weighted average

        Returns:
            Weighted average of all sub-rewards
        """
        if not self.rewards:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for reward in self.rewards:
            if not reward.is_applicable(metadata):
                continue

            score = reward.compute(
                prompt=prompt,
                response=response,
                ground_truth=ground_truth,
                reasoning_steps=reasoning_steps,
                metadata=metadata
            )

            weighted_sum += score * reward.weight
            total_weight += reward.weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0
