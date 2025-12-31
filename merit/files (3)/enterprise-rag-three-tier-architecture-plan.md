# Enterprise RAG Platform: Deep-Dive Analysis & Three-Tier Architecture Plan

## Executive Summary

This document provides a comprehensive analysis of your Enterprise RAG Chatbot Stack and presents a detailed three-tier architecture implementation plan designed to accelerate bespoke customer implementations across diverse use cases including: RAG chatbots, data extraction pipelines, content enrichment, AI-assisted query engines, automatic tagging, NER, financial metric analysis, supply chain analytics, and mining industry end-to-end pipelines.

---

## Part 1: Current Architecture Deep-Dive Analysis

### 1.1 Repository Structure Analysis

Based on the repository structure at `trajeshbe/ChatBot/tree/claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK`:

```
├── .claude/                    # Claude AI development configuration
├── .devcontainer/              # VS Code dev container setup
├── Codex/                      # Code documentation/indexing
├── backend/                    # FastAPI + GraphQL backend
├── devops/skaffold/            # Local K8s development
├── docs/                       # Comprehensive documentation
│   ├── guides/                 # Quickstart, Admin guides
│   ├── architecture/           # Memory hierarchy, deployment
│   ├── setup/                  # LLM setup, local dev
│   ├── debugging/              # RAG debugging guides
│   └── evaluation/             # RAG evaluation guides
├── error_screenshots/          # Debug artifacts
├── frontend/                   # Next.js 14 frontend
├── infrastructure/             # K8s, Istio, ArgoCD, Tekton, OPA
├── istio-1.28.0/              # Service mesh config
├── ml/                        # ML pipelines, models
├── observability/             # Grafana, Tempo, Loki, Mimir
├── org_structure/             # Organization configs
├── sample_data/               # Test datasets
├── scripts/                   # Automation scripts
│   ├── setup/                 # Initial setup
│   ├── testing/               # Integration tests
│   ├── debugging/             # Diagnostics
│   └── maintenance/           # System maintenance
├── test_data/                 # Test fixtures
├── theme/                     # UI theming (customer customization)
├── docker-compose.yml         # Local development orchestration
├── Makefile                   # Build automation
└── CLAUDE.md                  # AI assistant development guide
```

### 1.2 Technology Stack Analysis

#### Frontend Layer
| Component | Technology | Maturity | Modularization Potential |
|-----------|------------|----------|--------------------------|
| Framework | Next.js 14 | Production-ready | High - SSR enables easy feature gating |
| Styling | Tailwind CSS | Production-ready | High - `/theme/` already exists |
| Language | TypeScript | Production-ready | High - Interface-driven development |
| Rendering | React Markdown | Production-ready | Medium - Use case specific |

**Assessment**: Frontend is well-positioned for multi-tenancy with existing theme support.

#### Backend Layer
| Component | Technology | Maturity | Modularization Potential |
|-----------|------------|----------|--------------------------|
| API Framework | FastAPI | Production-ready | High - Dependency injection native |
| GraphQL | Strawberry | Production-ready | High - Schema composition |
| Language | Python 3.11 | Production-ready | High - Dynamic loading |
| Doc Processing | Docling | Production-ready | High - Pipeline pattern |

**Assessment**: FastAPI's dependency injection and router system enables clean module boundaries.

#### LLM & AI Layer
| Component | Technology | Maturity | Modularization Potential |
|-----------|------------|----------|--------------------------|
| GPU Inference | vLLM on Kube-Ray | Production-ready | Medium - Resource intensive |
| CPU Fallback | llama.cpp | Production-ready | High - Lightweight |
| Cloud Fallback | OpenAI API | Production-ready | High - API abstraction |
| Embeddings | Sentence Transformers | Production-ready | High - Swappable |
| Orchestration | LangGraph | Production-ready | **Critical** - DAG-based workflows |

**Assessment**: LangGraph is the key enabler for use-case specific workflows.

#### Data Layer
| Component | Technology | Maturity | Modularization Potential |
|-----------|------------|----------|--------------------------|
| Vector DB | PostgreSQL 16 + pgvector | Production-ready | High - Schema isolation |
| Cache | Redis 7.2 + RediSearch | Production-ready | High - Namespace isolation |
| Object Storage | MinIO | Production-ready | High - Bucket isolation |
| Stream Processing | Apache Flink | Production-ready | Medium - Complex setup |
| Feature Store | Feast | Production-ready | High - Feature namespaces |

**Assessment**: All data layer components support multi-tenant isolation patterns.

#### Infrastructure Layer
| Component | Technology | Maturity | Modularization Potential |
|-----------|------------|----------|--------------------------|
| Orchestration | Kubernetes | Production-ready | High - Namespace isolation |
| Service Mesh | Istio Ambient | Production-ready | High - mTLS, traffic routing |
| Ingress | Envoy (Contour) | Production-ready | High - Route-based |
| Policy | OPA Gatekeeper | Production-ready | High - Declarative |
| GitOps | Argo CD | Production-ready | **Critical** - App-of-apps pattern |
| CI/CD | Tekton | Production-ready | High - Parameterized pipelines |
| Local Dev | Skaffold | Production-ready | High - Profile-based |

**Assessment**: Infrastructure is GitOps-ready for module-based deployments.

#### Observability Layer
| Component | Technology | Maturity | Modularization Potential |
|-----------|------------|----------|--------------------------|
| Tracing | OpenTelemetry | Production-ready | High - Span attributes |
| Traces Backend | Grafana Tempo | Production-ready | High - Tag filtering |
| Logs | Grafana Loki | Production-ready | High - Label-based |
| Metrics | Grafana Mimir | Production-ready | High - Metric labels |
| Visualization | Grafana | Production-ready | High - Dashboard vars |
| Cost | OpenCost | Production-ready | High - Label allocation |

**Assessment**: Full observability with tenant/module attribution capability.

### 1.3 Current Capabilities Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CURRENT PLATFORM CAPABILITIES                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │ Document Upload │    │  Web Scraping   │    │   Chat/Q&A      │        │
│  │  PDF, DOCX,     │───▶│  URL extraction │───▶│  Conversational │        │
│  │  TXT, JSON, MD  │    │  Prompt-based   │    │  Source refs    │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                     │                      │                   │
│           ▼                     ▼                      ▼                   │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                     SHARED PROCESSING PIPELINE                    │    │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐         │    │
│  │  │ Docling │─▶│Embeddings│─▶│ pgvector │─▶│Redis Cache│         │    │
│  │  │ Parser  │  │ Model    │  │  Store   │  │   VSS     │         │    │
│  │  └─────────┘  └──────────┘  └──────────┘  └───────────┘         │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│           │                     │                      │                   │
│           ▼                     ▼                      ▼                   │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                        LLM INFERENCE LAYER                        │    │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐                         │    │
│  │  │  vLLM   │◀─│ LangGraph│─▶│  OpenAI  │                         │    │
│  │  │  (GPU)  │  │   DAG    │  │ Fallback │                         │    │
│  │  └─────────┘  └──────────┘  └──────────┘                         │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Gaps Identified for Multi-Use-Case Support

| Gap | Impact | Priority | Effort |
|-----|--------|----------|--------|
| No module registry/loader | Cannot dynamically enable/disable features | Critical | Medium |
| Monolithic LangGraph DAG | Cannot swap workflows per use case | Critical | High |
| Single prompt template set | Cannot customize per domain | High | Low |
| No tenant context propagation | Cannot isolate customer data | High | Medium |
| Hardcoded extraction schemas | Cannot support varied data structures | High | Medium |
| No feature flag system | Cannot A/B test or gradual rollout | Medium | Low |
| Single embedding model | Cannot optimize for domain-specific retrieval | Medium | Medium |

