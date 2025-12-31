# Three-Tier Folder Reorganization Plan

**Date**: 2025-12-31
**Purpose**: Reorganize existing codebase into 3-tier architecture without disrupting functionality
**Approach**: Keep ALL current code as Tier 1 (Core Platform), add empty Tier 2/3 folders for future expansion

---

## 🎯 Goals

1. ✅ **Zero Disruption**: All existing functionality remains unchanged
2. ✅ **Clear Organization**: Logical folder hierarchy matching 3-tier architecture
3. ✅ **Future Ready**: Structure prepared for modular expansion (Tier 2/3)
4. ✅ **Minimal Changes**: Only import path updates, no business logic changes

---

## 📊 Current State Analysis

### Inventory

| Category | Count | Location |
|----------|-------|----------|
| **Core Infrastructure** | 4 files | `app/core/` |
| **Services** | 51 files | `app/services/*.py` |
| **Service Subdirs** | 5 subdirs | `app/services/{engines, finetuning, project_estimator, webscraper, ...}` |
| **RAG Pipeline** | 10 files | `app/rag_pipeline/` |
| **Agents** | 2 subdirs | `app/agents/{construction_metrics, project_estimator}` |
| **API Routes** | Multiple | `app/api/routes/` |
| **Models** | Multiple | `app/models/` |
| **Schemas** | Multiple | `app/schemas/` |

### Current Structure
```
backend/app/
├── __init__.py
├── main.py
├── main_enhanced.py
├── core/                    # Infrastructure (4 files)
├── services/                # Business logic (51 files + 5 subdirs)
├── rag_pipeline/            # RAG components (10 files)
├── agents/                  # LangGraph agents (2 subdirs)
├── api/                     # REST + GraphQL
├── models/                  # Database models
├── schemas/                 # Pydantic schemas
├── tasks/                   # Celery tasks
├── tools/                   # Utility tools
├── utils/                   # Helper functions
├── mcp/                     # MCP integration
├── middleware/              # Middleware
├── metrics/                 # Metrics
└── config/                  # Configuration files
```

---

## 🏗️ Proposed 3-Tier Structure

### New Organization

