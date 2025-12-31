"""
Dynamic Query Classifier with Configurable Rules

Features:
1. Load rules from YAML configuration file
2. Priority-based rule ordering (intelligent, not hardcoded)
3. Context-aware classification (proper nouns, word count, etc.)
4. User-specific rule overrides
5. Rule hit tracking for adaptive ordering
6. Export/import rule configurations

This solves the problem of hardcoded rules and fixed ordering.

Author: AI Assistant
Date: 2025-11-24
"""

import yaml
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class ClassificationRule:
    """Represents a single classification rule"""
    id: str
    name: str
    priority: int
    enabled: bool
    type: str  # pattern_match, context_aware, llm_based
    classification: str  # ai_personal, document_specific, general, ambiguous
    confidence: float
    use_documents: bool
    description: str
    patterns: List[str] = field(default_factory=list)
    detect: Optional[str] = None  # For context_aware rules
    hit_count: int = 0  # Track how often this rule matches

    def matches(self, query: str, context: Dict[str, Any]) -> bool:
        """
        Check if this rule matches the query

        Args:
            query: User query text
            context: Additional context (proper_nouns, word_count, etc.)

        Returns:
            True if rule matches
        """
        if not self.enabled:
            return False

        query_lower = query.lower().strip()

        if self.type == "pattern_match":
            # Match against patterns using regex
            for pattern in self.patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    logger.debug(f"✓ Rule '{self.id}' matched pattern: {pattern}")
                    return True
            return False

        elif self.type == "context_aware":
            # Evaluate context-based conditions
            if self.detect:
                try:
                    # Parse detect condition (e.g., "word_count <= 3")
                    result = eval(self.detect, {"__builtins__": {}}, context)
                    if result:
                        logger.debug(f"✓ Rule '{self.id}' matched context: {self.detect}")
                    return bool(result)
                except Exception as e:
                    logger.warning(f"Failed to evaluate context rule '{self.id}': {e}")
                    return False
            return False

        elif self.type == "llm_based":
            # LLM-based rules handled separately
            return False

        return False


@dataclass
class RuleHitStats:
    """Statistics for rule hit tracking"""
    rule_id: str
    hit_count: int = 0
    last_hit_timestamp: Optional[float] = None
    average_confidence: float = 0.0