---

## Part 2: Use Case Analysis & Module Mapping

### 2.1 Use Case Decomposition

| Use Case | Core Capability | Specialized Capability | Complexity |
|----------|-----------------|------------------------|------------|
| **Website Chatbot** | RAG + Conversation | Branding, Widget embed | Low |
| **Data Extraction Pipeline** | Document Processing | Schema extraction, Validation | Medium |
| **Metrics Extraction** | Data Extraction | Numeric parsing, Aggregation | Medium |
| **Content Enrichment** | NLP Processing | Entity linking, Taxonomy mapping | Medium |
| **AI Query Engine** | RAG + SQL Generation | Schema introspection, Query optimization | High |
| **Automatic Tagging** | Classification | Multi-label, Hierarchical taxonomy | Medium |
| **NER (Named Entity Recognition)** | NLP Processing | Custom entity types, Span detection | Medium |
| **Financial Metric Analysis** | Data Extraction + Analytics | Financial formulas, Period comparison | High |
| **Supply Chain Analytics** | Data Extraction + Analytics | Graph analysis, Optimization | High |
| **Mining E2E Pipeline** | Full Stack | Domain models, Safety compliance | Very High |

### 2.2 Capability Dependency Matrix

```
                          SHARED CORE    MODULE-SPECIFIC    CUSTOMER-SPECIFIC
                          ─────────────  ─────────────────  ─────────────────
Document Processing          ████████           ░░                 
Vector Storage               ████████           ░░                 
Semantic Caching             ████████                              
LLM Inference                ████████           ░░                 
Observability                ████████                              
Authentication               ████████                     ░░       
                                                                   
RAG Pipeline                              ████████                 
Data Extraction                           ████████                 
NLP/NER Processing                        ████████                 
Analytics Engine                          ████████                 
Classification                            ████████                 
                                                                   
Domain Prompts                                           ████████  
Branding/Theme                                           ████████  
Custom Integrations                                      ████████  
Business Logic                                           ████████  

████████ = Required    ░░ = Optional/Configurable
```

### 2.3 Module Definition

Based on analysis, the following modules are recommended:

```
TIER 2 MODULES
├── core-rag/                    # Base RAG functionality
│   ├── retrieval/               # Vector search, reranking
│   ├── generation/              # Response synthesis
│   └── conversation/            # Multi-turn handling
│
├── data-extraction/             # Structured data extraction
│   ├── schema-extraction/       # JSON/table extraction
│   ├── form-filling/            # Template population
│   └── validation/              # Data quality checks
│
├── nlp-processing/              # NLP capabilities
│   ├── ner/                     # Named entity recognition
│   ├── classification/          # Text classification
│   ├── tagging/                 # Multi-label tagging
│   └── entity-linking/          # KB linking
│
├── analytics-engine/            # Analytics capabilities
│   ├── metric-extraction/       # Numeric data extraction
│   ├── aggregation/             # Statistical analysis
│   ├── comparison/              # Period/entity comparison
│   └── visualization/           # Chart generation
│
├── query-engine/                # AI-assisted querying
│   ├── nl2sql/                  # Natural language to SQL
│   ├── schema-discovery/        # Database introspection
│   └── query-optimization/      # Performance tuning
│
└── domain-verticals/            # Industry-specific
    ├── financial/               # Financial services
    ├── supply-chain/            # Supply chain/logistics
    ├── mining/                  # Mining industry
    └── healthcare/              # Healthcare (future)
```

---

## Part 3: Three-Tier Architecture Specification

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CUSTOMER DEPLOYMENT                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  TIER 3: CUSTOMER BESPOKE LAYER                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │   Branding   │  │   Domain     │  │  Custom      │  │  Business    │    │   │
│  │  │   & Theme    │  │   Prompts    │  │  Integrations│  │  Logic       │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  │                                                                             │   │
│  │  Config: customer-{id}.yaml | Helm Values | Feature Overrides              │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                           │
│                                        ▼                                           │
│  TIER 2: USE-CASE MODULES (Selectively Enabled)                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │   │
│  │  │ core-rag │  │  data-   │  │   nlp-   │  │analytics-│  │  query-  │     │   │
│  │  │    ✓     │  │extraction│  │processing│  │  engine  │  │  engine  │     │   │
│  │  │          │  │    ✓     │  │    ✓     │  │    ✗     │  │    ✗     │     │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │   │
│  │                                                                             │   │
│  │  ┌────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  domain-verticals/financial  ✗  | supply-chain ✗ | mining ✗       │    │   │
│  │  └────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                             │   │
│  │  Registry: modules.yaml | LangGraph DAGs | Prompt Templates | Schemas     │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                           │
│                                        ▼                                           │
│  TIER 1: CORE PLATFORM (Always Deployed)                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │  FastAPI Core  │  GraphQL Schema  │  Auth/RBAC  │  Rate Limiting   │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │  PostgreSQL+pgvector │ Redis+RediSearch │ MinIO │ Apache Flink    │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │  vLLM/llama.cpp │ Sentence Transformers │ Docling │ LangGraph     │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │  OpenTelemetry │ Grafana Stack │ OpenCost │ Prefect 3             │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │  Kubernetes │ Istio Ambient │ Argo CD │ Tekton │ OPA Gatekeeper   │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Tier 1: Core Platform Specification

#### 3.2.1 Directory Structure Refactoring

**Current Structure** (Monolithic):
```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── utils/
```

**Proposed Structure** (Module-Aware):
```
backend/
├── app/
│   ├── main.py                          # App entrypoint
│   ├── core/                            # TIER 1: Core platform
│   │   ├── __init__.py
│   │   ├── config.py                    # Configuration loading
│   │   ├── database.py                  # PostgreSQL + pgvector
│   │   ├── cache.py                     # Redis + RediSearch
│   │   ├── storage.py                   # MinIO operations
│   │   ├── llm/                         # LLM abstraction layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Abstract LLM interface
│   │   │   ├── vllm_provider.py
│   │   │   ├── llamacpp_provider.py
│   │   │   └── openai_provider.py
│   │   ├── embeddings/                  # Embedding abstraction
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── sentence_transformers.py
│   │   ├── document_processing/         # Docling integration
│   │   │   ├── __init__.py
│   │   │   ├── parser.py
│   │   │   └── chunker.py
│   │   ├── auth/                        # Authentication
│   │   │   ├── __init__.py
│   │   │   ├── jwt.py
│   │   │   └── rbac.py
│   │   ├── observability/               # Tracing, metrics
│   │   │   ├── __init__.py
│   │   │   ├── tracing.py
│   │   │   └── metrics.py
│   │   └── api/                         # Core API routes
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── documents.py
│   │       └── settings.py
│   │
│   ├── modules/                         # TIER 2: Pluggable modules
│   │   ├── __init__.py
│   │   ├── registry.py                  # Module registry & loader
│   │   ├── base.py                      # Abstract module interface
│   │   └── [module_dirs]/               # Individual modules
│   │
│   ├── customers/                       # TIER 3: Customer configs
│   │   ├── __init__.py
│   │   ├── loader.py                    # Customer config loader
│   │   └── configs/                     # Customer-specific configs
│   │
│   └── api/                             # Unified API layer
│       ├── __init__.py
│       ├── router.py                    # Dynamic route registration
│       └── graphql/                     # GraphQL schema composition
```

#### 3.2.2 Core Platform Components

**Module Registry Implementation** (`backend/app/modules/registry.py`):