```
backend/app/
├── __init__.py
├── main.py                  # Entry point (minimal changes)
├── main_enhanced.py
│
├── tier-1/                  # 🆕 TIER 1: CORE PLATFORM (all existing code)
│   ├── __init__.py
│   ├── README.md           # "Core Platform - Always Deployed"
│   │
│   ├── infrastructure/     # Core infrastructure services
│   │   ├── __init__.py
│   │   ├── config.py       # ← from app/core/config.py
│   │   ├── database.py     # ← from app/core/database.py
│   │   ├── security.py     # ← from app/core/security.py
│   │   ├── cache.py        # ← Redis/caching logic (if exists)
│   │   └── storage.py      # ← MinIO logic (extract from services)
│   │
│   ├── llm/                # LLM abstraction layer
│   │   ├── __init__.py
│   │   ├── llm_service.py              # ← from app/services/llm_service.py
│   │   ├── ollama_model_service.py     # ← from app/services/
│   │   ├── ollama_deployment_service.py # ← from app/services/
│   │   └── mcp_server_service.py       # ← from app/services/
│   │
│   ├── embeddings/         # Embedding services
│   │   ├── __init__.py
│   │   ├── embedding_service.py            # ← from app/services/
│   │   ├── intelligent_embedding_service.py # ← from app/services/
│   │   └── reranker_service.py             # ← from app/services/
│   │
│   ├── document_processing/ # Document handling
│   │   ├── __init__.py
│   │   ├── document_service.py         # ← from app/services/
│   │   ├── ocr_service.py              # ← from app/services/
│   │   ├── vision_service.py           # ← from app/services/
│   │   ├── content_analyzer.py         # ← from app/services/
│   │   └── hybrid_extraction_service.py # ← from app/services/
│   │
│   ├── rag/                # Core RAG functionality
│   │   ├── __init__.py
│   │   ├── rag_service.py              # ← from app/services/
│   │   ├── multi_strategy_rag.py       # ← from app/services/
│   │   ├── intelligent_retrieval_service.py # ← from app/services/
│   │   ├── query_reformulation_service.py   # ← from app/services/
│   │   ├── query_classifier.py              # ← from app/services/
│   │   ├── dynamic_query_classifier.py      # ← from app/services/
│   │   └── pipeline/                   # ← from app/rag_pipeline/
│   │       ├── __init__.py
│   │       ├── config.py
│   │       ├── embeddings.py
│   │       ├── llm.py
│   │       ├── observability.py
│   │       ├── pipeline.py
│   │       ├── reranker.py
│   │       ├── retrieval.py
│   │       └── semantic_cache.py
│   │
│   ├── agents/             # Agent framework
│   │   ├── __init__.py
│   │   ├── agent_service.py            # ← from app/services/
│   │   ├── agent_sandbox_manager.py    # ← from app/services/
│   │   ├── task_router.py              # ← from app/services/
│   │   ├── terminal_session_manager.py # ← from app/services/
│   │   ├── optimized_state_manager.py  # ← from app/services/
│   │   └── engines/                    # ← from app/services/engines/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── default_engine.py
│   │       ├── claude_code_cli_engine.py
│   │       └── codex_cli_engine.py
│   │
│   ├── platform_services/ # Platform-level services
│   │   ├── __init__.py
│   │   ├── auth_service.py             # ← from app/services/
│   │   ├── rbac_service.py             # ← from app/services/
│   │   ├── audit_service.py            # ← from app/services/
│   │   ├── secrets_service.py          # ← from app/services/
│   │   ├── api_usage_tracker.py        # ← from app/services/
│   │   ├── tool_usage_tracker.py       # ← from app/services/
│   │   └── security_guardrails.py      # ← from app/services/
│   │
│   ├── finetuning/         # Fine-tuning infrastructure
│   │   ├── __init__.py
│   │   ├── finetuning_service.py       # ← from app/services/finetuning/
│   │   ├── gpu_pool_manager.py         # ← from app/services/finetuning/
│   │   ├── gpu_resource_manager.py     # ← from app/services/
│   │   ├── base_trainer.py             # ← from app/services/finetuning/
│   │   ├── trainer_factory.py          # ← from app/services/finetuning/
│   │   ├── dataset_preprocessor.py     # ← from app/services/finetuning/
│   │   ├── model_evaluation_service.py # ← from app/services/finetuning/
│   │   ├── model_merge_service.py      # ← from app/services/finetuning/
│   │   ├── model_registry_service.py   # ← from app/services/finetuning/
│   │   └── trainers/                   # ← from app/services/finetuning/trainers/
│   │       ├── sft_trainer.py
│   │       ├── peft_trainer.py
│   │       ├── rlhf_ppo_trainer.py
│   │       ├── rlhf_grpo_trainer.py
│   │       └── unsloth_trainer.py
│   │
│   ├── evaluation/         # Evaluation services
│   │   ├── __init__.py
│   │   ├── evaluation_service.py       # ← from app/services/
│   │   ├── ragas_evaluator.py          # ← from app/services/
│   │   └── quality_metrics.py          # ← from app/services/
│   │
│   ├── data_extraction/    # Data extraction services
│   │   ├── __init__.py
│   │   ├── template_extraction_service.py  # ← from app/services/
│   │   ├── template_parser_service.py      # ← from app/services/
│   │   ├── scraper_service.py              # ← from app/services/
│   │   ├── scraper_strategies.py           # ← from app/services/
│   │   ├── scraping_config_service.py      # ← from app/services/
│   │   └── webscraper/                     # ← from app/services/webscraper/
│   │       ├── core/
│   │       ├── agents/
│   │       ├── compliance/
│   │       ├── extractors/
│   │       ├── workflows/
│   │       ├── templates/
│   │       └── ... (all subdirs)
│   │
│   ├── nlp_processing/     # NLP services
│   │   ├── __init__.py
│   │   ├── translation_service.py          # ← from app/services/
│   │   ├── complexity_analyzer_service.py  # ← from app/services/
│   │   ├── task_complexity_analyzer.py     # ← from app/services/
│   │   ├── eda_analyzer.py                 # ← from app/services/
│   │   ├── multi_analyzer_ensemble.py      # ← from app/services/
│   │   └── multi_channel_processor.py      # ← from app/services/
│   │
│   ├── export/             # Export services
│   │   ├── __init__.py
│   │   ├── export_service.py           # ← from app/services/
│   │   └── weights_config_service.py   # ← from app/services/
│   │
│   ├── cv_processing/      # Computer vision services
│   │   ├── __init__.py
│   │   └── opencv_measurement_service.py # ← from app/services/
│   │
│   └── utilities/          # Shared utilities
│       ├── __init__.py
│       ├── minio_path_builder.py       # ← from app/services/
│       └── ... (other utility services)
│
├── tier-2/                  # 🆕 TIER 2: PLUGGABLE MODULES (future expansion)
│   ├── __init__.py
│   ├── README.md           # "Use-Case Modules - Selectively Enabled"
│   ├── registry.py         # Module registry & loader (TO BE IMPLEMENTED)
│   ├── base.py             # Abstract module interface (TO BE IMPLEMENTED)
│   │
│   ├── construction_metrics/  # ← MOVE from app/agents/construction_metrics/
│   │   ├── __init__.py
│   │   ├── workflow.py
│   │   ├── state.py
│   │   ├── extractors.py
│   │   └── aggregator.py
│   │
│   ├── project_estimator/  # ← MOVE from app/agents/project_estimator/
│   │   ├── __init__.py
│   │   ├── workflow.py
│   │   ├── prompt_templates.py
│   │   └── ... (service files from app/services/project_estimator/)
│   │
│   └── _templates/         # Module templates for future development
│       ├── module_template/
│       │   ├── __init__.py
│       │   ├── workflow.py
│       │   └── README.md
│       └── README.md       # "How to create new modules"
│
├── tier-3/                  # 🆕 TIER 3: CUSTOMER IMPLEMENTATIONS (future expansion)
│   ├── __init__.py
│   ├── README.md           # "Customer Configurations - Bespoke Deployments"
│   ├── loader.py           # Customer config loader (TO BE IMPLEMENTED)
│   │
│   ├── configs/            # Customer YAML configurations
│   │   ├── _template.yaml  # Template configuration
│   │   └── README.md       # "How to create customer configs"
│   │
│   └── _examples/          # Example customer implementations
│       ├── british-council/
│       │   ├── config.yaml
│       │   └── README.md
│       └── README.md       # "Customer onboarding guide"
│
├── api/                    # API layer (KEEP AS IS - minor import updates)
│   ├── __init__.py
│   ├── routes/            # Import from tier-1/*
│   └── graphql/
│
├── models/                 # Database models (KEEP AS IS)
│   └── ...
│
├── schemas/                # Pydantic schemas (KEEP AS IS)
│   └── ...
│
├── tasks/                  # Celery tasks (KEEP AS IS - update imports)
│   └── ...
│
├── middleware/             # Middleware (KEEP AS IS)
│   └── ...
│
├── metrics/                # Metrics (KEEP AS IS)
│   └── ...
│
├── mcp/                    # MCP (KEEP AS IS or move to tier-1/platform_services/)
│   └── ...
│
├── tools/                  # Tools (KEEP AS IS)
│   └── ...
│
├── utils/                  # Utils (KEEP AS IS)
│   └── ...
│
└── config/                 # Config files (KEEP AS IS)
    └── ...
```

