# Dynamic POC Configuration Architecture

**Date:** 2026-01-02
**Status:** 🎯 Architectural Design & Implementation Plan
**Purpose:** Enable UI-based configuration for all POCs/Customer Solutions

---

## Executive Summary

This document presents a comprehensive architecture for making all Customer Solutions (POCs) dynamically configurable through the UI, eliminating 143+ hardcoded values across Tier 2 and Tier 3 modules.

**Key Benefits:**
- ✅ **Zero-Code POC Deployment** - Configure new customers via UI in minutes
- ✅ **A/B Testing** - Test different prompts, models, and parameters
- ✅ **Customer Self-Service** - Allow customers to tune their own deployment
- ✅ **Faster Iteration** - No code changes or deployments required
- ✅ **Version Control** - Track configuration changes over time
- ✅ **Multi-Tenancy Ready** - Per-customer configurations with inheritance

**Audit Summary:**
- 143 hardcoded values identified
- 21 hardcoded LLM models
- 47 hardcoded prompts
- 28 hardcoded hyperparameters
- 14 hardcoded confidence thresholds
- 8 hardcoded regex patterns
- 25 other hardcoded values

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Configuration Hierarchy](#configuration-hierarchy)
3. [Database Schema](#database-schema)
4. [Backend API Design](#backend-api-design)
5. [Frontend UI Design](#frontend-ui-design)
6. [Configuration Service](#configuration-service)
7. [Migration Strategy](#migration-strategy)
8. [Implementation Plan](#implementation-plan)
9. [Code Examples](#code-examples)
10. [Security Considerations](#security-considerations)

---

## Architecture Overview

### Current State (Hardcoded)

```
┌─────────────────────────────────────┐
│   Frontend UI (Customer Solutions) │
│   - British Council                │
│   - CRU Mining                     │
│   - Grant Thornton                 │
│   - GT Motive                      │
│   - Solera                         │
│   - Construction Monitor           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Backend Services                  │
│   ┌───────────────────────────────┐│
│   │ HARDCODED VALUES:             ││
│   │ - Models: "gpt-4o-mini"       ││
│   │ - Prompts: "You are a..."     ││
│   │ - Temp: 0.0, 0.1, 0.2         ││
│   │ - Thresholds: 0.7, 0.8, 0.9   ││
│   └───────────────────────────────┘│
└─────────────────────────────────────┘
```

### Target State (Dynamic Configuration)

```
┌──────────────────────────────────────────────────────────────┐
│   Frontend UI - POC Configuration Management                 │
│   ┌────────────────────────────────────────────────────────┐│
│   │ 📝 Prompts Tab    🤖 Models Tab    ⚙️ Parameters Tab  ││
│   │ 🎯 Thresholds Tab 📊 Scoring Tab   🔍 Advanced Tab    ││
│   └────────────────────────────────────────────────────────┘│
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│   Configuration Service (Middleware)                         │
│   ┌────────────────────────────────────────────────────────┐│
│   │ 3-Level Hierarchy:                                     ││
│   │ 1. User-Specific Overrides (highest priority)         ││
│   │ 2. POC-Specific Configuration                         ││
│   │ 3. Global Defaults (fallback)                         ││
│   └────────────────────────────────────────────────────────┘│
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│   PostgreSQL Database                                         │
│   ┌────────────────┬───────────────────┬───────────────────┐│
│   │ poc_configs    │ config_versions   │ config_templates  ││
│   │ config_schemas │ config_overrides  │ audit_logs        ││
│   └────────────────┴───────────────────┴───────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## Configuration Hierarchy

### 3-Level Inheritance Model

```
┌─────────────────────────────────────────────────────────────┐
│ Level 1: Global Defaults (Base Configuration)               │
│ ----------------------------------------------------------- │
│ File: config/defaults/global_defaults.yaml                 │
│                                                             │
│ llm:                                                        │
│   default_model: "gpt-4o-mini"                             │
│   default_temperature: 0.2                                 │
│   default_max_tokens: 1000                                 │
│                                                             │
│ prompts:                                                    │
│   default_system: "You are a helpful AI assistant."       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Inherits & Overrides
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Level 2: POC-Specific Configuration                        │
│ ----------------------------------------------------------- │
│ Database: poc_configurations table                         │
│                                                             │
│ british_council:                                            │
│   llm:                                                      │
│     profile_analyzer:                                       │
│       model: "gpt-4o-mini"      ← Overrides global        │
│       temperature: 0.0          ← Overrides global        │
│       max_tokens: 500           ← Overrides global        │
│   prompts:                                                  │
│     profile_extraction: "Extract user profile..."          │
│   scoring:                                                  │
│     semantic_weight: 0.6                                    │
│     profile_weight: 0.4                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Inherits & Overrides
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Level 3: User-Specific Overrides (Highest Priority)        │
│ ----------------------------------------------------------- │
│ Database: poc_user_overrides table                         │
│                                                             │
│ user_id: "customer_abc"                                     │
│ poc_name: "british_council"                                 │
│ overrides:                                                  │
│   llm:                                                      │
│     profile_analyzer:                                       │
│       temperature: 0.1    ← Final override for this user   │
│   scoring:                                                  │
│     semantic_weight: 0.7  ← A/B test variant              │
└─────────────────────────────────────────────────────────────┘
```

**Resolution Order:**
1. Check user-specific overrides first
2. Fall back to POC-specific config
3. Fall back to global defaults
4. Fail with clear error if no config found

---

## Database Schema

### Core Tables

#### 1. `poc_configurations`
Stores base configuration for each POC.

```sql
CREATE TABLE poc_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    poc_name VARCHAR(100) NOT NULL UNIQUE,  -- 'british_council', 'cru', etc.
    display_name VARCHAR(255) NOT NULL,      -- 'British Council Course Recommendations'
    description TEXT,

    -- Configuration JSON (JSONB for querying)
    config JSONB NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,

    -- Version tracking
    current_version INTEGER DEFAULT 1,

    CONSTRAINT unique_poc_name UNIQUE(poc_name)
);

-- Indexes
CREATE INDEX idx_poc_configs_name ON poc_configurations(poc_name);
CREATE INDEX idx_poc_configs_active ON poc_configurations(is_active);
CREATE INDEX idx_poc_configs_config ON poc_configurations USING GIN(config);

-- Example config structure
{
  "llm": {
    "profile_analyzer": {
      "model": "gpt-4o-mini",
      "temperature": 0.0,
      "max_tokens": 500,
      "top_p": 1.0,
      "frequency_penalty": 0.0,
      "presence_penalty": 0.0
    },
    "answer_synthesis": {
      "model": "gpt-4o-mini",
      "temperature": 0.2,
      "max_tokens": 800
    }
  },
  "prompts": {
    "system": {
      "profile_extraction": "Extract a structured user profile from this text...",
      "course_recommendation": "Based on the user profile, recommend courses..."
    },
    "user": {
      "profile_query_template": "User background: {background}\nFind courses matching..."
    }
  },
  "scoring": {
    "weights": {
      "semantic": 0.6,
      "profile": 0.4
    },
    "profile_factors": {
      "education_match": 0.3,
      "format_match": 0.2,
      "availability_match": 0.2,
      "skill_intersection": 0.3
    },
    "thresholds": {
      "match_threshold": 0.8,
      "high_match": 0.9
    }
  },
  "retrieval": {
    "initial_top_k": 10,
    "rerank_top_k": 5,
    "final_recommendations": 5
  },
  "features": {
    "enable_reranking": true,
    "enable_profile_extraction": true,
    "enable_caching": true
  }
}
```

#### 2. `poc_user_overrides`
Per-user or per-customer configuration overrides.

```sql
CREATE TABLE poc_user_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    poc_name VARCHAR(100) NOT NULL,

    -- Override configuration (only contains overridden fields)
    overrides JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    -- A/B Testing
    variant_name VARCHAR(100),  -- 'control', 'variant_a', 'variant_b'
    experiment_id UUID,

    CONSTRAINT unique_user_poc UNIQUE(user_id, poc_name)
);

CREATE INDEX idx_user_overrides_user ON poc_user_overrides(user_id);
CREATE INDEX idx_user_overrides_poc ON poc_user_overrides(poc_name);
CREATE INDEX idx_user_overrides_variant ON poc_user_overrides(variant_name);
```

#### 3. `config_versions`
Version history for all configuration changes.

```sql
CREATE TABLE config_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    poc_name VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,

    -- Full configuration snapshot at this version
    config JSONB NOT NULL,

    -- Change tracking
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    change_description TEXT,

    -- Diff from previous version
    diff JSONB,  -- JSON patch format

    CONSTRAINT unique_poc_version UNIQUE(poc_name, version)
);

CREATE INDEX idx_versions_poc ON config_versions(poc_name);
CREATE INDEX idx_versions_version ON config_versions(version);
```

#### 4. `config_schemas`
JSON schemas for validating POC configurations.

```sql
CREATE TABLE config_schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_name VARCHAR(100) NOT NULL UNIQUE,
    schema_version VARCHAR(20) NOT NULL,

    -- JSON Schema definition
    schema JSONB NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Example schema
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "llm": {
      "type": "object",
      "properties": {
        "profile_analyzer": {
          "type": "object",
          "properties": {
            "model": {"type": "string", "enum": ["gpt-4o-mini", "gpt-4", "claude-3-sonnet"]},
            "temperature": {"type": "number", "minimum": 0, "maximum": 2},
            "max_tokens": {"type": "integer", "minimum": 1, "maximum": 128000}
          },
          "required": ["model", "temperature", "max_tokens"]
        }
      }
    }
  }
}
```

#### 5. `config_templates`
Reusable configuration templates for quick POC setup.

```sql
CREATE TABLE config_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Template configuration
    template JSONB NOT NULL,

    -- Categories
    category VARCHAR(100),  -- 'education', 'finance', 'automotive', 'insurance'
    tags TEXT[],

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_public BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0
);

CREATE INDEX idx_templates_category ON config_templates(category);
CREATE INDEX idx_templates_tags ON config_templates USING GIN(tags);
```

#### 6. `config_audit_logs`
Detailed audit trail for configuration changes.

```sql
CREATE TABLE config_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    poc_name VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- 'create', 'update', 'delete', 'override'

    -- Change details
    changed_field_path VARCHAR(255),  -- 'llm.profile_analyzer.temperature'
    old_value JSONB,
    new_value JSONB,

    -- User context
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,

    -- Additional context
    change_reason TEXT,
    metadata JSONB
);

CREATE INDEX idx_audit_poc ON config_audit_logs(poc_name);
CREATE INDEX idx_audit_user ON config_audit_logs(changed_by);
CREATE INDEX idx_audit_time ON config_audit_logs(changed_at);
```

---

## Backend API Design

### Configuration Service API Endpoints

```python
# Backend: app/api/routes/poc_config_routes.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/poc-config", tags=["POC Configuration"])

# ============================================================================
# Schemas
# ============================================================================

class LLMConfig(BaseModel):
    model: str
    temperature: float
    max_tokens: int
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0

class PromptConfig(BaseModel):
    system: Dict[str, str]
    user: Dict[str, str]

class POCConfiguration(BaseModel):
    poc_name: str
    display_name: str
    description: Optional[str] = None
    llm: Dict[str, LLMConfig]
    prompts: PromptConfig
    scoring: Optional[Dict[str, Any]] = None
    retrieval: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, bool]] = None