```python
"""
Module Registry - Central hub for module discovery and lifecycle management
"""
from typing import Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    LOADING = "loading"
    ERROR = "error"


@dataclass
class ModuleConfig:
    """Configuration for a single module"""
    name: str
    version: str
    enabled: bool = False
    dependencies: List[str] = field(default_factory=list)
    config: Dict = field(default_factory=dict)
    routes_prefix: str = ""
    
    
@dataclass
class ModuleMetadata:
    """Runtime metadata for loaded modules"""
    name: str
    config: ModuleConfig
    status: ModuleStatus
    instance: Optional["BaseModule"] = None
    error_message: Optional[str] = None


class ModuleRegistry:
    """
    Central registry for all platform modules.
    Handles discovery, loading, dependency resolution, and lifecycle.
    """
    
    _instance: Optional["ModuleRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._modules: Dict[str, ModuleMetadata] = {}
        self._load_order: List[str] = []
        self._initialized = True
    
    def discover_modules(self, modules_path: Path) -> List[str]:
        """
        Discover available modules in the modules directory.
        Each module must have a module.yaml and __init__.py
        """
        discovered = []
        for item in modules_path.iterdir():
            if item.is_dir() and (item / "module.yaml").exists():
                discovered.append(item.name)
                logger.info(f"Discovered module: {item.name}")
        return discovered
    
    def register_module(self, config: ModuleConfig) -> None:
        """Register a module configuration"""
        self._modules[config.name] = ModuleMetadata(
            name=config.name,
            config=config,
            status=ModuleStatus.DISABLED
        )
    
    def enable_module(self, name: str, customer_config: Dict = None) -> bool:
        """
        Enable a module with optional customer-specific configuration.
        Resolves dependencies and loads in correct order.
        """
        if name not in self._modules:
            logger.error(f"Module {name} not registered")
            return False
        
        metadata = self._modules[name]
        
        # Check dependencies
        for dep in metadata.config.dependencies:
            if dep not in self._modules or self._modules[dep].status != ModuleStatus.ENABLED:
                logger.info(f"Enabling dependency {dep} for {name}")
                if not self.enable_module(dep, customer_config):
                    return False
        
        # Load the module
        try:
            metadata.status = ModuleStatus.LOADING
            module_class = self._import_module(name)
            
            # Merge customer config with module defaults
            merged_config = {**metadata.config.config}
            if customer_config and name in customer_config:
                merged_config.update(customer_config[name])
            
            metadata.instance = module_class(merged_config)
            metadata.instance.initialize()
            metadata.status = ModuleStatus.ENABLED
            self._load_order.append(name)
            
            logger.info(f"Module {name} enabled successfully")
            return True
            
        except Exception as e:
            metadata.status = ModuleStatus.ERROR
            metadata.error_message = str(e)
            logger.error(f"Failed to enable module {name}: {e}")
            return False
    
    def _import_module(self, name: str) -> Type["BaseModule"]:
        """Dynamically import a module class"""
        module = importlib.import_module(f"app.modules.{name}")
        return module.Module
    
    def get_enabled_modules(self) -> List[ModuleMetadata]:
        """Get all enabled modules in load order"""
        return [
            self._modules[name] 
            for name in self._load_order 
            if self._modules[name].status == ModuleStatus.ENABLED
        ]
    
    def get_module(self, name: str) -> Optional[ModuleMetadata]:
        """Get a specific module by name"""
        return self._modules.get(name)
    
    def get_routes(self) -> List:
        """Collect all routes from enabled modules"""
        routes = []
        for metadata in self.get_enabled_modules():
            if metadata.instance:
                routes.extend(metadata.instance.get_routes())
        return routes
    
    def get_graphql_types(self) -> List:
        """Collect all GraphQL types from enabled modules"""
        types = []
        for metadata in self.get_enabled_modules():
            if metadata.instance:
                types.extend(metadata.instance.get_graphql_types())
        return types
    
    def shutdown(self):
        """Gracefully shutdown all modules in reverse order"""
        for name in reversed(self._load_order):
            metadata = self._modules[name]
            if metadata.instance:
                try:
                    metadata.instance.shutdown()
                    logger.info(f"Module {name} shutdown complete")
                except Exception as e:
                    logger.error(f"Error shutting down {name}: {e}")


# Singleton instance
registry = ModuleRegistry()
```

**Base Module Interface** (`backend/app/modules/base.py`):

```python
"""
Base Module Interface - All modules must implement this
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel


class ModuleCapability(BaseModel):
    """Describes a capability provided by a module"""
    name: str
    description: str
    version: str
    input_schema: Optional[Dict] = None
    output_schema: Optional[Dict] = None


class BaseModule(ABC):
    """
    Abstract base class for all platform modules.
    Modules must implement initialization, routes, and capability registration.
    """
    
    # Module metadata - override in subclasses
    NAME: str = "base"
    VERSION: str = "0.0.0"
    DESCRIPTION: str = "Base module"
    DEPENDENCIES: List[str] = []
    
    def __init__(self, config: Dict):
        self.config = config
        self._router: Optional[APIRouter] = None
        self._capabilities: List[ModuleCapability] = []
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the module. Called when module is enabled.
        Setup database tables, load models, register capabilities.
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        Cleanup resources when module is disabled or app shuts down.
        """
        pass
    
    def get_routes(self) -> List[APIRouter]:
        """Return FastAPI routers for this module"""
        if self._router:
            return [self._router]
        return []
    
    def get_graphql_types(self) -> List:
        """Return Strawberry GraphQL types for this module"""
        return []
    
    def get_capabilities(self) -> List[ModuleCapability]:
        """Return capabilities this module provides"""
        return self._capabilities
    
    def register_capability(self, capability: ModuleCapability) -> None:
        """Register a capability provided by this module"""
        self._capabilities.append(capability)
    
    @abstractmethod
    def get_langgraph_nodes(self) -> Dict[str, Any]:
        """
        Return LangGraph nodes this module contributes.
        Used for workflow composition.
        """
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """Module-specific health check"""
        return {
            "module": self.NAME,
            "status": "healthy" if self._initialized else "not_initialized",
            "version": self.VERSION
        }
```

**Customer Configuration Loader** (`backend/app/customers/loader.py`):

