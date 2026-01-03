"""
Pydantic schemas for dynamic module configuration API.

Provides request/response models for the configuration management endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


# ============================================================================
# LLM Configuration
# ============================================================================

class LLMConfig(BaseModel):
    """LLM model configuration"""
    model: str = Field(..., description="LLM model name")
    temperature: float = Field(0.2, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(1000, ge=1, le=128000, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Top-p sampling")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")

    class Config:
        schema_extra = {
            "example": {
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "max_tokens": 1000,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
        }


class MultiLLMConfig(BaseModel):
    """Configuration for multiple LLM stages"""
    default: Optional[LLMConfig] = None
    # Allow arbitrary keys for different stages (e.g., 'profile_analyzer', 'query_processor')
    stages: Dict[str, LLMConfig] = Field(default_factory=dict)


# ============================================================================
# Prompt Configuration
# ============================================================================

class PromptConfig(BaseModel):
    """Prompt templates configuration"""
    system: Dict[str, str] = Field(default_factory=dict, description="System prompts")
    user: Dict[str, str] = Field(default_factory=dict, description="User prompt templates")

    class Config:
        schema_extra = {
            "example": {
                "system": {
                    "main": "You are a helpful AI assistant specialized in {domain}.",
                    "analyzer": "Analyze the following content and extract key information."
                },
                "user": {
                    "query_template": "User query: {query}\nContext: {context}"
                }
            }
        }


# ============================================================================
# Parameters Configuration
# ============================================================================

class ParametersConfig(BaseModel):
    """General parameters configuration"""
    # Flexible structure to accommodate various parameter types
    params: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "params": {
                    "batch_size": 10,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "cache_ttl": 3600
                }
            }
        }


# ============================================================================
# Thresholds Configuration
# ============================================================================

class ThresholdsConfig(BaseModel):
    """Confidence and quality thresholds"""
    thresholds: Dict[str, float] = Field(default_factory=dict)

    @validator('thresholds')
    def validate_thresholds(cls, v):
        """Ensure all threshold values are between 0 and 1"""
        for key, value in v.items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Threshold '{key}' must be between 0 and 1, got {value}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "thresholds": {
                    "min_confidence": 0.7,
                    "high_quality": 0.9,
                    "match_threshold": 0.8
                }
            }
        }


# ============================================================================
# Scoring Configuration
# ============================================================================

class ScoringConfig(BaseModel):
    """Scoring weights and factors"""
    weights: Dict[str, float] = Field(default_factory=dict, description="Scoring weights")
    factors: Optional[Dict[str, float]] = Field(default_factory=dict, description="Scoring factors")

    @validator('weights', 'factors')
    def validate_weights(cls, v):
        """Ensure all weights are between 0 and 1"""
        for key, value in v.items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Weight '{key}' must be between 0 and 1, got {value}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "weights": {
                    "semantic": 0.6,
                    "keyword": 0.4
                },
                "factors": {
                    "recency": 0.3,
                    "relevance": 0.7
                }
            }
        }


# ============================================================================
# Retrieval Configuration
# ============================================================================

class RetrievalConfig(BaseModel):
    """Vector search and retrieval configuration"""
    top_k: int = Field(10, ge=1, le=100, description="Number of results to retrieve")
    rerank_top_k: Optional[int] = Field(5, ge=1, le=50, description="Number of results after reranking")
    min_score: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity score")

    class Config:
        schema_extra = {
            "example": {
                "top_k": 10,
                "rerank_top_k": 5,
                "min_score": 0.7
            }
        }


# ============================================================================
# Features Configuration
# ============================================================================

class FeaturesConfig(BaseModel):
    """Feature flags configuration"""
    features: Dict[str, bool] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "features": {
                    "enable_reranking": True,
                    "enable_caching": True,
                    "enable_debug_logging": False
                }
            }
        }


# ============================================================================
# Complete Module Configuration
# ============================================================================

class ModuleConfigData(BaseModel):
    """Complete configuration data for a module"""
    llm: Optional[Dict[str, Any]] = Field(default_factory=dict, description="LLM configuration")
    prompts: Optional[PromptConfig] = Field(default=None, description="Prompt templates")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="General parameters")
    thresholds: Optional[Dict[str, float]] = Field(default_factory=dict, description="Confidence thresholds")
    scoring: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Scoring weights")
    retrieval: Optional[RetrievalConfig] = Field(default=None, description="Retrieval configuration")
    features: Optional[Dict[str, bool]] = Field(default_factory=dict, description="Feature flags")

    # Allow additional custom fields
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional custom configuration")

    class Config:
        schema_extra = {
            "example": {
                "llm": {
                    "default": {
                        "model": "gpt-4o-mini",
                        "temperature": 0.2,
                        "max_tokens": 1000
                    }
                },
                "prompts": {
                    "system": {
                        "main": "You are a helpful AI assistant."
                    },
                    "user": {
                        "query_template": "Query: {query}"
                    }
                },
                "thresholds": {
                    "min_confidence": 0.7
                },
                "scoring": {
                    "weights": {
                        "semantic": 0.6,
                        "keyword": 0.4
                    }
                },
                "features": {
                    "enable_caching": True
                }
            }
        }


# ============================================================================
# API Request/Response Models
# ============================================================================

class ModuleConfigurationCreate(BaseModel):
    """Request model for creating a new module configuration"""
    module_name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    module_type: str = Field(..., description="'tier2_domain_vertical' or 'tier3_customer_solution'")
    category: Optional[str] = None
    config: ModuleConfigData


class ModuleConfigurationUpdate(BaseModel):
    """Request model for updating module configuration"""
    updates: Dict[str, Any] = Field(..., description="Configuration updates (partial)")
    change_reason: Optional[str] = Field(None, description="Reason for the change")


class ModuleConfigurationResponse(BaseModel):
    """Response model for module configuration"""
    id: UUID
    module_name: str
    display_name: str
    description: Optional[str]
    module_type: str
    category: Optional[str]
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    current_version: int

    class Config:
        from_attributes = True


class ModuleConfigurationListItem(BaseModel):
    """Simplified model for listing module configurations"""
    module_name: str
    display_name: str
    module_type: str
    category: Optional[str]
    is_active: bool
    current_version: int

    class Config:
        from_attributes = True


class UserOverrideCreate(BaseModel):
    """Request model for creating user overrides"""
    overrides: Dict[str, Any] = Field(..., description="Configuration overrides")
    variant_name: Optional[str] = Field(None, description="A/B test variant name")
    experiment_id: Optional[UUID] = Field(None, description="Experiment ID for A/B testing")


class UserOverrideResponse(BaseModel):
    """Response model for user overrides"""
    id: UUID
    user_id: UUID
    module_name: str
    overrides: Dict[str, Any]
    variant_name: Optional[str]
    experiment_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ConfigVersionResponse(BaseModel):
    """Response model for configuration version"""
    id: UUID
    module_name: str
    version: int
    config: Dict[str, Any]
    changed_by: Optional[UUID]
    changed_at: datetime
    change_description: Optional[str]
    diff: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ConfigTemplateCreate(BaseModel):
    """Request model for creating configuration template"""
    template_name: str
    display_name: str
    description: Optional[str]
    template: Dict[str, Any]
    category: Optional[str]
    tags: Optional[List[str]] = []
    module_type: Optional[str]
    is_public: bool = True


class ConfigTemplateResponse(BaseModel):
    """Response model for configuration template"""
    id: UUID
    template_name: str
    display_name: str
    description: Optional[str]
    template: Dict[str, Any]
    category: Optional[str]
    tags: Optional[List[str]]
    module_type: Optional[str]
    created_at: datetime
    is_public: bool
    usage_count: int

    class Config:
        from_attributes = True


class ConfigValidationResponse(BaseModel):
    """Response model for configuration validation"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class MergedConfigResponse(BaseModel):
    """Response model for merged configuration (with overrides)"""
    module_name: str
    config: Dict[str, Any]
    has_user_overrides: bool = False
    override_fields: List[str] = []
    resolution_order: List[str] = ["global_defaults", "module_config", "user_overrides"]