class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, Any]
    change_reason: Optional[str] = None

# ============================================================================
# Endpoints
# ============================================================================

@router.get("/pocs")
async def list_pocs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, str]]:
    """List all available POCs with basic info"""
    return await poc_config_service.list_pocs(db)

@router.get("/pocs/{poc_name}")
async def get_poc_config(
    poc_name: str,
    user_id: Optional[str] = None,
    include_overrides: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> POCConfiguration:
    """
    Get complete configuration for a POC.

    Resolution order:
    1. User-specific overrides (if user_id provided)
    2. POC-specific configuration
    3. Global defaults
    """
    return await poc_config_service.get_config(
        db=db,
        poc_name=poc_name,
        user_id=user_id or current_user.id,
        include_overrides=include_overrides
    )

@router.put("/pocs/{poc_name}")
async def update_poc_config(
    poc_name: str,
    request: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> POCConfiguration:
    """Update POC configuration (creates new version)"""
    return await poc_config_service.update_config(
        db=db,
        poc_name=poc_name,
        updates=request.updates,
        changed_by=current_user.id,
        change_reason=request.change_reason
    )

@router.post("/pocs/{poc_name}/overrides")
async def set_user_override(
    poc_name: str,
    overrides: Dict[str, Any],
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Set user-specific configuration overrides"""
    return await poc_config_service.set_override(
        db=db,
        poc_name=poc_name,
        user_id=user_id or current_user.id,
        overrides=overrides
    )

@router.delete("/pocs/{poc_name}/overrides")
async def clear_user_override(
    poc_name: str,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Clear user-specific overrides (revert to POC defaults)"""
    await poc_config_service.clear_override(
        db=db,
        poc_name=poc_name,
        user_id=user_id or current_user.id
    )
    return {"status": "success", "message": "Overrides cleared"}

@router.get("/pocs/{poc_name}/versions")
async def get_config_versions(
    poc_name: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get version history for POC configuration"""
    return await poc_config_service.get_versions(
        db=db,
        poc_name=poc_name,
        limit=limit
    )

@router.post("/pocs/{poc_name}/versions/{version}/restore")
async def restore_version(
    poc_name: str,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> POCConfiguration:
    """Restore a previous configuration version"""
    return await poc_config_service.restore_version(
        db=db,
        poc_name=poc_name,
        version=version,
        changed_by=current_user.id
    )

@router.get("/templates")
async def list_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List available configuration templates"""
    return await poc_config_service.list_templates(
        db=db,
        category=category
    )

@router.post("/pocs/{poc_name}/from-template")
async def create_from_template(
    poc_name: str,
    template_name: str,
    overrides: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> POCConfiguration:
    """Create new POC configuration from template"""
    return await poc_config_service.create_from_template(
        db=db,
        poc_name=poc_name,
        template_name=template_name,
        overrides=overrides,
        created_by=current_user.id
    )

@router.get("/pocs/{poc_name}/schema")
async def get_config_schema(
    poc_name: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get JSON schema for validating POC configuration"""
    return await poc_config_service.get_schema(
        db=db,
        poc_name=poc_name
    )

@router.post("/pocs/{poc_name}/validate")
async def validate_config(
    poc_name: str,
    config: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Validate configuration against schema"""
    is_valid, errors = await poc_config_service.validate_config(
        db=db,
        poc_name=poc_name,
        config=config
    )
    return {
        "valid": is_valid,
        "errors": errors if not is_valid else []
    }
```

---

## Frontend UI Design

### POC Configuration Management UI

#### 1. Main Configuration Page

```
┌──────────────────────────────────────────────────────────────┐
│ POC Configuration: British Council Course Recommendations    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Tabs: [ 📝 Prompts ] [ 🤖 Models ] [ ⚙️ Parameters ]      │
│        [ 🎯 Thresholds ] [ 📊 Scoring ] [ 🔍 Advanced ]     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📝 PROMPTS TAB                                             │
│  ──────────────                                             │
│                                                              │
│  System Prompts:                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Profile Extraction Prompt:                             │ │
│  │ ┌────────────────────────────────────────────────────┐ │ │
│  │ │ Extract a structured user profile from this text...││ │
│  │ │                                                     ││ │
│  │ │ Focus on:                                          ││ │
│  │ │ - Education level and background                  ││ │
│  │ │ - Preferred learning format (online/offline)      ││ │
│  │ │ - Time availability                               ││ │
│  │ │ - Subject interests and skills                    ││ │
│  │ └────────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │ [Edit] [Preview] [Reset to Default] [Save Changes]    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  User Prompt Templates:                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Course Recommendation Template:                        │ │
│  │ ┌────────────────────────────────────────────────────┐ │ │
│  │ │ User Profile: {profile_summary}                    ││ │
│  │ │                                                     ││ │
│  │ │ Find courses that match:                           ││ │
│  │ │ - Education level: {education_level}               ││ │
│  │ │ - Format preference: {format_preference}           ││ │
│  │ │ - Skills to develop: {skills}                      ││ │
│  │ └────────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │ [Edit] [Test with Sample] [Save]                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  💡 Tip: Use {variable_name} for dynamic content            │
│  📊 Last updated: 2026-01-02 by admin@example.com           │
│  🔄 Version: 3 [View History]                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 2. Models Tab

```
┌──────────────────────────────────────────────────────────────┐
│ 🤖 MODELS TAB                                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  LLM Configuration:                                         │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Profile Analyzer:                                      │ │
│  │                                                         │ │
│  │  Model:                                                 │ │
│  │  ┌─────────────────────────────────────┐              │ │
│  │  │ ▼ gpt-4o-mini                      │ [Test Model] │ │
│  │  └─────────────────────────────────────┘              │ │
│  │  Options: gpt-4o-mini, gpt-4, claude-3-opus,          │ │
│  │          claude-3-sonnet, mistral-large, llama3.1    │ │
│  │                                                         │ │
│  │  Provider:                                              │ │
│  │  ◉ OpenAI  ○ Anthropic  ○ Ollama  ○ Auto-Select       │ │
│  │                                                         │ │
│  │  Fallback Chain:                                        │ │
│  │  1. gpt-4o-mini      [↑] [↓] [Remove]                 │ │
│  │  2. gpt-3.5-turbo    [↑] [↓] [Remove]                 │ │
│  │  [+ Add Fallback Model]                                │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Answer Synthesis:                                      │ │
│  │                                                         │ │
│  │  Model: ┌─────────────────────┐                        │ │
│  │        │ ▼ gpt-4o-mini       │                        │ │
│  │         └─────────────────────┘                        │ │
│  │                                                         │ │
│  │  Provider: ◉ OpenAI  ○ Anthropic  ○ Ollama            │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Save Changes] [Reset to Defaults]                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 3. Parameters Tab

```
┌──────────────────────────────────────────────────────────────┐
│ ⚙️ PARAMETERS TAB                                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Generation Parameters:                                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Profile Analyzer:                                      │ │
│  │                                                         │ │
│  │  Temperature:                                           │ │
│  │  ├──────●─────────────────────┤  0.0                   │ │
│  │  0.0                        2.0                        │ │
│  │  💡 Lower = more deterministic, Higher = more creative │ │
│  │                                                         │ │
│  │  Max Tokens:                                            │ │
│  │  ┌──────────┐                                          │ │
│  │  │ 500      │ tokens                                   │ │
│  │  └──────────┘                                          │ │
│  │  Range: 1 - 128000                                     │ │
│  │                                                         │ │
│  │  Top P:                                                 │ │
│  │  ├───────────●──────────┤  1.0                         │ │
│  │  0.0                  1.0                              │ │
│  │                                                         │ │
│  │  Frequency Penalty:                                     │ │
│  │  ├──●────────────────────┤  0.0                        │ │
│  │  -2.0                  2.0                             │ │
│  │                                                         │ │
│  │  Presence Penalty:                                      │ │
│  │  ├──●────────────────────┤  0.0                        │ │
│  │  -2.0                  2.0                             │ │
│  │                                                         │ │
│  │  [Advanced Options ▼]                                  │ │
│  │    ☐ Stop Sequences                                    │ │
│  │    ☐ Logit Bias                                        │ │
│  │    ☐ Seed (for reproducibility)                       │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Save Changes] [Test with Sample Query] [Reset Defaults]   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 4. Thresholds Tab

```
┌──────────────────────────────────────────────────────────────┐
│ 🎯 THRESHOLDS TAB                                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Confidence Thresholds:                                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Match Quality:                                         │ │
│  │                                                         │ │
│  │  High Match Threshold:                                  │ │
│  │  ├──────────────────────●──┤  0.9                      │ │
│  │  0.0                     1.0                           │ │
│  │  💡 Courses above this score are "highly recommended"  │ │
│  │                                                         │ │
│  │  Good Match Threshold:                                  │ │
│  │  ├─────────────────●────────┤  0.8                     │ │
│  │  0.0                     1.0                           │ │
│  │  💡 Courses above this score are "recommended"         │ │
│  │                                                         │ │
│  │  Minimum Match Threshold:                               │ │
│  │  ├──────────────●───────────┤  0.6                     │ │
│  │  0.0                     1.0                           │ │
│  │  💡 Courses below this score are filtered out          │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Retrieval Thresholds:                                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Initial Retrieval Top K: ┌───┐                         │ │
│  │                         │10 │ results                  │ │
│  │                          └───┘                         │ │
│  │                                                         │ │
│  │ Reranker Top K:         ┌───┐                          │ │
│  │                         │ 5 │ results                  │ │
│  │                          └───┘                         │ │
│  │                                                         │ │
│  │ Final Recommendations:  ┌───┐                          │ │
│  │                         │ 5 │ courses                  │ │
│  │                          └───┘                         │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Save Changes] [Run Test Query]                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 5. Scoring Tab

```
┌──────────────────────────────────────────────────────────────┐
│ 📊 SCORING TAB                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Scoring Weights:                                           │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Overall Score Composition:                             │ │
│  │                                                         │ │
│  │  Semantic Similarity:                                   │ │
│  │  ├───────────●──────────┤  0.6 (60%)                   │ │
│  │  0.0                  1.0                              │ │
│  │                                                         │ │
│  │  Profile Match:                                         │ │
│  │  ├──────●──────────────┤  0.4 (40%)                    │ │
│  │  0.0                  1.0                              │ │
│  │                                                         │ │
│  │  Total: 1.0 ✓                                          │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Profile Scoring Factors:                               │ │
│  │                                                         │ │
│  │  Education Match:                                       │ │
│  │  ├──────────●──────────┤  0.3 (30%)                    │ │
│  │                                                         │ │
│  │  Format Match:                                          │ │
│  │  ├──────●──────────────┤  0.2 (20%)                    │ │
│  │                                                         │ │
│  │  Availability Match:                                    │ │
│  │  ├──────●──────────────┤  0.2 (20%)                    │ │
│  │                                                         │ │
│  │  Skill Intersection:                                    │ │
│  │  ├──────────●──────────┤  0.3 (30%)                    │ │
│  │                                                         │ │
│  │  Total: 1.0 ✓                                          │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  💡 Adjust weights to prioritize different factors          │
│  📊 [Visualize Score Distribution]                          │
│  [Save Changes] [Reset to Defaults]                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 6. Advanced Tab

```
┌──────────────────────────────────────────────────────────────┐
│ 🔍 ADVANCED TAB                                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Feature Flags:                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ☑ Enable Reranking                                     │ │
│  │ ☑ Enable Profile Extraction                            │ │
│  │ ☑ Enable Semantic Caching                              │ │
│  │ ☐ Enable A/B Testing                                   │ │
│  │ ☐ Enable Debug Logging                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Regex Patterns:                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Custom Extraction Patterns:                            │ │
│  │ ┌────────────────────────────────────────────────────┐ │ │
│  │ │ Pattern Name: course_code                          ││ │
│  │ │ Regex: \b[A-Z]{3}\d{4}\b                          ││ │
│  │ │ Description: Extract course codes like ABC1234    ││ │
│  │ │ [Test Pattern] [Save] [Delete]                    ││ │
│  │ └────────────────────────────────────────────────────┘ │ │
│  │ [+ Add New Pattern]                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Cache Configuration:                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Embedding Cache TTL: ┌──────┐ seconds                 │ │
│  │                      │ 3600 │                         │ │
│  │                      └──────┘                         │ │
│  │                                                         │ │
│  │ Query Cache TTL:     ┌──────┐ seconds                 │ │
│  │                      │ 1800 │                         │ │
│  │                      └──────┘                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Version Control:                                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Current Version: 3                                     │ │
│  │ Last Updated: 2026-01-02 14:23:45                      │ │
│  │ Updated By: admin@example.com                          │ │
│  │                                                         │ │
│  │ [View Version History] [Restore Previous Version]     │ │
│  │ [Export Configuration] [Import Configuration]         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Save All Changes]                                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Frontend Components (TypeScript/React)

```typescript
// frontend/src/components/POCConfigManager.tsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface POCConfigManagerProps {
  pocName: string;
  userId?: string;
}

export const POCConfigManager: React.FC<POCConfigManagerProps> = ({ pocName, userId }) => {
  const [config, setConfig] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<string>('prompts');
  const [hasChanges, setHasChanges] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConfig();
  }, [pocName, userId]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/v1/poc-config/pocs/${pocName}`, {
        params: { user_id: userId }
      });
      setConfig(response.data);
    } catch (error) {
      console.error('Failed to load config:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveChanges = async () => {
    try {
      await axios.put(`/api/v1/poc-config/pocs/${pocName}`, {
        updates: config,
        change_reason: 'Updated via UI'
      });
      setHasChanges(false);
      alert('Configuration saved successfully!');
    } catch (error) {
      console.error('Failed to save config:', error);
      alert('Failed to save configuration');
    }
  };

  const updateConfig = (path: string, value: any) => {
    setConfig((prev: any) => {
      const newConfig = { ...prev };
      // Deep set using path (e.g., 'llm.profile_analyzer.temperature')
      const keys = path.split('.');
      let current = newConfig;
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      setHasChanges(true);
      return newConfig;
    });
  };

  if (loading) {
    return <div>Loading configuration...</div>;
  }

  return (
    <div className="poc-config-manager">
      <div className="config-header">
        <h1>POC Configuration: {config?.display_name}</h1>
        {hasChanges && (
          <button onClick={saveChanges} className="save-btn">
            Save Changes
          </button>
        )}
      </div>

      <div className="config-tabs">
        {['prompts', 'models', 'parameters', 'thresholds', 'scoring', 'advanced'].map(tab => (
          <button
            key={tab}
            className={activeTab === tab ? 'active' : ''}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <div className="config-content">
        {activeTab === 'prompts' && (
          <PromptsTab config={config} updateConfig={updateConfig} />
        )}
        {activeTab === 'models' && (
          <ModelsTab config={config} updateConfig={updateConfig} />
        )}
        {activeTab === 'parameters' && (
          <ParametersTab config={config} updateConfig={updateConfig} />
        )}
        {activeTab === 'thresholds' && (
          <ThresholdsTab config={config} updateConfig={updateConfig} />
        )}
        {activeTab === 'scoring' && (
          <ScoringTab config={config} updateConfig={updateConfig} />
        )}
        {activeTab === 'advanced' && (
          <AdvancedTab config={config} updateConfig={updateConfig} />
        )}
      </div>
    </div>
  );
};
```

---

## Configuration Service

### Backend Service Implementation

```python
# Backend: app/services/poc_config_service.py

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
import json
from jsonschema import validate, ValidationError
from deepdiff import DeepDiff

class POCConfigService:
    """Service for managing POC configurations with 3-level hierarchy"""

    def __init__(self):
        self.cache = {}  # Simple in-memory cache

    async def get_config(
        self,
        db: Session,
        poc_name: str,
        user_id: Optional[str] = None,
        include_overrides: bool = True
    ) -> Dict[str, Any]:
        """
        Get complete configuration with 3-level resolution:
        1. User-specific overrides (if user_id provided)
        2. POC-specific configuration
        3. Global defaults
        """
        # Start with global defaults
        config = await self._get_global_defaults(db)

        # Merge POC-specific config
        poc_config = await self._get_poc_config(db, poc_name)
        if poc_config:
            config = self._merge_configs(config, poc_config)

        # Merge user-specific overrides
        if include_overrides and user_id:
            user_overrides = await self._get_user_overrides(db, poc_name, user_id)
            if user_overrides:
                config = self._merge_configs(config, user_overrides)

        return config

    async def update_config(
        self,
        db: Session,
        poc_name: str,
        updates: Dict[str, Any],
        changed_by: str,
        change_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update POC configuration and create new version"""
        # Get current config
        current_config = await self._get_poc_config(db, poc_name)

        # Merge updates
        new_config = self._merge_configs(current_config, updates)

        # Validate against schema
        schema = await self.get_schema(db, poc_name)
        try:
            validate(instance=new_config, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e.message}")

        # Calculate diff
        diff = DeepDiff(current_config, new_config)

        # Get current version
        current_version = db.execute(
            select(POCConfiguration.current_version)
            .where(POCConfiguration.poc_name == poc_name)
        ).scalar()

        new_version = (current_version or 0) + 1

        # Create version record
        version_record = ConfigVersion(
            poc_name=poc_name,
            version=new_version,
            config=new_config,
            changed_by=changed_by,
            change_description=change_reason,
            diff=json.loads(diff.to_json())
        )
        db.add(version_record)

        # Update current config
        db.execute(
            update(POCConfiguration)
            .where(POCConfiguration.poc_name == poc_name)
            .values(
                config=new_config,
                current_version=new_version,
                updated_at=datetime.utcnow()
            )
        )

        # Create audit log
        await self._create_audit_log(
            db=db,
            poc_name=poc_name,
            action='update',
            changed_by=changed_by,
            old_value=current_config,
            new_value=new_config
        )

        db.commit()

        # Invalidate cache
        self._invalidate_cache(poc_name)

        return new_config

    async def set_override(
        self,
        db: Session,
        poc_name: str,
        user_id: str,
        overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set user-specific configuration overrides"""
        # Check if override exists
        existing = db.execute(
            select(POCUserOverride)
            .where(
                POCUserOverride.user_id == user_id,
                POCUserOverride.poc_name == poc_name
            )
        ).scalar_one_or_none()

        if existing:
            # Update existing override
            existing.overrides = overrides
            existing.updated_at = datetime.utcnow()
        else:
            # Create new override
            override = POCUserOverride(
                user_id=user_id,
                poc_name=poc_name,
                overrides=overrides
            )
            db.add(override)

        db.commit()
        return overrides

    async def clear_override(
        self,
        db: Session,
        poc_name: str,
        user_id: str
    ) -> bool:
        """Clear user-specific overrides"""
        db.execute(
            delete(POCUserOverride)
            .where(
                POCUserOverride.user_id == user_id,
                POCUserOverride.poc_name == poc_name
            )
        )
        db.commit()
        return True

    def _merge_configs(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two configurations (override wins)"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    async def _get_global_defaults(self, db: Session) -> Dict[str, Any]:
        """Load global default configuration"""
        # In production, load from YAML file or database
        return {
            "llm": {
                "default_model": "gpt-4o-mini",
                "default_temperature": 0.2,
                "default_max_tokens": 1000
            },
            "prompts": {
                "system": {
                    "default": "You are a helpful AI assistant."
                }
            }
        }

    async def _get_poc_config(
        self,
        db: Session,
        poc_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get POC-specific configuration"""
        result = db.execute(
            select(POCConfiguration.config)
            .where(POCConfiguration.poc_name == poc_name)
        ).scalar_one_or_none()
        return result

    async def _get_user_overrides(
        self,
        db: Session,
        poc_name: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user-specific overrides"""
        result = db.execute(
            select(POCUserOverride.overrides)
            .where(
                POCUserOverride.user_id == user_id,
                POCUserOverride.poc_name == poc_name,
                POCUserOverride.is_active == True
            )
        ).scalar_one_or_none()
        return result

    def _invalidate_cache(self, poc_name: str):
        """Invalidate configuration cache"""
        if poc_name in self.cache:
            del self.cache[poc_name]

# Global instance
poc_config_service = POCConfigService()
```

---

## Migration Strategy

### Phase 1: Setup (Week 1)

**Goal:** Create infrastructure for configuration management

1. **Database Setup**
   ```bash
   # Create migration
   cd backend
   alembic revision -m "add_poc_configuration_tables"
   ```

   - Create all 6 tables (poc_configurations, poc_user_overrides, config_versions, etc.)
   - Add indexes
   - Seed with default configurations

2. **Backend Service**
   - Create `POCConfigService`
   - Create API routes
   - Add configuration schema validation

3. **Testing**
   - Unit tests for configuration merging
   - Integration tests for API endpoints

### Phase 2: British Council Migration (Week 2)

**Goal:** Migrate one POC as proof of concept

1. **Extract Current Configuration**
   ```python
   # Extract hardcoded values from british_council_service.py
   config = {
       "llm": {
           "profile_analyzer": {
               "model": "gpt-4o-mini",
               "temperature": 0.0,
               "max_tokens": 500
           }
       },
       # ... rest of config
   }
   ```

2. **Create Database Record**
   ```sql
   INSERT INTO poc_configurations (poc_name, display_name, config)
   VALUES (
       'british_council',
       'British Council Course Recommendations',
       '{"llm": {...}, "prompts": {...}, "scoring": {...}}'::jsonb
   );
   ```

3. **Refactor Service**
   ```python
   # Before
   response = await self.llm.generate_response(
       prompt,
       model="gpt-4o-mini",  # Hardcoded
       temperature=0.0       # Hardcoded
   )

   # After
   config = await poc_config_service.get_config(
       db=db,
       poc_name="british_council",
       user_id=user_id
   )
   response = await self.llm.generate_response(
       prompt,
       model=config['llm']['profile_analyzer']['model'],
       temperature=config['llm']['profile_analyzer']['temperature']
   )
   ```

4. **Testing**
   - Verify same behavior with config
   - Test config updates
   - Test user overrides

### Phase 3: Remaining POCs (Weeks 3-5)

**Goal:** Migrate all 5 remaining POCs

- Week 3: CRU + GT Motive
- Week 4: Grant Thornton + Solera
- Week 5: Construction Monitor + Tier 2 services

**Parallel Work:**
- Frontend UI development
- Documentation
- Testing

### Phase 4: Frontend UI (Week 6)

**Goal:** Build configuration management UI

1. **Core Components**
   - POCConfigManager (main container)
   - PromptsTab
   - ModelsTab
   - ParametersTab
   - ThresholdsTab
   - ScoringTab
   - AdvancedTab

2. **Features**
   - Real-time validation
   - Preview/test functionality
   - Version history viewer
   - Export/import configs

3. **Integration**
   - Add config buttons to each POC UI
   - Test end-to-end workflow

### Phase 5: Advanced Features (Week 7+)

1. **A/B Testing Framework**
   - Variant management
   - Traffic splitting
   - Metrics comparison

2. **Template Library**
   - Industry-specific templates
   - Best practice configs
   - Community sharing

3. **Monitoring**
   - Config change notifications
   - Performance impact tracking
   - Rollback automation

---

## Code Examples

### Example 1: Refactoring British Council Service

**Before (Hardcoded):**

```python
# backend/app/tier_3/customer_solutions/british_council_service.py

class ProfileAnalyzer:
    async def analyze_profile(self, text: str) -> Dict[str, Any]:
        prompt = """Extract a structured user profile from this text.

        Focus on:
        - Education level and background
        - Preferred learning format (online/offline)
        - Time availability
        - Subject interests and skills

        User text: {text}
        """

        response = await llm_service.generate_response(
            prompt.format(text=text),
            model="gpt-4o-mini",      # HARDCODED
            temperature=0.0,           # HARDCODED
            max_tokens=500             # HARDCODED
        )

        return json.loads(response)

class BritishCouncilService:
    async def recommend_courses(
        self,
        query: str,
        user_profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # Hardcoded weights
        semantic_weight = 0.6      # HARDCODED
        profile_weight = 0.4       # HARDCODED

        # Hardcoded thresholds
        match_threshold = 0.8      # HARDCODED

        # Hardcoded retrieval params
        initial_top_k = 10         # HARDCODED
        rerank_top_k = 5           # HARDCODED
        final_count = 5            # HARDCODED

        # ... rest of logic
```

**After (Dynamic Configuration):**

```python
# backend/app/tier_3/customer_solutions/british_council_service.py

from app.services.poc_config_service import poc_config_service

class ProfileAnalyzer:
    def __init__(self, db: Session, user_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.config = None

    async def _load_config(self):
        """Load configuration with user overrides"""
        if not self.config:
            self.config = await poc_config_service.get_config(
                db=self.db,
                poc_name="british_council",
                user_id=self.user_id
            )

    async def analyze_profile(self, text: str) -> Dict[str, Any]:
        await self._load_config()

        # Get prompt from config
        prompt_template = self.config['prompts']['system']['profile_extraction']
        prompt = prompt_template.format(text=text)

        # Get LLM settings from config
        llm_config = self.config['llm']['profile_analyzer']

        response = await llm_service.generate_response(
            prompt,
            model=llm_config['model'],               # FROM CONFIG
            temperature=llm_config['temperature'],   # FROM CONFIG
            max_tokens=llm_config['max_tokens']      # FROM CONFIG
        )

        return json.loads(response)

class BritishCouncilService:
    def __init__(self, db: Session, user_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.config = None

    async def _load_config(self):
        """Load configuration with user overrides"""
        if not self.config:
            self.config = await poc_config_service.get_config(
                db=self.db,
                poc_name="british_council",
                user_id=self.user_id
            )

    async def recommend_courses(
        self,
        query: str,
        user_profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        await self._load_config()

        # Get all values from config
        scoring = self.config['scoring']
        semantic_weight = scoring['weights']['semantic']      # FROM CONFIG
        profile_weight = scoring['weights']['profile']        # FROM CONFIG
        match_threshold = scoring['thresholds']['match_threshold']  # FROM CONFIG

        retrieval = self.config['retrieval']
        initial_top_k = retrieval['initial_top_k']            # FROM CONFIG
        rerank_top_k = retrieval['rerank_top_k']              # FROM CONFIG
        final_count = retrieval['final_recommendations']      # FROM CONFIG

        # ... rest of logic uses config values
```

### Example 2: Frontend Configuration UI

```typescript
// frontend/src/components/BritishCouncilConfig.tsx

import React, { useState, useEffect } from 'react';
import { POCConfigManager } from './POCConfigManager';
import axios from 'axios';

export const BritishCouncilConfig: React.FC = () => {
  const [showConfig, setShowConfig] = useState(false);

  return (
    <div className="british-council-page">
      <div className="page-header">
        <h1>British Council Course Recommendations</h1>
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="config-btn"
        >
          ⚙️ Configure POC
        </button>
      </div>

      {showConfig && (
        <POCConfigManager
          pocName="british_council"
          userId={currentUser.id}
        />
      )}

      <div className="main-content">
        {/* Existing British Council UI */}
      </div>
    </div>
  );
};
```

---

## Security Considerations

### 1. Access Control

```python
# Only admins can modify global/POC configurations
@router.put("/pocs/{poc_name}")
@require_role("admin")  # Decorator
async def update_poc_config(...)

# Users can only modify their own overrides
@router.post("/pocs/{poc_name}/overrides")
async def set_user_override(
    poc_name: str,
    overrides: Dict[str, Any],
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Ensure users can only override their own config
    if user_id and user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "Cannot modify other users' overrides")
```

### 2. Input Validation

```python
# Validate all config updates against JSON schema
async def validate_config(config: Dict[str, Any], schema: Dict[str, Any]):
    try:
        validate(instance=config, schema=schema)
    except ValidationError as e:
        raise HTTPException(400, f"Invalid configuration: {e.message}")

# Sanitize prompts (prevent injection)
def sanitize_prompt(prompt: str) -> str:
    # Remove dangerous patterns
    dangerous_patterns = ['<script>', 'eval(', 'exec(']
    for pattern in dangerous_patterns:
        if pattern in prompt.lower():
            raise ValueError(f"Dangerous pattern detected: {pattern}")
    return prompt
```

### 3. Audit Logging

```python
# Log all configuration changes
async def _create_audit_log(
    db: Session,
    poc_name: str,
    action: str,
    changed_by: str,
    old_value: Any,
    new_value: Any
):
    audit_log = ConfigAuditLog(
        poc_name=poc_name,
        action=action,
        changed_by=changed_by,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent')
    )
    db.add(audit_log)
```

### 4. Rate Limiting

```python
# Prevent abuse of config updates
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.put("/pocs/{poc_name}")
@limiter.limit("10/minute")  # Max 10 updates per minute
async def update_poc_config(...)
```

---

## Implementation Plan

### Timeline: 7 Weeks

#### Week 1: Infrastructure Setup
- **Database Schema**
  - Create all 6 tables
  - Add indexes
  - Write migration scripts
- **Backend Service**
  - Implement POCConfigService
  - Add configuration merging logic
  - Add validation
- **API Routes**
  - Create all REST endpoints
  - Add authentication/authorization
  - Write API tests

#### Week 2: British Council Migration (PoC)
- **Extract Configuration**
  - Audit british_council_service.py
  - Create config JSON
  - Create JSON schema
- **Refactor Service**
  - Replace hardcoded values
  - Add config loading
  - Test functionality
- **Seed Database**
  - Insert British Council config
  - Create default template

#### Week 3: CRU + GT Motive Migration
- **CRU Mining**
  - Extract config (prompts, LLM settings, retrieval params)
  - Refactor service
  - Test multi-pipeline routing
- **GT Motive**
  - Extract config (regex patterns, prompts, thresholds)
  - Refactor service
  - Test part code extraction

#### Week 4: Grant Thornton + Solera Migration
- **Grant Thornton**
  - Extract config (simple query processing)
  - Refactor service
  - Test financial extraction
- **Solera**
  - Extract config (VIN patterns, damage assessment)
  - Refactor service
  - Test claims processing

#### Week 5: Construction Monitor + Tier 2
- **Construction Monitor**
  - Extract config (entity types, relation types, prompts)
  - Refactor service
  - Test entity/relation extraction
- **Tier 2 Services**
  - Migrate LLM service prompts
  - Migrate Vision service prompts
  - Migrate OCR service thresholds

#### Week 6: Frontend UI Development
- **Core Components**
  - POCConfigManager (main container)
  - PromptsTab (text editors)
  - ModelsTab (dropdowns)
  - ParametersTab (sliders)
- **Integration**
  - Add config buttons to all 6 POC UIs
  - Connect to backend API
  - Test end-to-end workflow

#### Week 7: Testing & Documentation
- **Testing**
  - E2E tests for all 6 POCs
  - A/B testing framework
  - Performance testing
- **Documentation**
  - User guide for config management
  - Admin guide for templates
  - Developer guide for adding new POCs

---

## Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Configuration Coverage** | 100% of hardcoded values moved to config | Count hardcoded values remaining |
| **API Response Time** | < 100ms for config retrieval | Monitor API latency |
| **Config Update Success Rate** | > 99% | Track update failures |
| **Zero-Downtime Deployments** | 100% of config changes | No restarts required for config updates |

### Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **POC Deployment Time** | < 1 hour (from days) | Time to configure new customer |
| **Customer Self-Service** | 50% of config changes by customers | Track who makes changes |
| **A/B Test Velocity** | 10+ experiments per month | Count active experiments |
| **Support Ticket Reduction** | 30% reduction | Track config-related tickets |

---

## Appendix A: Configuration Schema Examples

### British Council Full Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "British Council POC Configuration",
  "type": "object",
  "properties": {
    "llm": {
      "type": "object",
      "properties": {
        "profile_analyzer": {
          "type": "object",
          "properties": {
            "model": {
              "type": "string",
              "enum": ["gpt-4o-mini", "gpt-4", "gpt-4-turbo", "claude-3-sonnet", "claude-3-opus"],
              "default": "gpt-4o-mini"
            },
            "temperature": {
              "type": "number",
              "minimum": 0,
              "maximum": 2,
              "default": 0.0
            },
            "max_tokens": {
              "type": "integer",
              "minimum": 1,
              "maximum": 128000,
              "default": 500
            },
            "top_p": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "default": 1.0
            }
          },
          "required": ["model", "temperature", "max_tokens"]
        }
      }
    },
    "prompts": {
      "type": "object",
      "properties": {
        "system": {
          "type": "object",
          "properties": {
            "profile_extraction": {
              "type": "string",
              "minLength": 10
            },
            "course_recommendation": {
              "type": "string",
              "minLength": 10
            }
          }
        }
      }
    },
    "scoring": {
      "type": "object",
      "properties": {
        "weights": {
          "type": "object",
          "properties": {
            "semantic": {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            "profile": {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            }
          },
          "additionalProperties": false
        },
        "thresholds": {
          "type": "object",
          "properties": {
            "match_threshold": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "default": 0.8
            }
          }
        }
      }
    },
    "retrieval": {
      "type": "object",
      "properties": {
        "initial_top_k": {
          "type": "integer",
          "minimum": 1,
          "maximum": 100,
          "default": 10
        },
        "rerank_top_k": {
          "type": "integer",
          "minimum": 1,
          "maximum": 50,
          "default": 5
        },
        "final_recommendations": {
          "type": "integer",
          "minimum": 1,
          "maximum": 20,
          "default": 5
        }
      }
    }
  },
  "required": ["llm", "prompts", "scoring", "retrieval"]
}
```

---

## Appendix B: Migration Checklist

### Per-POC Migration Checklist

```markdown
## POC: [POC_NAME]

### Phase 1: Audit
- [ ] Identify all hardcoded LLM models
- [ ] Identify all hardcoded prompts
- [ ] Identify all hardcoded hyperparameters
- [ ] Identify all hardcoded thresholds
- [ ] Identify all hardcoded regex patterns
- [ ] Identify all hardcoded scoring weights
- [ ] Document current behavior (for testing)

### Phase 2: Configuration Design
- [ ] Design configuration JSON structure
- [ ] Create JSON schema for validation
- [ ] Define default values
- [ ] Create configuration template

### Phase 3: Database Setup
- [ ] Insert POC configuration record
- [ ] Insert configuration schema
- [ ] Create default template
- [ ] Test configuration retrieval

### Phase 4: Code Refactoring
- [ ] Add config loading to service __init__
- [ ] Replace hardcoded models with config values
- [ ] Replace hardcoded prompts with config values
- [ ] Replace hardcoded parameters with config values
- [ ] Replace hardcoded thresholds with config values
- [ ] Add error handling for missing config

### Phase 5: Testing
- [ ] Unit tests: config loading
- [ ] Unit tests: config merging
- [ ] Integration tests: same behavior as before
- [ ] Integration tests: config updates work
- [ ] Integration tests: user overrides work
- [ ] Performance tests: no regression

### Phase 6: Frontend Integration
- [ ] Add config button to POC UI
- [ ] Test prompts tab
- [ ] Test models tab
- [ ] Test parameters tab
- [ ] Test thresholds tab
- [ ] Test scoring tab (if applicable)
- [ ] Test advanced tab

### Phase 7: Documentation
- [ ] Update POC README
- [ ] Document configuration options
- [ ] Create configuration best practices
- [ ] Add troubleshooting guide
```

---

**End of Document**

**Next Steps:**
1. Review and approve architecture
2. Begin Week 1: Infrastructure Setup
3. Pilot with British Council (Week 2)
4. Roll out to remaining POCs (Weeks 3-5)
5. Build frontend UI (Week 6)
6. Test and document (Week 7)

**Estimated Total Effort:** 7 weeks (1 developer full-time)
**Expected ROI:** 10x faster POC deployment, 50% reduction in engineering support