```python
"""
Customer Configuration Loader - Manages customer-specific settings
"""
import yaml
from pathlib import Path
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class BrandingConfig(BaseModel):
    """Customer branding configuration"""
    logo_url: Optional[str] = None
    primary_color: str = "#3B82F6"
    secondary_color: str = "#1E40AF"
    company_name: str = "Enterprise"
    favicon_url: Optional[str] = None
    custom_css: Optional[str] = None


class IntegrationConfig(BaseModel):
    """External integration configuration"""
    webhook_url: Optional[str] = None
    api_key_header: str = "X-API-Key"
    callback_urls: Dict[str, str] = Field(default_factory=dict)
    sso_config: Optional[Dict] = None


class ModuleOverrides(BaseModel):
    """Customer-specific module configuration overrides"""
    enabled_modules: list[str] = Field(default_factory=list)
    disabled_modules: list[str] = Field(default_factory=list)
    module_configs: Dict[str, Dict] = Field(default_factory=dict)


class CustomerConfig(BaseModel):
    """Complete customer configuration"""
    customer_id: str
    customer_name: str
    environment: str = "production"
    
    # Tier 3: Customer-specific
    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    integrations: IntegrationConfig = Field(default_factory=IntegrationConfig)
    
    # Module overrides
    modules: ModuleOverrides = Field(default_factory=ModuleOverrides)
    
    # Domain-specific prompts
    system_prompts: Dict[str, str] = Field(default_factory=dict)
    
    # Custom extraction schemas
    extraction_schemas: Dict[str, Dict] = Field(default_factory=dict)
    
    # Feature flags
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    
    # Resource limits
    rate_limits: Dict[str, int] = Field(default_factory=lambda: {
        "requests_per_minute": 60,
        "tokens_per_day": 100000,
        "documents_per_month": 1000
    })


class CustomerConfigLoader:
    """
    Loads and manages customer configurations.
    Supports file-based configs and runtime overrides.
    """
    
    def __init__(self, configs_path: Path):
        self.configs_path = configs_path
        self._cache: Dict[str, CustomerConfig] = {}
    
    @lru_cache(maxsize=100)
    def load_config(self, customer_id: str) -> CustomerConfig:
        """Load customer configuration from YAML file"""
        config_file = self.configs_path / f"{customer_id}.yaml"
        
        if not config_file.exists():
            logger.warning(f"No config found for {customer_id}, using defaults")
            return CustomerConfig(
                customer_id=customer_id,
                customer_name=customer_id
            )
        
        with open(config_file) as f:
            data = yaml.safe_load(f)
        
        config = CustomerConfig(**data)
        self._cache[customer_id] = config
        logger.info(f"Loaded configuration for customer: {customer_id}")
        return config
    
    def get_enabled_modules(self, customer_id: str) -> list[str]:
        """Get list of modules enabled for a customer"""
        config = self.load_config(customer_id)
        
        # Start with default modules
        enabled = set(["core-rag"])  # Always enabled
        
        # Add customer-enabled modules
        enabled.update(config.modules.enabled_modules)
        
        # Remove explicitly disabled
        enabled -= set(config.modules.disabled_modules)
        
        return list(enabled)
    
    def get_module_config(self, customer_id: str, module_name: str) -> Dict:
        """Get customer-specific configuration for a module"""
        config = self.load_config(customer_id)
        return config.modules.module_configs.get(module_name, {})
    
    def get_system_prompt(self, customer_id: str, prompt_key: str) -> Optional[str]:
        """Get customer-specific system prompt"""
        config = self.load_config(customer_id)
        return config.system_prompts.get(prompt_key)
    
    def is_feature_enabled(self, customer_id: str, feature: str) -> bool:
        """Check if a feature flag is enabled for customer"""
        config = self.load_config(customer_id)
        return config.feature_flags.get(feature, False)
    
    def invalidate_cache(self, customer_id: str = None):
        """Invalidate cached configurations"""
        if customer_id:
            self._cache.pop(customer_id, None)
            self.load_config.cache_clear()
        else:
            self._cache.clear()
            self.load_config.cache_clear()
```

### 3.3 Tier 2: Module Specifications

#### 3.3.1 Core RAG Module

**Directory Structure**:
```
modules/
└── core_rag/
    ├── __init__.py              # Module entry point
    ├── module.yaml              # Module metadata
    ├── config.py                # Configuration schema
    ├── router.py                # FastAPI routes
    ├── graphql/                 # GraphQL types & resolvers
    │   ├── __init__.py
    │   ├── types.py
    │   └── resolvers.py
    ├── services/                # Business logic
    │   ├── __init__.py
    │   ├── retrieval.py         # Vector search service
    │   ├── generation.py        # Response generation
    │   ├── conversation.py      # Multi-turn handling
    │   └── reranking.py         # Result reranking
    ├── workflows/               # LangGraph DAGs
    │   ├── __init__.py
    │   ├── rag_chain.py         # Main RAG workflow
    │   └── nodes.py             # Workflow nodes
    ├── prompts/                 # Prompt templates
    │   ├── system.txt
    │   ├── retrieval.txt
    │   └── generation.txt
    └── tests/
        ├── __init__.py
        ├── test_retrieval.py
        └── test_generation.py
```

**Module Configuration** (`modules/core_rag/module.yaml`):
```yaml
name: core-rag
version: "1.0.0"
description: "Core RAG functionality with retrieval, generation, and conversation management"

dependencies: []  # No dependencies, this is a base module

routes_prefix: "/api/v1/rag"

config:
  # Retrieval settings
  retrieval:
    top_k: 5
    similarity_threshold: 0.7
    reranking_enabled: true
    reranking_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
  
  # Generation settings
  generation:
    max_tokens: 1024
    temperature: 0.7
    include_sources: true
    streaming_enabled: true
  
  # Conversation settings
  conversation:
    max_history_turns: 10
    summarize_after_turns: 5
    context_window_tokens: 4096

capabilities:
  - name: "semantic_search"
    description: "Search documents using semantic similarity"
    input_schema:
      type: object
      properties:
        query: {type: string}
        filters: {type: object}
        top_k: {type: integer}
    output_schema:
      type: array
      items:
        type: object
        properties:
          content: {type: string}
          score: {type: number}
          metadata: {type: object}
  
  - name: "generate_response"
    description: "Generate response based on retrieved context"
    input_schema:
      type: object
      properties:
        query: {type: string}
        context: {type: array}
        conversation_history: {type: array}
    output_schema:
      type: object
      properties:
        response: {type: string}
        sources: {type: array}
        confidence: {type: number}

langgraph_nodes:
  - retrieve_documents
  - rerank_results
  - generate_response
  - format_output
```

**Module Implementation** (`modules/core_rag/__init__.py`):
```python
"""
Core RAG Module - Provides base RAG functionality
"""
from typing import Dict, List, Any
from fastapi import APIRouter

from app.modules.base import BaseModule, ModuleCapability
from .config import CoreRAGConfig
from .router import router as rag_router
from .services.retrieval import RetrievalService
from .services.generation import GenerationService
from .services.conversation import ConversationService
from .workflows.rag_chain import create_rag_workflow
from .graphql.types import RAGQuery, RAGResponse


class Module(BaseModule):
    """Core RAG Module implementation"""
    
    NAME = "core-rag"
    VERSION = "1.0.0"
    DESCRIPTION = "Core RAG functionality with retrieval and generation"
    DEPENDENCIES = []
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.rag_config = CoreRAGConfig(**config)
        self.retrieval_service: RetrievalService = None
        self.generation_service: GenerationService = None
        self.conversation_service: ConversationService = None
        self._workflow = None
    
    def initialize(self) -> None:
        """Initialize RAG services"""
        # Initialize services
        self.retrieval_service = RetrievalService(self.rag_config.retrieval)
        self.generation_service = GenerationService(self.rag_config.generation)
        self.conversation_service = ConversationService(self.rag_config.conversation)
        
        # Create LangGraph workflow
        self._workflow = create_rag_workflow(
            retrieval_service=self.retrieval_service,
            generation_service=self.generation_service,
            conversation_service=self.conversation_service
        )
        
        # Setup router with dependencies
        self._router = rag_router
        self._router.retrieval_service = self.retrieval_service
        self._router.generation_service = self.generation_service
        
        # Register capabilities
        self.register_capability(ModuleCapability(
            name="semantic_search",
            description="Search documents using semantic similarity",
            version="1.0.0"
        ))
        self.register_capability(ModuleCapability(
            name="generate_response",
            description="Generate response based on retrieved context",
            version="1.0.0"
        ))
        
        self._initialized = True
    
    def shutdown(self) -> None:
        """Cleanup resources"""
        if self.retrieval_service:
            self.retrieval_service.close()
        if self.generation_service:
            self.generation_service.close()
        self._initialized = False
    
    def get_routes(self) -> List[APIRouter]:
        """Return RAG API routes"""
        return [self._router]
    
    def get_graphql_types(self) -> List:
        """Return GraphQL types"""
        return [RAGQuery, RAGResponse]
    
    def get_langgraph_nodes(self) -> Dict[str, Any]:
        """Return LangGraph nodes for workflow composition"""
        return {
            "retrieve_documents": self.retrieval_service.retrieve,
            "rerank_results": self.retrieval_service.rerank,
            "generate_response": self.generation_service.generate,
            "summarize_history": self.conversation_service.summarize
        }
    
    def get_workflow(self):
        """Get the RAG workflow for execution"""
        return self._workflow
```