---

## 📋 Migration Checklist

### Phase 1: Preparation (Week 1, Day 1)
- [ ] Create backup branch: `git checkout -b backup/pre-three-tier-reorg`
- [ ] Document all current import paths (script to find all imports)
- [ ] Run full test suite to establish baseline
- [ ] Create new folder structure (empty directories)

### Phase 2: Tier 1 Reorganization (Week 1, Days 2-3)
- [ ] Create `tier-1/` directory structure
- [ ] Move files to new Tier 1 locations (use `git mv` to preserve history)
- [ ] Update `__init__.py` files with exports
- [ ] Create README.md for each Tier 1 subdirectory

### Phase 3: Import Path Updates (Week 1, Days 4-5)
- [ ] Update imports in `api/routes/` files
- [ ] Update imports in `tasks/` files
- [ ] Update imports in `main.py` and `main_enhanced.py`
- [ ] Update imports in test files
- [ ] Run automated import checker script

### Phase 4: Tier 2/3 Setup (Week 2, Day 1)
- [ ] Create `tier-2/` with registry skeleton
- [ ] Move existing agents to `tier-2/`
- [ ] Create `tier-3/` with loader skeleton
- [ ] Create template files and documentation

### Phase 5: Testing & Validation (Week 2, Days 2-3)
- [ ] Run full test suite
- [ ] Test all API endpoints
- [ ] Verify Docker build succeeds
- [ ] Test local development workflow
- [ ] Run production deployment dry-run

