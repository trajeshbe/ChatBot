"""
Built-in Reasoning Reward Functions

Implements 6 core reward functions for reasoning model training:
1. CorrectnessReward - Answer accuracy (fuzzy matching)
2. ReasoningClarityReward - Logical flow and structure
3. StepByStepReward - Appropriate granularity (3-7 steps optimal)
4. EfficiencyReward - Concise reasoning (15-50 tokens/step)
5. MathematicalNotationReward - Domain-specific notation
6. CoherenceReward - No contradictions in reasoning
"""

import re
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher
import logging

from .base import RewardFunction, RewardConfig

logger = logging.getLogger(__name__)


class CorrectnessReward(RewardFunction):
    """
    Reward based on answer correctness using fuzzy matching

    Compares model's answer against ground truth using:
    - Exact match (1.0)
    - High similarity >0.8 (0.9)
    - Medium similarity 0.5-0.8 (0.6)
    - Low similarity <0.5 (0.0)
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        if config is None:
            config = RewardConfig(name="CorrectnessReward", weight=2.0)
        super().__init__(config)

    def compute(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Compute correctness reward"""
        if not ground_truth:
            logger.warning("CorrectnessReward: No ground_truth provided, returning neutral score")
            return 0.5

        # Extract final answer from response (after reasoning steps)
        answer = self._extract_answer(response)

        # Normalize both strings
        answer_norm = self._normalize(answer)
        truth_norm = self._normalize(ground_truth)

        # Exact match
        if answer_norm == truth_norm:
            return 1.0

        # Fuzzy match using SequenceMatcher
        similarity = SequenceMatcher(None, answer_norm, truth_norm).ratio()

        if similarity > 0.8:
            return 0.9
        elif similarity > 0.5:
            return 0.6
        else:
            return 0.0

    def _extract_answer(self, response: str) -> str:
        """Extract final answer from response (after reasoning)"""
        # Look for common answer patterns
        patterns = [
            r"(?:answer|solution|result)[\s:]+(.+?)(?:\n|$)",
            r"(?:therefore|thus|hence)[\s:,]+(.+?)(?:\n|$)",
            r"(?:=|equals?)[\s]+(.+?)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: last line
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        return lines[-1] if lines else response

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Lowercase
        return text.lower()


class ReasoningClarityReward(RewardFunction):
    """
    Reward based on reasoning clarity and logical flow

    Checks for:
    - Numbered or bulleted steps (0.3)
    - Logical connectors ("therefore", "because", "thus") (0.3)
    - Proper structure (intro → steps → conclusion) (0.4)
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        if config is None:
            config = RewardConfig(name="ReasoningClarityReward", weight=1.5)
        super().__init__(config)

        self.logical_connectors = [
            "therefore", "thus", "hence", "consequently",
            "because", "since", "as", "given that",
            "this means", "which implies", "leads to"
        ]

    def compute(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Compute reasoning clarity reward"""
        score = 0.0
        response_lower = response.lower()

        # Check for numbered/bulleted steps (0.3 points)
        has_numbering = bool(re.search(r'^\s*[\d]+[\.\):]', response, re.MULTILINE))
        has_bullets = bool(re.search(r'^\s*[-•*]', response, re.MULTILINE))
        if has_numbering or has_bullets:
            score += 0.3

        # Check for logical connectors (0.3 points)
        connector_count = sum(
            1 for connector in self.logical_connectors
            if connector in response_lower
        )
        if connector_count >= 3:
            score += 0.3
        elif connector_count >= 1:
            score += 0.15

        # Check for proper structure (0.4 points)
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if len(lines) >= 3:
            # Has intro, steps, and conclusion
            has_intro = any(word in lines[0].lower() for word in ["let", "first", "to solve", "step"])
            has_conclusion = any(word in lines[-1].lower() for word in ["therefore", "thus", "answer", "result"])

            if has_intro and has_conclusion:
                score += 0.4
            elif has_intro or has_conclusion:
                score += 0.2

        return min(score, 1.0)


class StepByStepReward(RewardFunction):
    """
    Reward based on appropriate step granularity

    Optimal: 3-7 reasoning steps
    - 3-7 steps: 1.0
    - 2 or 8 steps: 0.7
    - 1 or 9+ steps: 0.3
    - 0 steps: 0.0
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        if config is None:
            config = RewardConfig(name="StepByStepReward", weight=1.0)
        super().__init__(config)

    def compute(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Compute step-by-step reward"""
        # Use provided reasoning_steps if available
        if reasoning_steps:
            num_steps = len(reasoning_steps)
        else:
            # Count steps from response
            num_steps = self._count_steps(response)

        # Reward based on step count
        if 3 <= num_steps <= 7:
            return 1.0
        elif num_steps == 2 or num_steps == 8:
            return 0.7
        elif num_steps == 1 or num_steps >= 9:
            return 0.3
        else:  # 0 steps
            return 0.0

    def _count_steps(self, response: str) -> int:
        """Count reasoning steps in response"""
        # Method 1: Numbered steps (1., 2., 3.)
        numbered = re.findall(r'^\s*[\d]+[\.\):]', response, re.MULTILINE)
        if numbered:
            return len(numbered)

        # Method 2: Bullet points
        bullets = re.findall(r'^\s*[-•*]', response, re.MULTILINE)
        if bullets:
            return len(bullets)

        # Method 3: Newlines (rough estimate)
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        # Filter out very short lines (likely not steps)
        steps = [line for line in lines if len(line.split()) > 3]
        return len(steps)


class EfficiencyReward(RewardFunction):
    """
    Reward based on reasoning efficiency (conciseness)

    Optimal: 15-50 tokens per step
    - 15-50 tokens/step: 1.0
    - 10-60 tokens/step: 0.7
    - 5-80 tokens/step: 0.4
    - Otherwise: 0.0
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        if config is None:
            config = RewardConfig(name="EfficiencyReward", weight=0.8)
        super().__init__(config)

    def compute(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Compute efficiency reward"""
        # Use provided reasoning_steps if available
        if reasoning_steps:
            steps = reasoning_steps
        else:
            # Extract steps from response
            steps = self._extract_steps(response)

        if not steps:
            return 0.5  # Neutral if no steps detected

        # Calculate average tokens per step
        total_tokens = sum(len(step.split()) for step in steps)
        avg_tokens_per_step = total_tokens / len(steps)

        # Reward based on efficiency
        if 15 <= avg_tokens_per_step <= 50:
            return 1.0
        elif 10 <= avg_tokens_per_step <= 60:
            return 0.7
        elif 5 <= avg_tokens_per_step <= 80:
            return 0.4
        else:
            return 0.0

    def _extract_steps(self, response: str) -> List[str]:
        """Extract reasoning steps from response"""
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        # Filter lines that look like steps (have reasonable length)
        steps = [line for line in lines if 5 < len(line.split()) < 100]
        return steps


class MathematicalNotationReward(RewardFunction):
    """
    Reward for proper mathematical notation (domain-specific)

    Only applies to math/physics domains.
    Checks for:
    - Equations (=, +, -, *, /) (0.3)
    - Mathematical symbols (√, ², ³, π, etc.) (0.3)
    - Units (m, kg, s, etc.) (0.2)
    - Proper formatting (0.2)
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        if config is None:
            config = RewardConfig(
                name="MathematicalNotationReward",
                weight=1.2,
                domain="math"
            )
        super().__init__(config)

        self.math_symbols = ['√', '²', '³', 'π', '∞', '≈', '≠', '≤', '≥', '∫', '∑', 'Δ']
        self.units = ['m', 'kg', 's', 'N', 'J', 'W', 'V', 'A', 'Ω', 'Hz', 'Pa']

    def is_applicable(self, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Only apply to math/physics domains"""
        if not super().is_applicable(metadata):
            return False

        if metadata and "domain" in metadata:
            return metadata["domain"] in ["math", "physics", "engineering"]

        return True

    def compute(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Compute mathematical notation reward"""
        score = 0.0

        # Check for equations (0.3 points)
        has_equations = bool(re.search(r'[=+\-*/]', response))
        equation_count = len(re.findall(r'=', response))
        if equation_count >= 3:
            score += 0.3
        elif has_equations:
            score += 0.15

        # Check for mathematical symbols (0.3 points)
        symbol_count = sum(1 for symbol in self.math_symbols if symbol in response)
        if symbol_count >= 2:
            score += 0.3
        elif symbol_count >= 1:
            score += 0.15

        # Check for units (0.2 points)
        unit_pattern = r'\b\d+\.?\d*\s*(' + '|'.join(self.units) + r')\b'
        has_units = bool(re.search(unit_pattern, response))
        if has_units:
            score += 0.2

        # Check for proper formatting (0.2 points)
        # Look for LaTeX-style or clear mathematical expressions
        has_formatting = bool(re.search(r'\$.*?\$|\\[a-zA-Z]+\{', response))
        if has_formatting:
            score += 0.2
        elif has_equations and has_units:
            score += 0.1  # Partial credit for basic formatting

        return min(score, 1.0)


class CoherenceReward(RewardFunction):
    """
    Reward for reasoning coherence (no contradictions)

    Checks for:
    - No contradictory statements (0.5)
    - Consistent terminology (0.3)
    - Logical flow without jumps (0.2)
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        if config is None:
            config = RewardConfig(name="CoherenceReward", weight=1.0)
        super().__init__(config)

        self.contradiction_markers = [
            ("but", "however", "although"),
            ("not", "never", "cannot"),
            ("incorrect", "wrong", "false")
        ]

    def compute(
        self,
        prompt: str,
        response: str,
        ground_truth: Optional[str] = None,
        reasoning_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Compute coherence reward"""
        score = 1.0  # Start with perfect score, deduct for issues
        response_lower = response.lower()

        # Check for contradictory statements (deduct up to 0.5)
        sentences = re.split(r'[.!?]', response)
        contradiction_count = 0

        for i, sent1 in enumerate(sentences):
            for sent2 in sentences[i+1:]:
                if self._are_contradictory(sent1, sent2):
                    contradiction_count += 1

        if contradiction_count > 0:
            score -= min(0.5, contradiction_count * 0.2)

        # Check for inconsistent terminology (deduct up to 0.3)
        # Example: using "x" and "y" interchangeably for same variable
        if self._has_inconsistent_terminology(response):
            score -= 0.3

        # Check for logical jumps (deduct up to 0.2)
        if reasoning_steps and len(reasoning_steps) > 1:
            for i in range(len(reasoning_steps) - 1):
                if self._has_logical_jump(reasoning_steps[i], reasoning_steps[i+1]):
                    score -= 0.1
                    break

        return max(score, 0.0)

    def _are_contradictory(self, sent1: str, sent2: str) -> bool:
        """Check if two sentences contradict each other"""
        sent1_lower = sent1.lower()
        sent2_lower = sent2.lower()

        # Simple heuristic: same subject with negation
        # Example: "x is 5" vs "x is not 5"
        for word in ["is", "equals", "means"]:
            if word in sent1_lower and word in sent2_lower:
                # Check if one has negation and other doesn't
                has_neg1 = any(neg in sent1_lower for neg in ["not", "never", "cannot"])
                has_neg2 = any(neg in sent2_lower for neg in ["not", "never", "cannot"])
                if has_neg1 != has_neg2:
                    # Same subject?
                    words1 = set(sent1_lower.split())
                    words2 = set(sent2_lower.split())
                    common = words1.intersection(words2)
                    if len(common) > 2:  # Significant overlap
                        return True

        return False

    def _has_inconsistent_terminology(self, response: str) -> bool:
        """Check for inconsistent terminology"""
        # Look for variable reassignments or inconsistent naming
        # Example: "let x = 5" ... "now y = 5" (should be x)

        # Extract variable definitions
        var_pattern = r'(?:let|set|assume)\s+([a-zA-Z])\s*=\s*(\S+)'
        definitions = re.findall(var_pattern, response.lower())

        # Check if same value assigned to different variables
        values = {}
        for var, val in definitions:
            if val in values and values[val] != var:
                return True
            values[val] = var

        return False

    def _has_logical_jump(self, step1: str, step2: str) -> bool:
        """Check if there's a logical jump between steps"""
        # Simple heuristic: very different vocabulary = potential jump
        words1 = set(step1.lower().split())
        words2 = set(step2.lower().split())

        # Remove common words
        common_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at"}
        words1 -= common_words
        words2 -= common_words

        # Calculate overlap
        if not words1 or not words2:
            return False

        overlap = len(words1.intersection(words2))
        max_len = max(len(words1), len(words2))
        overlap_ratio = overlap / max_len

        # If less than 20% overlap, likely a jump
        return overlap_ratio < 0.2