#### 3.3.2 Data Extraction Module

**Directory Structure**:
```
modules/
└── data_extraction/
    ├── __init__.py
    ├── module.yaml
    ├── config.py
    ├── router.py
    ├── services/
    │   ├── __init__.py
    │   ├── schema_extractor.py      # JSON/structured extraction
    │   ├── table_extractor.py       # Table extraction
    │   ├── form_filler.py           # Template population
    │   └── validator.py             # Data validation
    ├── workflows/
    │   ├── __init__.py
    │   ├── extraction_chain.py
    │   └── nodes.py
    ├── schemas/                     # Predefined extraction schemas
    │   ├── invoice.json
    │   ├── contract.json
    │   └── resume.json
    ├── prompts/
    │   ├── extraction_system.txt
    │   └── validation_system.txt
    └── tests/
```

**Module Configuration** (`modules/data_extraction/module.yaml`):
```yaml
name: data-extraction
version: "1.0.0"
description: "Structured data extraction from documents"

dependencies:
  - core-rag  # Needs document processing from core

routes_prefix: "/api/v1/extraction"

config:
  extraction:
    default_schema: "auto"  # auto-detect or specify
    confidence_threshold: 0.8
    validation_enabled: true
    output_formats: ["json", "csv", "xlsx"]
  
  table_extraction:
    enabled: true
    merge_cells: true
    header_detection: "auto"
  
  form_filling:
    enabled: true
    template_storage: "minio"

capabilities:
  - name: "extract_structured_data"
    description: "Extract structured data based on schema"
  - name: "extract_tables"
    description: "Extract tables from documents"
  - name: "fill_template"
    description: "Fill document template with extracted data"
  - name: "validate_extraction"
    description: "Validate extracted data against schema"

langgraph_nodes:
  - analyze_document_structure
  - extract_schema_data
  - extract_tables
  - validate_results
  - format_output
```

#### 3.3.3 NLP Processing Module

**Directory Structure**:
```
modules/
└── nlp_processing/
    ├── __init__.py
    ├── module.yaml
    ├── config.py
    ├── router.py
    ├── services/
    │   ├── __init__.py
    │   ├── ner_service.py           # Named entity recognition
    │   ├── classification_service.py # Text classification
    │   ├── tagging_service.py       # Multi-label tagging
    │   └── entity_linking_service.py # Knowledge base linking
    ├── models/                      # Model definitions
    │   ├── __init__.py
    │   ├── ner_model.py
    │   └── classifier_model.py
    ├── workflows/
    │   ├── __init__.py
    │   ├── nlp_chain.py
    │   └── nodes.py
    ├── taxonomies/                  # Predefined taxonomies
    │   ├── standard_entities.json
    │   └── industry_tags.json
    └── tests/
```

**Module Configuration** (`modules/nlp_processing/module.yaml`):
```yaml
name: nlp-processing
version: "1.0.0"
description: "NLP capabilities including NER, classification, and tagging"

dependencies:
  - core-rag

routes_prefix: "/api/v1/nlp"

config:
  ner:
    enabled: true
    model: "en_core_web_lg"  # spaCy model
    custom_entities: []
    confidence_threshold: 0.7
  
  classification:
    enabled: true
    model: "distilbert-base-uncased"
    max_labels: 5
    threshold: 0.5
  
  tagging:
    enabled: true
    taxonomy_source: "taxonomies/standard_entities.json"
    hierarchical: true
  
  entity_linking:
    enabled: false
    knowledge_base: "wikidata"

capabilities:
  - name: "extract_entities"
    description: "Extract named entities from text"
  - name: "classify_text"
    description: "Classify text into categories"
  - name: "tag_content"
    description: "Apply multi-label tags to content"
  - name: "link_entities"
    description: "Link entities to knowledge base"

langgraph_nodes:
  - preprocess_text
  - extract_entities
  - classify_content
  - apply_tags
  - link_entities
  - aggregate_results
```

#### 3.3.4 Analytics Engine Module

```yaml
# modules/analytics_engine/module.yaml
name: analytics-engine
version: "1.0.0"
description: "Analytics and metric extraction capabilities"

dependencies:
  - core-rag
  - data-extraction

routes_prefix: "/api/v1/analytics"

config:
  metric_extraction:
    enabled: true
    numeric_patterns: true
    currency_detection: true
    date_normalization: true
  
  aggregation:
    enabled: true
    functions: ["sum", "avg", "min", "max", "count", "std"]
    grouping_enabled: true
  
  comparison:
    enabled: true
    period_types: ["yoy", "qoq", "mom", "custom"]
    variance_thresholds: [0.05, 0.10, 0.20]
  
  visualization:
    enabled: true
    chart_types: ["line", "bar", "pie", "scatter", "heatmap"]
    export_formats: ["png", "svg", "pdf"]

capabilities:
  - name: "extract_metrics"
  - name: "aggregate_data"
  - name: "compare_periods"
  - name: "generate_visualization"
```

#### 3.3.5 Query Engine Module

```yaml
# modules/query_engine/module.yaml
name: query-engine
version: "1.0.0"
description: "AI-assisted query generation and execution"

dependencies:
  - core-rag

routes_prefix: "/api/v1/query"

config:
  nl2sql:
    enabled: true
    dialect: "postgresql"  # postgresql, mysql, sqlite
    max_joins: 5
    explain_queries: true
  
  schema_discovery:
    enabled: true
    cache_ttl: 3600
    include_samples: true
  
  query_optimization:
    enabled: true
    timeout_seconds: 30
    max_rows: 10000

capabilities:
  - name: "natural_language_to_sql"
  - name: "discover_schema"
  - name: "execute_query"
  - name: "optimize_query"
```

#### 3.3.6 Domain Vertical: Financial Module

```yaml
# modules/domain_financial/module.yaml
name: domain-financial
version: "1.0.0"
description: "Financial services domain-specific capabilities"

dependencies:
  - core-rag
  - data-extraction
  - analytics-engine

routes_prefix: "/api/v1/financial"

config:
  financial_extraction:
    enabled: true
    metric_types:
      - revenue
      - ebitda
      - net_income
      - cash_flow
      - debt_equity_ratio
      - current_ratio
    currency_normalization: true
    fiscal_calendar: "calendar"  # calendar, fiscal-jan, fiscal-apr
  
  period_analysis:
    enabled: true
    standard_periods: ["Q1", "Q2", "Q3", "Q4", "FY", "YTD"]
    comparison_types: ["absolute", "percentage", "cagr"]
  
  compliance:
    enabled: false
    standards: ["GAAP", "IFRS"]

capabilities:
  - name: "extract_financial_metrics"
  - name: "analyze_financial_periods"
  - name: "generate_financial_summary"
  - name: "compare_financials"

# Domain-specific prompts
prompts:
  financial_extraction: |
    You are a financial analyst assistant. Extract the following metrics 
    from the provided document with high precision. Include:
    - The exact value with currency
    - The period it relates to
    - Confidence level
    - Source location in document
    
  financial_comparison: |
    Compare the financial metrics between the specified periods.
    Highlight significant variances (>5%) and provide brief analysis.
```

### 3.4 Tier 3: Customer Configuration Schema