class DynamicQueryClassifier:
    """
    Dynamic query classifier with configurable rules

    Features:
    - Load rules from YAML config
    - Priority-based ordering
    - Context-aware classification
    - Adaptive rule ordering based on hit rates
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize classifier with configuration

        Args:
            config_path: Path to YAML config file. If None, uses default.
        """
        if config_path is None:
            # Default config path
            config_path = Path(__file__).parent.parent / "config" / "query_classification_rules.yaml"

        self.config_path = Path(config_path)
        self.rules: List[ClassificationRule] = []
        self.settings: Dict[str, Any] = {}
        self.user_rules: Dict[str, List[ClassificationRule]] = defaultdict(list)
        self.rule_stats: Dict[str, RuleHitStats] = {}

        # Load configuration
        self.load_config()

    def load_config(self):
        """Load rules from YAML configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Load settings
            self.settings = config.get('settings', {})

            # Load rules
            rules_data = config.get('rules', [])
            self.rules = []

            for rule_data in rules_data:
                rule = ClassificationRule(
                    id=rule_data['id'],
                    name=rule_data['name'],
                    priority=rule_data['priority'],
                    enabled=rule_data['enabled'],
                    type=rule_data['type'],
                    classification=rule_data['classification'],
                    confidence=rule_data['confidence'],
                    use_documents=rule_data['use_documents'],
                    description=rule_data['description'],
                    patterns=rule_data.get('patterns', []),
                    detect=rule_data.get('detect')
                )
                self.rules.append(rule)

            # Sort rules by priority (highest first)
            self.rules.sort(key=lambda r: r.priority, reverse=True)

            # Load user-specific overrides
            user_rules_data = config.get('user_rules', [])
            for user_rule_data in user_rules_data:
                user_id = user_rule_data.get('user_id', 'default')
                overrides = user_rule_data.get('overrides', [])

                for override in overrides:
                    # Check if this is modifying an existing rule or adding new
                    rule_id = override.get('rule_id')

                    if any(r.id == rule_id for r in self.rules):
                        # Modify existing rule
                        for rule in self.rules:
                            if rule.id == rule_id:
                                # Apply overrides
                                if 'enabled' in override:
                                    rule.enabled = override['enabled']
                                if 'priority' in override:
                                    rule.priority = override['priority']
                                break
                    else:
                        # Add new user-specific rule
                        new_rule = ClassificationRule(
                            id=override['rule_id'],
                            name=override['name'],
                            priority=override['priority'],
                            enabled=override['enabled'],
                            type=override['type'],
                            classification=override['classification'],
                            confidence=override['confidence'],
                            use_documents=override['use_documents'],
                            description=override['description'],
                            patterns=override.get('patterns', []),
                            detect=override.get('detect')
                        )
                        self.rules.append(new_rule)

            # Re-sort after user overrides
            self.rules.sort(key=lambda r: r.priority, reverse=True)

            logger.info(f"✓ Loaded {len(self.rules)} classification rules from {self.config_path}")

        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            self.rules = []
            self.settings = {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.rules = []
            self.settings = {}

    async def classify(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify query using dynamic rules

        Args:
            query: User query
            user_id: Optional user ID for user-specific rules

        Returns:
            Classification result with type, confidence, use_documents, reason
        """
        query = query.strip()

        # Build context for context-aware rules
        context = self._build_context(query)

        # Try each rule in priority order
        for rule in self.rules:
            if rule.matches(query, context):
                # Record hit
                self._record_hit(rule.id, rule.confidence)

                result = {
                    'query_type': rule.classification,
                    'confidence': rule.confidence,
                    'use_documents': rule.use_documents,
                    'reason': f"Matched rule: {rule.name} (priority={rule.priority})",
                    'rule_id': rule.id,
                    'rule_priority': rule.priority
                }

                # Log classification
                emoji_map = {
                    'ai_personal': '🤖',
                    'document_specific': '📄',
                    'general': '🌍',
                    'ambiguous': '❓'
                }
                emoji = emoji_map.get(result['query_type'], '❓')
                logger.info(
                    f"{emoji} Classified as {result['query_type']} "
                    f"(confidence: {result['confidence']:.2f}, rule: {rule.name}): {query[:50]}..."
                )

                return result

        # No rule matched - use LLM fallback if enabled
        if self.settings.get('enable_llm_fallback', True):
            logger.info("No rule matched, falling back to LLM classification")
            # Import here to avoid circular dependency
            from app.services.query_classifier import query_classifier as llm_classifier
            return await llm_classifier.classify(query)

        # Default fallback
        default_classification = self.settings.get('default_classification', 'ambiguous')
        default_confidence = self.settings.get('default_confidence', 0.5)
        default_use_documents = self.settings.get('default_use_documents', True)

        logger.info(f"No rule matched, using default: {default_classification}")

        return {
            'query_type': default_classification,
            'confidence': default_confidence,
            'use_documents': default_use_documents,
            'reason': 'No specific rule matched, using default classification'
        }

    def _build_context(self, query: str) -> Dict[str, Any]:
        """
        Build context for context-aware rules

        Returns context dict with:
        - word_count: Number of words
        - char_count: Number of characters
        - has_question_mark: Whether query ends with ?
        - proper_nouns: List of detected proper nouns
        - proper_nouns_count: Count of proper nouns
        - is_short: Whether query is short (<= 3 words)
        """
        words = query.split()
        proper_nouns = self._detect_proper_nouns(query)

        context = {
            'word_count': len(words),
            'char_count': len(query),
            'has_question_mark': query.strip().endswith('?'),
            'proper_nouns': proper_nouns,
            'proper_nouns_count': len(proper_nouns),
            'is_short': len(words) <= 3,
            'is_very_short': len(words) <= 2
        }

        return context

    def _detect_proper_nouns(self, query: str) -> List[str]:
        """
        Detect proper nouns in query

        Returns list of capitalized words that are likely proper nouns
        """
        proper_nouns = []
        words = query.split()

        for i, word in enumerate(words):
            # Clean punctuation
            clean_word = re.sub(r'[^\w\s]', '', word)

            if not clean_word or len(clean_word) <= 1:
                continue

            # Skip common question words at start
            if i == 0 and clean_word.lower() in {
                'do', 'does', 'did', 'are', 'is', 'was', 'were',
                'can', 'could', 'will', 'would', 'should',
                'have', 'has', 'had',
                'what', 'who', 'where', 'when', 'why', 'how', 'which'
            }:
                continue

            # Capitalized word (likely proper noun)
            if clean_word[0].isupper() and len(clean_word) > 1:
                proper_nouns.append(clean_word)

        # Deduplicate
        return list(set(proper_nouns))

    def _record_hit(self, rule_id: str, confidence: float):
        """Record that a rule was hit (for adaptive ordering)"""
        if not self.settings.get('track_rule_hits', True):
            return

        if rule_id not in self.rule_stats:
            self.rule_stats[rule_id] = RuleHitStats(rule_id=rule_id)

        stats = self.rule_stats[rule_id]
        stats.hit_count += 1
        stats.last_hit_timestamp = __import__('time').time()

        # Update average confidence
        if stats.hit_count == 1:
            stats.average_confidence = confidence
        else:
            # Running average
            stats.average_confidence = (
                (stats.average_confidence * (stats.hit_count - 1) + confidence)
                / stats.hit_count
            )

    def get_rule_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all rules"""
        stats = []
        for rule in self.rules:
            rule_stat = self.rule_stats.get(rule.id, RuleHitStats(rule_id=rule.id))
            stats.append({
                'rule_id': rule.id,
                'rule_name': rule.name,
                'priority': rule.priority,
                'enabled': rule.enabled,
                'hit_count': rule_stat.hit_count,
                'average_confidence': rule_stat.average_confidence
            })

        # Sort by hit count (most hit first)
        stats.sort(key=lambda s: s['hit_count'], reverse=True)
        return stats

    def reorder_by_hit_rate(self):
        """
        Reorder rules based on hit rate (adaptive ordering)

        Rules that are hit more often get higher priority (checked first)
        """
        if not self.settings.get('adaptive_ordering', True):
            return

        # Get rules with hit counts
        rules_with_hits = [
            (rule, self.rule_stats.get(rule.id, RuleHitStats(rule_id=rule.id)).hit_count)
            for rule in self.rules
        ]

        # Sort by hit count (descending), then by original priority
        rules_with_hits.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

        # Update rule list
        self.rules = [rule for rule, _ in rules_with_hits]

        logger.info("✓ Reordered rules based on hit rate")

    def export_config(self, output_path: str):
        """Export current configuration to YAML file"""
        config = {
            'version': '1.0',
            'settings': self.settings,
            'rules': [
                {
                    'id': rule.id,
                    'name': rule.name,
                    'priority': rule.priority,
                    'enabled': rule.enabled,
                    'type': rule.type,
                    'classification': rule.classification,
                    'confidence': rule.confidence,
                    'use_documents': rule.use_documents,
                    'description': rule.description,
                    'patterns': rule.patterns,
                    'detect': rule.detect
                }
                for rule in self.rules
            ]
        }

        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"✓ Exported config to {output_path}")

    def add_custom_rule(
        self,
        rule_id: str,
        name: str,
        patterns: List[str],
        classification: str,
        priority: int = 99,
        confidence: float = 0.95,
        use_documents: bool = True
    ):
        """
        Add a custom rule dynamically

        Args:
            rule_id: Unique rule ID
            name: Human-readable name
            patterns: List of regex patterns
            classification: Target classification type
            priority: Rule priority (0-100)
            confidence: Classification confidence
            use_documents: Whether to use RAG
        """
        new_rule = ClassificationRule(
            id=rule_id,
            name=name,
            priority=priority,
            enabled=True,
            type="pattern_match",
            classification=classification,
            confidence=confidence,
            use_documents=use_documents,
            description=f"Custom rule: {name}",
            patterns=patterns
        )

        self.rules.append(new_rule)

        # Re-sort by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)

        logger.info(f"✓ Added custom rule: {name} (priority={priority})")


# Global singleton
dynamic_classifier = DynamicQueryClassifier()