### Phase 6: Documentation (Week 2, Days 4-5)
- [ ] Update CLAUDE.md with new structure
- [ ] Update README.md with new paths
- [ ] Create migration guide for developers
- [ ] Update architecture diagrams
- [ ] Create Tier 2/3 development guides

---

## 🔄 Import Path Changes

### Example: Before & After

**Before**:
```python
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from app.rag_pipeline.pipeline import RAGPipeline
from app.core.config import Settings
```

**After**:
```python
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.embeddings.embedding_service import EmbeddingService
from app.tier_1.rag.pipeline.pipeline import RAGPipeline
from app.tier_1.infrastructure.config import Settings
```

### Backwards Compatibility Option

Create compatibility shims in old locations:

```python
# app/services/llm_service.py (legacy location)
"""
DEPRECATED: This module has moved to app.tier_1.llm.llm_service
This file provides backwards compatibility and will be removed in v2.0
"""
from app.tier_1.llm.llm_service import *  # noqa: F401, F403
import warnings

warnings.warn(
    "Importing from app.services.llm_service is deprecated. "
    "Use app.tier_1.llm.llm_service instead.",
    DeprecationWarning,
    stacklevel=2
)
```

---

## 🛠️ Automation Scripts

### Script 1: Create Directory Structure
```bash
#!/bin/bash
# scripts/migration/01_create_tier_structure.sh

mkdir -p backend/app/tier-1/{infrastructure,llm,embeddings,document_processing,rag/pipeline,agents/engines,platform_services,finetuning/trainers,evaluation,data_extraction/webscraper,nlp_processing,export,cv_processing,utilities}
mkdir -p backend/app/tier-2/{construction_metrics,project_estimator,_templates/module_template}
mkdir -p backend/app/tier-3/{configs,_examples/british-council}

echo "✅ Directory structure created"
```

### Script 2: Move Files (Example)
```bash
#!/bin/bash
# scripts/migration/02_move_tier1_files.sh

# LLM services
git mv backend/app/services/llm_service.py backend/app/tier-1/llm/
git mv backend/app/services/ollama_model_service.py backend/app/tier-1/llm/
git mv backend/app/services/ollama_deployment_service.py backend/app/tier-1/llm/

# Embedding services
git mv backend/app/services/embedding_service.py backend/app/tier-1/embeddings/
git mv backend/app/services/intelligent_embedding_service.py backend/app/tier-1/embeddings/
git mv backend/app/services/reranker_service.py backend/app/tier-1/embeddings/

# ... (continue for all services)

echo "✅ Files moved (git history preserved)"
```

### Script 3: Update Imports
```python
#!/usr/bin/env python3
# scripts/migration/03_update_imports.py

import os
import re
from pathlib import Path

IMPORT_MAPPINGS = {
    'from app.services.llm_service': 'from app.tier_1.llm.llm_service',
    'from app.services.embedding_service': 'from app.tier_1.embeddings.embedding_service',
    'from app.rag_pipeline': 'from app.tier_1.rag.pipeline',
    'from app.core.config': 'from app.tier_1.infrastructure.config',
    # ... add all mappings
}

def update_imports_in_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    original = content
    for old, new in IMPORT_MAPPINGS.items():
        content = content.replace(old, new)

    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Updated: {file_path}")

def main():
    backend_path = Path("backend/app")
    for py_file in backend_path.rglob("*.py"):
        if "tier-1" not in str(py_file):  # Don't update moved files
            update_imports_in_file(py_file)

if __name__ == "__main__":
    main()
```