#### 3.4.1 Customer Configuration File Template

```yaml
# customers/configs/acme-corp.yaml
customer_id: "acme-corp"
customer_name: "Acme Corporation"
environment: "production"

# Branding Configuration
branding:
  logo_url: "https://cdn.acme.com/logo.svg"
  primary_color: "#1E3A8A"
  secondary_color: "#3B82F6"
  company_name: "Acme AI Assistant"
  favicon_url: "https://cdn.acme.com/favicon.ico"
  custom_css: |
    .chat-header { background: linear-gradient(135deg, #1E3A8A, #3B82F6); }
    .message-bubble { border-radius: 12px; }

# Integration Configuration
integrations:
  webhook_url: "https://api.acme.com/webhooks/ai-events"
  api_key_header: "X-Acme-API-Key"
  callback_urls:
    document_processed: "https://api.acme.com/callbacks/document"
    extraction_complete: "https://api.acme.com/callbacks/extraction"
  sso_config:
    provider: "okta"
    domain: "acme.okta.com"
    client_id: "${ACME_SSO_CLIENT_ID}"

# Module Configuration
modules:
  enabled_modules:
    - core-rag
    - data-extraction
    - nlp-processing
    - domain-financial
  
  disabled_modules:
    - query-engine  # Not needed for this customer
  
  module_configs:
    core-rag:
      retrieval:
        top_k: 10  # Customer wants more results
        similarity_threshold: 0.65
      generation:
        max_tokens: 2048  # Longer responses
        temperature: 0.5  # More focused
    
    data-extraction:
      extraction:
        default_schema: "financial_report"
        confidence_threshold: 0.85  # Higher accuracy required
    
    nlp-processing:
      ner:
        custom_entities:
          - ACME_PRODUCT
          - ACME_DIVISION
          - COMPETITOR
      classification:
        max_labels: 3
    
    domain-financial:
      financial_extraction:
        metric_types:
          - revenue
          - gross_margin
          - operating_income
          - free_cash_flow
        currency_normalization: true
        base_currency: "USD"

# Domain-specific prompts (overrides module defaults)
system_prompts:
  main: |
    You are the Acme AI Assistant, a helpful financial analysis tool 
    for Acme Corporation employees. You have access to internal 
    financial documents, reports, and market analysis.
    
    Guidelines:
    - Always cite your sources with document names
    - Flag any metrics that seem unusual or require verification
    - Use Acme's standard terminology for financial metrics
    - Never share confidential information outside approved channels
  
  extraction: |
    Extract financial metrics from Acme Corporation documents.
    Focus on: Revenue, Gross Margin, Operating Income, Free Cash Flow.
    Use USD as the base currency. Flag any non-USD values for conversion.
  
  comparison: |
    When comparing financial periods for Acme:
    - Always include YoY comparison
    - Highlight variances > 5%
    - Note any one-time items or adjustments

# Custom extraction schemas
extraction_schemas:
  quarterly_report:
    type: object
    properties:
      quarter: { type: string, pattern: "^Q[1-4] \\d{4}$" }
      revenue: 
        type: object
        properties:
          value: { type: number }
          currency: { type: string, default: "USD" }
          yoy_change: { type: number }
      gross_margin:
        type: object
        properties:
          percentage: { type: number }
          yoy_change: { type: number }
      operating_income:
        type: object
        properties:
          value: { type: number }
          currency: { type: string }
      highlights:
        type: array
        items: { type: string }
    required: [quarter, revenue, gross_margin]

# Feature flags
feature_flags:
  enable_streaming: true
  enable_voice_input: false
  enable_document_upload: true
  enable_web_scraping: false  # Disabled for security
  enable_cost_tracking: true
  enable_feedback_collection: true
  enable_export_to_excel: true
  beta_features:
    enable_multi_modal: false
    enable_agent_mode: false

# Resource limits
rate_limits:
  requests_per_minute: 120
  tokens_per_day: 500000
  documents_per_month: 5000
  concurrent_extractions: 10

# Data isolation
data_isolation:
  namespace: "acme-corp"
  vector_collection: "acme_documents"
  cache_prefix: "acme:"
  storage_bucket: "acme-corp-documents"
```

### 3.5 Infrastructure Configuration

#### 3.5.1 Helm Chart Structure

```
infrastructure/helm/
├── Chart.yaml
├── values.yaml                      # Default values
├── values-production.yaml           # Production overrides
├── templates/
│   ├── _helpers.tpl
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   └── pdb.yaml
└── customers/                       # Customer-specific values
    ├── acme-corp.yaml
    ├── globex-inc.yaml
    └── initech.yaml
```

#### 3.5.2 Argo CD Application-of-Apps Pattern

