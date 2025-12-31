#!/bin/bash

# Three-Tier Reorganization - Script 1: Create Directory Structure
# Purpose: Create empty tier-1, tier-2, tier-3 folder hierarchies
# Date: 2025-12-31

set -e  # Exit on error

echo "=================================================="
echo "Three-Tier Reorganization - Directory Creation"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Navigate to backend/app
cd "$(dirname "$0")/../../backend/app" || exit 1

echo -e "${BLUE}📁 Creating Tier 1 directories...${NC}"

# Tier 1: Core Platform
mkdir -p tier-1/infrastructure
mkdir -p tier-1/llm
mkdir -p tier-1/embeddings
mkdir -p tier-1/document_processing
mkdir -p tier-1/rag/pipeline
mkdir -p tier-1/agents/engines
mkdir -p tier-1/platform_services
mkdir -p tier-1/finetuning/trainers
mkdir -p tier-1/finetuning/rewards
mkdir -p tier-1/evaluation
mkdir -p tier-1/data_extraction/webscraper
mkdir -p tier-1/nlp_processing
mkdir -p tier-1/export
mkdir -p tier-1/cv_processing
mkdir -p tier-1/utilities

echo -e "${GREEN}✅ Tier 1 structure created${NC}"
echo ""

echo -e "${BLUE}📁 Creating Tier 2 directories...${NC}"

# Tier 2: Pluggable Modules
mkdir -p tier-2/construction_metrics
mkdir -p tier-2/project_estimator
mkdir -p tier-2/_templates/module_template

echo -e "${GREEN}✅ Tier 2 structure created${NC}"
echo ""

echo -e "${BLUE}📁 Creating Tier 3 directories...${NC}"

# Tier 3: Customer Implementations
mkdir -p tier-3/configs
mkdir -p tier-3/_examples/british-council
mkdir -p tier-3/_examples/construction-monitoring
mkdir -p tier-3/_examples/grant-thornton

echo -e "${GREEN}✅ Tier 3 structure created${NC}"
echo ""

echo -e "${BLUE}📝 Creating __init__.py files...${NC}"

# Create __init__.py in all directories
find tier-1 tier-2 tier-3 -type d -exec touch {}/__init__.py \;

echo -e "${GREEN}✅ __init__.py files created${NC}"
echo ""

echo -e "${BLUE}📄 Creating README files...${NC}"

# Tier 1 README
cat > tier-1/README.md << 'EOF'
# Tier 1: Core Platform

**Status**: Always Deployed
**Purpose**: Foundation services required by all deployments

## Categories

- **infrastructure/**: Config, database, security, cache, storage
- **llm/**: LLM abstraction layer (OpenAI, Claude, Ollama, vLLM)
- **embeddings/**: Embedding and reranking services
- **document_processing/**: Document upload, OCR, vision, extraction
- **rag/**: RAG services and pipeline
- **agents/**: Agent framework and engines
- **platform_services/**: Auth, RBAC, audit, secrets, usage tracking
- **finetuning/**: Model fine-tuning infrastructure
- **evaluation/**: Evaluation and quality metrics
- **data_extraction/**: Web scraping and template extraction
- **nlp_processing/**: NLP services (translation, analysis, etc.)
- **export/**: Export and reporting services
- **cv_processing/**: Computer vision services
- **utilities/**: Shared utility functions

## Import Pattern

```python
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.rag.rag_service import RAGService
```

See [THREE_TIER_REORGANIZATION_PLAN.md](../../docs/architecture/THREE_TIER_REORGANIZATION_PLAN.md) for full details.
EOF

# Tier 2 README
cat > tier-2/README.md << 'EOF'
# Tier 2: Use-Case Modules

**Status**: Selectively Enabled
**Purpose**: Domain-specific capabilities enabled per customer

## Current Modules

- **construction_metrics/**: Building metrics extraction workflow
- **project_estimator/**: Project estimation workflow

## Module Registry (TO BE IMPLEMENTED)

See `registry.py` for dynamic module loading.

## Creating New Modules

See `_templates/module_template/` for starter template.

## Import Pattern

```python
from app.tier_2.construction_metrics.workflow import ConstructionMetricsWorkflow
```

See [THREE_TIER_REORGANIZATION_PLAN.md](../../docs/architecture/THREE_TIER_REORGANIZATION_PLAN.md) for full details.
EOF

# Tier 3 README
cat > tier-3/README.md << 'EOF'
# Tier 3: Customer Implementations

**Status**: Bespoke Configurations
**Purpose**: Customer-specific deployments and configurations

## Customer Configurations

Place customer YAML configs in `configs/` directory.

Example:
```yaml
# configs/acme-corp.yaml
customer:
  name: "Acme Corp"
  industry: "financial_services"

enabled_modules:
  - core_rag
  - financial_document_analysis

rag_settings:
  top_k: 10
  min_similarity: 0.75
```

## Examples

See `_examples/` for reference implementations:
- british-council
- construction-monitoring
- grant-thornton

## Config Loader (TO BE IMPLEMENTED)

See `loader.py` for YAML config loading.

See [THREE_TIER_REORGANIZATION_PLAN.md](../../docs/architecture/THREE_TIER_REORGANIZATION_PLAN.md) for full details.
EOF

echo -e "${GREEN}✅ README files created${NC}"
echo ""

echo "=================================================="
echo -e "${GREEN}✅ Directory structure creation COMPLETE${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Review created structure: ls -R tier-1/ tier-2/ tier-3/"
echo "2. Run script 02: ./scripts/migration/02_move_tier1_files.sh"
echo ""