---

## 🎯 Success Criteria

### Must Pass Before Merge
- ✅ All existing tests pass (100% success rate)
- ✅ Docker build succeeds without errors
- ✅ All API endpoints return 200 (health check)
- ✅ No import errors in any module
- ✅ Code coverage remains ≥80%
- ✅ CI/CD pipeline succeeds

### Quality Checks
- ✅ All moved files have updated imports
- ✅ No broken imports (run `python -m compileall backend/app`)
- ✅ All README.md files created
- ✅ Documentation updated (CLAUDE.md, README.md)
- ✅ Git history preserved (use `git mv`, not `mv`)

---

## 📊 Impact Analysis

### Affected Files (Estimate)

| Category | Files Affected | Change Type |
|----------|----------------|-------------|
| **Services** | 51 files moved | File relocation + import updates |
| **RAG Pipeline** | 10 files moved | File relocation + import updates |
| **API Routes** | ~30 files | Import path updates only |
| **Tests** | ~100 files | Import path updates only |
| **Tasks** | ~5 files | Import path updates only |
| **Main Entry** | 2 files | Import path updates only |
| **Documentation** | 10+ files | Content updates |

**Total Files**: ~200+ files touched
**Actual Code Changes**: Minimal (mostly import paths)
**Business Logic Changes**: **ZERO**

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Broken imports** | High | Medium | Automated import checker script + comprehensive testing |
| **Test failures** | High | Low | Run tests at each phase checkpoint |
| **Docker build failure** | High | Low | Test build after each major change |
| **Git history loss** | Medium | Low | Use `git mv` exclusively, not `mv` |
| **Developer confusion** | Medium | High | Clear documentation + migration guide + team training |
| **Deployment issues** | High | Low | Staged rollout + rollback plan |

---

## 🚀 Rollout Strategy

### Development Environment
1. Create feature branch: `feature/three-tier-reorganization`
2. Complete migration in phases (see checklist)
3. Test locally with full test suite
4. Code review by team
5. Merge to development branch

### Staging Environment
1. Deploy to staging
2. Run E2E tests
3. Manual testing by QA team
4. Performance benchmarking (ensure no regression)

### Production
1. **Gradual rollout** (if possible with blue-green deployment)
2. Monitor error rates closely (first 24 hours)
3. **Rollback plan**: Revert to previous commit if critical issues
4. Success metrics: Zero production errors for 48 hours

---

## 📚 Post-Migration Benefits

### Immediate Benefits
✅ **Clear Organization**: Logical folder structure aligned with architecture
✅ **Better Navigation**: Developers find code faster
✅ **Documentation Alignment**: Folder structure matches architecture docs

### Future Benefits
✅ **Modular Development**: Easy to add Tier 2 modules
✅ **Customer Onboarding**: Simple Tier 3 config-based deployment
✅ **Code Reuse**: Clear boundaries between platform and modules
✅ **Team Scalability**: Teams can own specific tiers

---

## 📞 Next Steps

1. **Review this plan** with development team
2. **Estimate effort** (recommended: 2 weeks with 1 developer)
3. **Schedule migration** (low-traffic period recommended)
4. **Assign ownership** (who will execute migration)
5. **Create tracking** (GitHub project or Jira epic)

---

## ✅ Approval Required

- [ ] Technical Lead approval
- [ ] Architecture team approval
- [ ] QA team acknowledgment
- [ ] DevOps team acknowledgment
- [ ] Documentation team acknowledgment

---

**Migration Owner**: _TBD_
**Estimated Duration**: 2 weeks
**Target Start Date**: _TBD_
**Risk Level**: 🟡 Medium (High impact but well-mitigated)

---

**End of Plan**