```yaml
# infrastructure/argocd/app-of-apps.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: enterprise-rag-platform
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/trajeshbe/ChatBot.git
    targetRevision: HEAD
    path: infrastructure/argocd/apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
---
# infrastructure/argocd/apps/customer-acme-corp.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: rag-platform-acme-corp
  namespace: argocd
  labels:
    customer: acme-corp
    tier: production
spec:
  project: default
  source:
    repoURL: https://github.com/trajeshbe/ChatBot.git
    targetRevision: HEAD
    path: infrastructure/helm
    helm:
      valueFiles:
        - values.yaml
        - values-production.yaml
        - customers/acme-corp.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: rag-acme-corp
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

---

## Part 4: Implementation Roadmap

### 4.1 Phase Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          IMPLEMENTATION TIMELINE                                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  PHASE 1: Foundation (Weeks 1-3)                                                │
│  ════════════════════════════════                                               │
│  [█████████████████████] Core Platform Refactoring                              │
│  [████████████████]      Module Registry Implementation                         │
│  [██████████████]        Customer Config Loader                                 │
│                                                                                  │
│  PHASE 2: Core Modules (Weeks 4-6)                                              │
│  ════════════════════════════════                                               │
│  [████████████████████████████] Core RAG Module Extraction                      │
│  [██████████████████████]       Data Extraction Module                          │
│  [██████████████████]           NLP Processing Module                           │
│                                                                                  │
│  PHASE 3: Advanced Modules (Weeks 7-9)                                          │
│  ═════════════════════════════════════                                          │
│  [████████████████████████] Analytics Engine Module                             │
│  [██████████████████████]   Query Engine Module                                 │
│  [████████████████████]     Domain Verticals (Financial)                        │
│                                                                                  │
│  PHASE 4: Customer Tooling (Weeks 10-11)                                        │
│  ═══════════════════════════════════════                                        │
│  [██████████████████████████████] Deployment Automation                         │
│  [████████████████████████]       Customer Onboarding CLI                       │
│  [████████████████████]           Documentation & Training                      │
│                                                                                  │
│  PHASE 5: Production Hardening (Week 12)                                        │
│  ═══════════════════════════════════════                                        │
│  [██████████████████████████████████████] Testing & Validation                  │
│  [████████████████████████████████]       Performance Optimization              │
│  [██████████████████████████████]         Security Audit                        │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Detailed Phase Breakdown

#### Phase 1: Foundation (Weeks 1-3)

**Week 1: Core Platform Refactoring**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 1.1 | Create new directory structure under `backend/app/` | 4h | Backend Lead |
| 1.2 | Extract core services (database, cache, storage) to `core/` | 8h | Backend Lead |
| 1.3 | Create LLM abstraction layer with provider pattern | 8h | ML Engineer |
| 1.4 | Create embeddings abstraction layer | 4h | ML Engineer |
| 1.5 | Setup core API routes (health, settings) | 4h | Backend Dev |
| 1.6 | Update imports throughout codebase | 8h | Backend Team |

**Deliverables:**
- `backend/app/core/` fully implemented
- All services abstracted behind interfaces
- Existing functionality maintained

**Week 2: Module Registry Implementation**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 2.1 | Implement `ModuleRegistry` class | 8h | Backend Lead |
| 2.2 | Implement `BaseModule` abstract class | 4h | Backend Lead |
| 2.3 | Create module discovery mechanism | 4h | Backend Dev |
| 2.4 | Implement dependency resolution | 8h | Backend Dev |
| 2.5 | Create dynamic route registration | 4h | Backend Dev |
| 2.6 | Create GraphQL schema composition | 8h | Backend Dev |
| 2.7 | Write unit tests for registry | 4h | QA |

**Deliverables:**
- Fully functional module registry
- Dynamic route and GraphQL registration
- 90%+ test coverage on registry

**Week 3: Customer Configuration System**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 3.1 | Implement `CustomerConfigLoader` | 8h | Backend Lead |
| 3.2 | Create Pydantic models for config schema | 4h | Backend Dev |
| 3.3 | Implement config caching mechanism | 4h | Backend Dev |
| 3.4 | Create sample customer configs | 4h | Backend Dev |
| 3.5 | Integrate config with module loading | 8h | Backend Lead |
| 3.6 | Add feature flag evaluation | 4h | Backend Dev |
| 3.7 | Write integration tests | 8h | QA |

**Deliverables:**
- Customer config system fully implemented
- Sample configs for 3 mock customers
- Feature flag system operational

---

#### Phase 2: Core Modules (Weeks 4-6)

**Week 4: Core RAG Module Extraction**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 4.1 | Create `modules/core_rag/` structure | 2h | Backend Lead |
| 4.2 | Extract retrieval service | 8h | ML Engineer |
| 4.3 | Extract generation service | 8h | ML Engineer |
| 4.4 | Extract conversation service | 6h | ML Engineer |
| 4.5 | Create LangGraph workflow | 8h | ML Engineer |
| 4.6 | Migrate prompts to module | 2h | Backend Dev |
| 4.7 | Create module.yaml and config | 2h | Backend Dev |
| 4.8 | Write module tests | 4h | QA |

**Week 5: Data Extraction Module**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 5.1 | Create `modules/data_extraction/` structure | 2h | Backend Lead |
| 5.2 | Implement schema extractor service | 12h | Backend Dev |
| 5.3 | Implement table extractor service | 8h | Backend Dev |
| 5.4 | Implement form filler service | 8h | Backend Dev |
| 5.5 | Create validation service | 6h | Backend Dev |
| 5.6 | Create extraction workflow | 4h | ML Engineer |
| 5.7 | Write module tests | 8h | QA |

**Week 6: NLP Processing Module**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 6.1 | Create `modules/nlp_processing/` structure | 2h | Backend Lead |
| 6.2 | Implement NER service | 10h | ML Engineer |
| 6.3 | Implement classification service | 8h | ML Engineer |
| 6.4 | Implement tagging service | 6h | ML Engineer |
| 6.5 | Create NLP workflow | 6h | ML Engineer |
| 6.6 | Create default taxonomies | 4h | Backend Dev |
| 6.7 | Write module tests | 8h | QA |

---

#### Phase 3: Advanced Modules (Weeks 7-9)

**Week 7: Analytics Engine Module**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 7.1 | Create `modules/analytics_engine/` structure | 2h | Backend Lead |
| 7.2 | Implement metric extraction service | 12h | Backend Dev |
| 7.3 | Implement aggregation service | 8h | Backend Dev |
| 7.4 | Implement comparison service | 8h | Backend Dev |
| 7.5 | Implement visualization service | 8h | Frontend Dev |
| 7.6 | Create analytics workflow | 4h | ML Engineer |
| 7.7 | Write module tests | 8h | QA |

**Week 8: Query Engine Module**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 8.1 | Create `modules/query_engine/` structure | 2h | Backend Lead |
| 8.2 | Implement NL2SQL service | 16h | ML Engineer |
| 8.3 | Implement schema discovery service | 8h | Backend Dev |
| 8.4 | Implement query optimization | 8h | Backend Dev |
| 8.5 | Create query workflow | 4h | ML Engineer |
| 8.6 | Write module tests | 8h | QA |

**Week 9: Domain Vertical - Financial**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 9.1 | Create `modules/domain_financial/` structure | 2h | Backend Lead |
| 9.2 | Implement financial metric extraction | 12h | Domain Expert |
| 9.3 | Implement period analysis | 8h | Domain Expert |
| 9.4 | Create financial prompts | 8h | Domain Expert |
| 9.5 | Create financial extraction schemas | 4h | Domain Expert |
| 9.6 | Write module tests | 8h | QA |

---

#### Phase 4: Customer Tooling (Weeks 10-11)

**Week 10: Deployment Automation**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 10.1 | Create Helm chart with module support | 12h | DevOps |
| 10.2 | Create Argo CD app-of-apps pattern | 8h | DevOps |
| 10.3 | Create customer namespace provisioning | 4h | DevOps |
| 10.4 | Create Tekton pipeline for deployments | 8h | DevOps |
| 10.5 | Create Skaffold profiles for modules | 4h | DevOps |
| 10.6 | Test deployment automation | 8h | DevOps + QA |

**Week 11: Customer Onboarding CLI**

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 11.1 | Create CLI framework (Click/Typer) | 4h | Backend Dev |
| 11.2 | Implement `rag-platform init` command | 8h | Backend Dev |
| 11.3 | Implement `rag-platform deploy` command | 8h | Backend Dev |
| 11.4 | Implement `rag-platform config` command | 4h | Backend Dev |
| 11.5 | Create documentation | 8h | Tech Writer |
| 11.6 | Create training materials | 8h | Tech Writer |

---

#### Phase 5: Production Hardening (Week 12)

| Task | Description | Effort | Owner |
|------|-------------|--------|-------|
| 12.1 | End-to-end integration testing | 16h | QA Team |
| 12.2 | Performance testing & optimization | 12h | Backend Team |
| 12.3 | Security audit | 8h | Security |
| 12.4 | Documentation review | 4h | Tech Writer |
| 12.5 | Runbook creation | 4h | DevOps |
| 12.6 | Final sign-off | 4h | All Leads |

---

## Part 5: Claude Skills for Acceleration

### 5.1 Customer Onboarding Skill

```markdown
# /mnt/skills/user/customer-onboarding/SKILL.md

## Purpose
Accelerate new customer onboarding by generating configuration files, 
deployment manifests, and initialization scripts from requirements.

## Workflow
1. Gather customer requirements through structured questions
2. Generate customer configuration YAML
3. Generate Helm values override file
4. Generate Argo CD application manifest
5. Generate onboarding checklist

## Usage
User: "Onboard new customer TechCorp, they need RAG chatbot and 
      data extraction for PDF invoices, SSO with Azure AD"

Output:
- customers/configs/techcorp.yaml
- infrastructure/helm/customers/techcorp.yaml
- infrastructure/argocd/apps/customer-techcorp.yaml
- docs/onboarding/techcorp-checklist.md
```

### 5.2 Module Generator Skill

```markdown
# /mnt/skills/user/module-generator/SKILL.md

## Purpose
Scaffold new use-case modules following the platform's module pattern.

## Workflow
1. Gather module requirements (name, capabilities, dependencies)
2. Generate module directory structure
3. Generate module.yaml configuration
4. Generate base service implementations
5. Generate LangGraph workflow skeleton
6. Generate test stubs

## Usage
User: "Create a new module for contract analysis with clause extraction,
      risk scoring, and compliance checking"

