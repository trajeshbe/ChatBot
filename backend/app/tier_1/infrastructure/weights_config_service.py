"""
Weights Configuration Service

Manages loading, updating, and validation of configurable weights
for multi-strategy RAG system.

Features:
- Load weights from YAML config file
- Update weights at runtime
- Reset to defaults
- Validation of weight values
- Thread-safe singleton pattern
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ==========================================
# PYDANTIC MODELS FOR VALIDATION
# ==========================================

class StrategyWeights(BaseModel):
    """Strategy base weights"""
    conversation_only: float = Field(1.0, ge=0.0, le=2.0)  # 🆕 Conversation-only mode (highest priority)
    rag_short_term: float = Field(0.30, ge=0.0, le=2.0)
    rag_hybrid: float = Field(0.25, ge=0.0, le=2.0)
    tool_navigation: float = Field(0.15, ge=0.0, le=2.0)
    tool_ocr: float = Field(0.10, ge=0.0, le=2.0)
    tool_docling: float = Field(0.15, ge=0.0, le=2.0)
    tool_web_scraping: float = Field(0.20, ge=0.0, le=2.0)
    rag_long_term: float = Field(0.30, ge=0.0, le=2.0)
    direct_llm: float = Field(0.05, ge=0.0, le=2.0)


class ScoringFormulaWeights(BaseModel):
    """Scoring formula component weights"""
    strategy_weight: float = Field(0.30, ge=0.0, le=1.0)
    confidence: float = Field(0.25, ge=0.0, le=1.0)
    source_quality_score: float = Field(0.25, ge=0.0, le=1.0)
    relevance_score: float = Field(0.15, ge=0.0, le=1.0)
    completeness_score: float = Field(0.05, ge=0.0, le=1.0)
    diversity_bonus: float = Field(0.10, ge=0.0, le=0.5)

    @validator('*', pre=True)
    def check_sum(cls, v, values):
        """Ensure weights sum to 1.0 (excluding diversity_bonus)"""
        if len(values) == 5:  # All non-bonus weights loaded
            total = sum([values.get(k, 0) for k in ['strategy_weight', 'confidence', 'source_quality_score', 'relevance_score', 'completeness_score']])
            if abs(total - 1.0) > 0.01:
                logger.warning(f"Scoring formula weights sum to {total:.2f}, expected 1.0")
        return v


class SourceQualityWeights(BaseModel):
    """Source quality weights"""
    short_term: float = Field(1.0, ge=0.0, le=1.5)
    long_term: float = Field(0.7, ge=0.0, le=1.5)
    general: float = Field(0.5, ge=0.0, le=1.5)
    scraped: float = Field(0.65, ge=0.0, le=1.5)
    ocr: float = Field(0.80, ge=0.0, le=1.5)


class ClassificationThresholds(BaseModel):
    """Classification confidence thresholds"""
    general_knowledge_skip: float = Field(0.75, ge=0.0, le=1.0)
    ai_personal_skip: float = Field(0.75, ge=0.0, le=1.0)
    ambiguous_use_rag: float = Field(0.50, ge=0.0, le=1.0)
    min_llm_classification_confidence: float = Field(0.60, ge=0.0, le=1.0)


class SimilarityThresholds(BaseModel):
    """Vector similarity thresholds"""
    default: float = Field(0.60, ge=0.0, le=1.0)
    proper_nouns: float = Field(0.50, ge=0.0, le=1.0)
    short_query: float = Field(0.55, ge=0.0, le=1.0)
    minimum: float = Field(0.45, ge=0.0, le=1.0)
    maximum: float = Field(0.75, ge=0.0, le=1.0)


class RerankingWeights(BaseModel):
    """Reranking weights"""
    semantic: float = Field(0.70, ge=0.0, le=1.0)
    keyword: float = Field(0.20, ge=0.0, le=1.0)
    recency: float = Field(0.10, ge=0.0, le=1.0)

    @validator('*', pre=True)
    def check_sum(cls, v, values):
        """Ensure weights sum to 1.0"""
        if len(values) == 2:  # All weights loaded
            total = sum(values.values()) + v
            if abs(total - 1.0) > 0.01:
                logger.warning(f"Reranking weights sum to {total:.2f}, expected 1.0")
        return v


class QueryPreprocessing(BaseModel):
    """Query preprocessing parameters"""
    max_length_for_expansion: int = Field(4, ge=1, le=20)
    min_query_length: int = Field(1, ge=1, le=10)
    max_query_length: int = Field(500, ge=10, le=5000)


class CacheConfig(BaseModel):
    """Cache configuration"""
    similarity_threshold: float = Field(0.95, ge=0.0, le=1.0)
    ttl_seconds: int = Field(3600, ge=60, le=86400)


class MultiToolWeights(BaseModel):
    """Multi-tool agent weights"""
    document_rag: float = Field(0.30, ge=0.0, le=2.0)
    navigation_agent: float = Field(0.20, ge=0.0, le=2.0)
    ocr_tool: float = Field(0.15, ge=0.0, le=2.0)
    web_scraping: float = Field(0.25, ge=0.0, le=2.0)
    docling: float = Field(0.10, ge=0.0, le=2.0)


class AnswerFusion(BaseModel):
    """Answer fusion weights"""
    best_answer_weight: float = Field(0.60, ge=0.0, le=1.0)
    second_best_weight: float = Field(0.30, ge=0.0, le=1.0)
    third_best_weight: float = Field(0.10, ge=0.0, le=1.0)

    @validator('*', pre=True)
    def check_sum(cls, v, values):
        """Ensure weights sum to 1.0"""
        if len(values) == 2:  # All weights loaded
            total = sum(values.values()) + v
            if abs(total - 1.0) > 0.01:
                logger.warning(f"Answer fusion weights sum to {total:.2f}, expected 1.0")
        return v


class RAGSettings(BaseModel):
    """Core RAG retrieval and processing parameters"""
    top_k: int = Field(5, ge=1, le=20)
    no_relevant_docs_threshold: float = Field(0.35, ge=0.0, le=1.0)
    chunk_size: int = Field(800, ge=100, le=2000)
    chunk_overlap: int = Field(150, ge=0, le=500)


class WeightsConfig(BaseModel):
    """Complete weights configuration"""
    strategy_weights: StrategyWeights
    scoring_formula_weights: ScoringFormulaWeights
    source_quality_weights: SourceQualityWeights
    classification_thresholds: ClassificationThresholds
    similarity_thresholds: SimilarityThresholds
    reranking_weights: RerankingWeights
    query_preprocessing: QueryPreprocessing
    cache: CacheConfig
    multi_tool_weights: MultiToolWeights
    answer_fusion: AnswerFusion
    rag_settings: RAGSettings


# ==========================================
# CONFIGURATION SERVICE
# ==========================================

class WeightsConfigService:
    """
    Singleton service for managing weights configuration

    Thread-safe loading and updating of weights from YAML config file.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize configuration service"""
        if self._initialized:
            return

        self.config_path = Path(__file__).parent.parent / "config" / "weights_config.yaml"
        self.config: Optional[WeightsConfig] = None
        self._load_config()
        self._initialized = True

        logger.info(f"✅ WeightsConfigService initialized from {self.config_path}")

    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config_dict = yaml.safe_load(f)

            # Remove metadata section (not part of Pydantic model)
            config_dict.pop('metadata', None)

            # Validate and load
            self.config = WeightsConfig(**config_dict)

            logger.info("📊 Weights configuration loaded successfully")

        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            # Load defaults
            self.config = WeightsConfig(
                strategy_weights=StrategyWeights(),
                scoring_formula_weights=ScoringFormulaWeights(),
                source_quality_weights=SourceQualityWeights(),
                classification_thresholds=ClassificationThresholds(),
                similarity_thresholds=SimilarityThresholds(),
                reranking_weights=RerankingWeights(),
                query_preprocessing=QueryPreprocessing(),
                cache=CacheConfig(),
                multi_tool_weights=MultiToolWeights(),
                answer_fusion=AnswerFusion(),
                rag_settings=RAGSettings()
            )
            logger.info("⚠️  Loaded default weights (config file missing)")

        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Load defaults as fallback
            self.config = WeightsConfig(
                strategy_weights=StrategyWeights(),
                scoring_formula_weights=ScoringFormulaWeights(),
                source_quality_weights=SourceQualityWeights(),
                classification_thresholds=ClassificationThresholds(),
                similarity_thresholds=SimilarityThresholds(),
                reranking_weights=RerankingWeights(),
                query_preprocessing=QueryPreprocessing(),
                cache=CacheConfig(),
                multi_tool_weights=MultiToolWeights(),
                answer_fusion=AnswerFusion(),
                rag_settings=RAGSettings()
            )
            logger.info("⚠️  Loaded default weights (config parsing error)")

    def get_config(self) -> WeightsConfig:
        """Get current configuration"""
        return self.config

    def get_strategy_weights(self) -> Dict[str, float]:
        """Get strategy weights as dictionary"""
        return self.config.strategy_weights.dict()

    def get_scoring_weights(self) -> Dict[str, float]:
        """Get scoring formula weights as dictionary"""
        return self.config.scoring_formula_weights.dict()

    def get_source_quality_weights(self) -> Dict[str, float]:
        """Get source quality weights as dictionary"""
        return self.config.source_quality_weights.dict()

    def get_classification_thresholds(self) -> Dict[str, float]:
        """Get classification thresholds as dictionary"""
        return self.config.classification_thresholds.dict()

    def get_similarity_thresholds(self) -> Dict[str, float]:
        """Get similarity thresholds as dictionary"""
        return self.config.similarity_thresholds.dict()

    def update_weights(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update weights with new values

        Args:
            updates: Dictionary with weight updates
                Format: {"strategy_weights": {"rag_short_term": 1.0, ...}, ...}

        Returns:
            Dictionary with update results
        """
        try:
            # Create updated config dict
            config_dict = self.config.dict()

            # Apply updates
            for section, values in updates.items():
                if section in config_dict and isinstance(values, dict):
                    config_dict[section].update(values)

            # Validate new configuration
            new_config = WeightsConfig(**config_dict)

            # If validation passes, update in memory
            with self._lock:
                self.config = new_config

            logger.info(f"✅ Weights updated: {updates}")

            return {
                "success": True,
                "message": "Weights updated successfully",
                "updated_sections": list(updates.keys())
            }

        except Exception as e:
            logger.error(f"Error updating weights: {e}")
            return {
                "success": False,
                "message": f"Failed to update weights: {str(e)}",
                "error": str(e)
            }

    def save_config(self) -> Dict[str, Any]:
        """
        Save current configuration to YAML file

        Returns:
            Dictionary with save results
        """
        try:
            with self._lock:
                config_dict = self.config.dict()

            # Add metadata
            config_dict['metadata'] = {
                'version': '1.0.0',
                'last_updated': '2025-11-24',
                'schema_version': '1',
                'description': 'Configurable weights for RAG system dynamic computation'
            }

            with open(self.config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

            logger.info(f"💾 Configuration saved to {self.config_path}")

            return {
                "success": True,
                "message": "Configuration saved successfully",
                "path": str(self.config_path)
            }

        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return {
                "success": False,
                "message": f"Failed to save configuration: {str(e)}",
                "error": str(e)
            }

    def reset_to_defaults(self) -> Dict[str, Any]:
        """
        Reset all weights to default values

        Returns:
            Dictionary with reset results
        """
        try:
            with self._lock:
                self.config = WeightsConfig(
                    strategy_weights=StrategyWeights(),
                    scoring_formula_weights=ScoringFormulaWeights(),
                    source_quality_weights=SourceQualityWeights(),
                    classification_thresholds=ClassificationThresholds(),
                    similarity_thresholds=SimilarityThresholds(),
                    reranking_weights=RerankingWeights(),
                    query_preprocessing=QueryPreprocessing(),
                    cache=CacheConfig(),
                    multi_tool_weights=MultiToolWeights(),
                    answer_fusion=AnswerFusion(),
                    rag_settings=RAGSettings()
                )

            logger.info("🔄 Weights reset to defaults")

            return {
                "success": True,
                "message": "Weights reset to defaults successfully"
            }

        except Exception as e:
            logger.error(f"Error resetting weights: {e}")
            return {
                "success": False,
                "message": f"Failed to reset weights: {str(e)}",
                "error": str(e)
            }

    def get_all_weights(self) -> Dict[str, Any]:
        """
        Get all weights as nested dictionary

        Returns:
            Complete weights configuration
        """
        return self.config.dict()


# ==========================================
# SINGLETON INSTANCE
# ==========================================

weights_config_service = WeightsConfigService()