Output:
- modules/contract_analysis/
  - __init__.py
  - module.yaml
  - config.py
  - router.py
  - services/clause_extractor.py
  - services/risk_scorer.py
  - services/compliance_checker.py
  - workflows/contract_chain.py
  - tests/test_contract_analysis.py
```

### 5.3 Prompt Tuner Skill

```markdown
# /mnt/skills/user/prompt-tuner/SKILL.md

## Purpose
Refine and optimize domain-specific prompts based on sample data 
and customer feedback.

## Workflow
1. Analyze sample documents/data provided
2. Identify domain terminology and patterns
3. Generate optimized system prompts
4. Generate few-shot examples
5. Output versioned prompt files

## Usage
User: "Tune prompts for mining industry, here are sample documents..."

Output:
- modules/domain_mining/prompts/system.txt
- modules/domain_mining/prompts/extraction.txt
- modules/domain_mining/prompts/examples/few_shot.json
```

---

## Part 6: Migration Strategy

### 6.1 Migration Approach

**Strategy: Strangler Fig Pattern**

```
┌──────────────────────────────────────────────────────────────────┐
│                    MIGRATION APPROACH                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Stage 1: Shadow Mode                                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  New modular system runs alongside existing monolith       │ │
│  │  Traffic: 100% monolith, 0% modular                        │ │
│  │  Validation: Compare outputs for correctness               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ▼                                      │
│  Stage 2: Canary Release                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Gradually shift traffic to modular system                 │ │
│  │  Traffic: 90% monolith, 10% modular                        │ │
│  │  Monitor: Latency, errors, user feedback                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ▼                                      │
│  Stage 3: Progressive Rollout                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Increase modular traffic based on metrics                 │ │
│  │  Traffic: 50% → 75% → 90% → 100% modular                   │ │
│  │  Rollback: Automated on error threshold breach             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ▼                                      │
│  Stage 4: Deprecation                                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Monolith deprecated, modular system is primary            │ │
│  │  Monolith kept for 30 days for emergency rollback          │ │
│  │  Final: Remove monolith code                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Risk Mitigation

| Risk | Mitigation | Contingency |
|------|------------|-------------|
| Module loading failures | Comprehensive testing, circuit breakers | Fall back to monolith |
| Performance degradation | Load testing, gradual rollout | Traffic shift back |
| Data inconsistency | Dual-write during migration | Reconciliation scripts |
| Customer disruption | Staged rollout by customer | Customer-level rollback |
| Integration breakage | Contract testing, API versioning | Legacy endpoint support |

---

## Part 7: Success Metrics

### 7.1 Technical Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| New module creation time | N/A (manual) | < 2 days | Time to first deployment |
| Customer onboarding time | 2-3 weeks | < 3 days | Time to production |
| Module test coverage | N/A | > 80% | pytest coverage |
| Deployment frequency | Weekly | Daily | ArgoCD metrics |
| Mean time to recovery | Hours | < 15 minutes | Incident tracking |

### 7.2 Business Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| POC to Production conversion | ~40% | > 70% | CRM tracking |
| Customer implementation cost | High | -50% | Project accounting |
| Time to value for customers | Weeks | Days | Customer feedback |
| Platform reuse across customers | ~30% | > 80% | Code analysis |
| Customer satisfaction | Baseline | +20% | NPS surveys |

---

## Appendices

### Appendix A: Module Interface Contract

```python
# Full interface specification for modules
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class ModuleInterface(ABC, Generic[T]):
    """Complete interface contract for platform modules"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique module identifier"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version string"""
        pass
    
    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """List of required module names"""
        pass
    
    @abstractmethod
    def initialize(self, config: T) -> None:
        """Initialize module with configuration"""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Graceful shutdown"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return health status"""
        pass
    
    @abstractmethod
    def get_routes(self) -> List["APIRouter"]:
        """Return FastAPI routers"""
        pass
    
    @abstractmethod
    def get_graphql_types(self) -> List[Any]:
        """Return Strawberry types"""
        pass
    
    @abstractmethod
    def get_langgraph_nodes(self) -> Dict[str, callable]:
        """Return workflow nodes"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List["ModuleCapability"]:
        """Return capability declarations"""
        pass
```

### Appendix B: Customer Configuration JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CustomerConfiguration",
  "type": "object",
  "required": ["customer_id", "customer_name"],
  "properties": {
    "customer_id": {
      "type": "string",
      "pattern": "^[a-z0-9-]+$"
    },
    "customer_name": {
      "type": "string"
    },
    "environment": {
      "type": "string",
      "enum": ["development", "staging", "production"]
    },
    "branding": {
      "type": "object",
      "properties": {
        "logo_url": {"type": "string", "format": "uri"},
        "primary_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "secondary_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "company_name": {"type": "string"}
      }
    },
    "modules": {
      "type": "object",
      "properties": {
        "enabled_modules": {
          "type": "array",
          "items": {"type": "string"}
        },
        "disabled_modules": {
          "type": "array",
          "items": {"type": "string"}
        },
        "module_configs": {
          "type": "object",
          "additionalProperties": {"type": "object"}
        }
      }
    },
    "feature_flags": {
      "type": "object",
      "additionalProperties": {"type": "boolean"}
    },
    "rate_limits": {
      "type": "object",
      "properties": {
        "requests_per_minute": {"type": "integer", "minimum": 1},
        "tokens_per_day": {"type": "integer", "minimum": 1},
        "documents_per_month": {"type": "integer", "minimum": 1}
      }
    }
  }
}
```

### Appendix C: LangGraph Workflow Composition Pattern

```python
"""
Example of composing module workflows into a unified execution graph
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Any

class PlatformState(TypedDict):
    """Shared state across all module workflows"""
    query: str
    documents: List[Any]
    extracted_data: dict
    entities: List[dict]
    response: str
    metadata: dict

def compose_workflow(enabled_modules: List["BaseModule"]) -> StateGraph:
    """
    Dynamically compose a workflow from enabled modules.
    Each module contributes nodes that are wired together.
    """
    workflow = StateGraph(PlatformState)
    
    # Collect all nodes from modules
    all_nodes = {}
    for module in enabled_modules:
        nodes = module.get_langgraph_nodes()
        for name, func in nodes.items():
            prefixed_name = f"{module.NAME}_{name}"
            all_nodes[prefixed_name] = func
            workflow.add_node(prefixed_name, func)
    
    # Wire nodes based on capability dependencies
    # This is a simplified example - real implementation would
    # use capability declarations to determine wiring
    
    # Example: RAG + NLP + Analytics composition
    if "core-rag_retrieve_documents" in all_nodes:
        workflow.set_entry_point("core-rag_retrieve_documents")
        workflow.add_edge("core-rag_retrieve_documents", "core-rag_rerank_results")
    
    if "nlp-processing_extract_entities" in all_nodes:
        workflow.add_edge("core-rag_rerank_results", "nlp-processing_extract_entities")
        workflow.add_edge("nlp-processing_extract_entities", "core-rag_generate_response")
    else:
        workflow.add_edge("core-rag_rerank_results", "core-rag_generate_response")
    
    if "analytics-engine_extract_metrics" in all_nodes:
        workflow.add_edge("core-rag_generate_response", "analytics-engine_extract_metrics")
        workflow.add_edge("analytics-engine_extract_metrics", END)
    else:
        workflow.add_edge("core-rag_generate_response", END)
    
    return workflow.compile()
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-XX | Claude AI | Initial comprehensive analysis and plan |

---

*This document serves as the master plan for implementing the three-tier architecture. 
It should be reviewed and updated as implementation progresses.*
