#!/bin/bash

# Three-Tier Reorganization - Script 2: Move Files to Tier 1
# Purpose: Move all services and core files to tier-1/ structure using git mv
# Date: 2025-12-31

set -e  # Exit on error

echo "=================================================="
echo "Three-Tier Reorganization - File Migration"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to backend/app
cd "$(dirname "$0")/../../backend/app" || exit 1

echo -e "${YELLOW}⚠️  This script will move files using 'git mv' to preserve history${NC}"
echo -e "${YELLOW}⚠️  Make sure you have a backup branch before proceeding!${NC}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""

# Function to move file with git mv
move_file() {
    local src=$1
    local dest=$2
    if [ -f "$src" ]; then
        git mv "$src" "$dest"
        echo -e "${GREEN}✅ Moved: $src → $dest${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipped (not found): $src${NC}"
    fi
}

# Function to move directory with git mv
move_dir() {
    local src=$1
    local dest=$2
    if [ -d "$src" ]; then
        git mv "$src" "$dest"
        echo -e "${GREEN}✅ Moved: $src/ → $dest/${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipped (not found): $src/${NC}"
    fi
}

echo -e "${BLUE}📦 Moving Core Infrastructure...${NC}"
move_file "core/config.py" "tier-1/infrastructure/config.py"
move_file "core/database.py" "tier-1/infrastructure/database.py"
move_file "core/security.py" "tier-1/infrastructure/security.py"
echo ""

echo -e "${BLUE}📦 Moving LLM Services...${NC}"
move_file "services/llm_service.py" "tier-1/llm/llm_service.py"
move_file "services/ollama_model_service.py" "tier-1/llm/ollama_model_service.py"
move_file "services/ollama_deployment_service.py" "tier-1/llm/ollama_deployment_service.py"
move_file "services/mcp_server_service.py" "tier-1/llm/mcp_server_service.py"
echo ""

echo -e "${BLUE}📦 Moving Embedding Services...${NC}"
move_file "services/embedding_service.py" "tier-1/embeddings/embedding_service.py"
move_file "services/intelligent_embedding_service.py" "tier-1/embeddings/intelligent_embedding_service.py"
move_file "services/reranker_service.py" "tier-1/embeddings/reranker_service.py"
echo ""

echo -e "${BLUE}📦 Moving Document Processing Services...${NC}"
move_file "services/document_service.py" "tier-1/document_processing/document_service.py"
move_file "services/ocr_service.py" "tier-1/document_processing/ocr_service.py"
move_file "services/vision_service.py" "tier-1/document_processing/vision_service.py"
move_file "services/content_analyzer.py" "tier-1/document_processing/content_analyzer.py"
move_file "services/hybrid_extraction_service.py" "tier-1/document_processing/hybrid_extraction_service.py"
echo ""

echo -e "${BLUE}📦 Moving RAG Services...${NC}"
move_file "services/rag_service.py" "tier-1/rag/rag_service.py"
move_file "services/multi_strategy_rag.py" "tier-1/rag/multi_strategy_rag.py"
move_file "services/intelligent_retrieval_service.py" "tier-1/rag/intelligent_retrieval_service.py"
move_file "services/query_reformulation_service.py" "tier-1/rag/query_reformulation_service.py"
move_file "services/query_classifier.py" "tier-1/rag/query_classifier.py"
move_file "services/dynamic_query_classifier.py" "tier-1/rag/dynamic_query_classifier.py"
echo ""

echo -e "${BLUE}📦 Moving RAG Pipeline...${NC}"
if [ -d "rag_pipeline" ]; then
    # Move individual files to preserve granular history
    move_file "rag_pipeline/__init__.py" "tier-1/rag/pipeline/__init__.py"
    move_file "rag_pipeline/config.py" "tier-1/rag/pipeline/config.py"
    move_file "rag_pipeline/embeddings.py" "tier-1/rag/pipeline/embeddings.py"
    move_file "rag_pipeline/llm.py" "tier-1/rag/pipeline/llm.py"
    move_file "rag_pipeline/observability.py" "tier-1/rag/pipeline/observability.py"
    move_file "rag_pipeline/pipeline.py" "tier-1/rag/pipeline/pipeline.py"
    move_file "rag_pipeline/reranker.py" "tier-1/rag/pipeline/reranker.py"
    move_file "rag_pipeline/retrieval.py" "tier-1/rag/pipeline/retrieval.py"
    move_file "rag_pipeline/semantic_cache.py" "tier-1/rag/pipeline/semantic_cache.py"
    move_file "rag_pipeline/README.md" "tier-1/rag/pipeline/README.md"
fi
echo ""

echo -e "${BLUE}📦 Moving Agent Services...${NC}"
move_file "services/agent_service.py" "tier-1/agents/agent_service.py"
move_file "services/agent_sandbox_manager.py" "tier-1/agents/agent_sandbox_manager.py"
move_file "services/task_router.py" "tier-1/agents/task_router.py"
move_file "services/terminal_session_manager.py" "tier-1/agents/terminal_session_manager.py"
move_file "services/optimized_state_manager.py" "tier-1/agents/optimized_state_manager.py"
echo ""

echo -e "${BLUE}📦 Moving Agent Engines...${NC}"
if [ -d "services/engines" ]; then
    move_dir "services/engines" "tier-1/agents/engines"
fi
echo ""

echo -e "${BLUE}📦 Moving Platform Services...${NC}"
move_file "services/auth_service.py" "tier-1/platform_services/auth_service.py"
move_file "services/rbac_service.py" "tier-1/platform_services/rbac_service.py"
move_file "services/audit_service.py" "tier-1/platform_services/audit_service.py"
move_file "services/secrets_service.py" "tier-1/platform_services/secrets_service.py"
move_file "services/api_usage_tracker.py" "tier-1/platform_services/api_usage_tracker.py"
move_file "services/tool_usage_tracker.py" "tier-1/platform_services/tool_usage_tracker.py"
move_file "services/security_guardrails.py" "tier-1/platform_services/security_guardrails.py"
echo ""

echo -e "${BLUE}📦 Moving Fine-tuning Services...${NC}"
if [ -d "services/finetuning" ]; then
    # Move entire directory preserving structure
    move_dir "services/finetuning" "tier-1/finetuning_temp"
    # Move GPU resource manager
    move_file "services/gpu_resource_manager.py" "tier-1/finetuning/gpu_resource_manager.py"
    # Note: finetuning directory has complex structure, review manually
    echo -e "${YELLOW}⚠️  Fine-tuning directory moved to tier-1/finetuning_temp/ - review and adjust structure${NC}"
fi
echo ""

echo -e "${BLUE}📦 Moving Evaluation Services...${NC}"
move_file "services/evaluation_service.py" "tier-1/evaluation/evaluation_service.py"
move_file "services/ragas_evaluator.py" "tier-1/evaluation/ragas_evaluator.py"
move_file "services/quality_metrics.py" "tier-1/evaluation/quality_metrics.py"
echo ""

echo -e "${BLUE}📦 Moving Data Extraction Services...${NC}"
move_file "services/template_extraction_service.py" "tier-1/data_extraction/template_extraction_service.py"
move_file "services/template_parser_service.py" "tier-1/data_extraction/template_parser_service.py"
move_file "services/scraper_service.py" "tier-1/data_extraction/scraper_service.py"
move_file "services/scraper_strategies.py" "tier-1/data_extraction/scraper_strategies.py"
move_file "services/scraping_config_service.py" "tier-1/data_extraction/scraping_config_service.py"

if [ -d "services/webscraper" ]; then
    move_dir "services/webscraper" "tier-1/data_extraction/webscraper"
fi
echo ""

echo -e "${BLUE}📦 Moving NLP Processing Services...${NC}"
move_file "services/translation_service.py" "tier-1/nlp_processing/translation_service.py"
move_file "services/complexity_analyzer_service.py" "tier-1/nlp_processing/complexity_analyzer_service.py"
move_file "services/task_complexity_analyzer.py" "tier-1/nlp_processing/task_complexity_analyzer.py"
move_file "services/eda_analyzer.py" "tier-1/nlp_processing/eda_analyzer.py"
move_file "services/multi_analyzer_ensemble.py" "tier-1/nlp_processing/multi_analyzer_ensemble.py"
move_file "services/multi_channel_processor.py" "tier-1/nlp_processing/multi_channel_processor.py"
echo ""

echo -e "${BLUE}📦 Moving Export Services...${NC}"
move_file "services/export_service.py" "tier-1/export/export_service.py"
move_file "services/weights_config_service.py" "tier-1/export/weights_config_service.py"
echo ""

echo -e "${BLUE}📦 Moving CV Processing Services...${NC}"
move_file "services/opencv_measurement_service.py" "tier-1/cv_processing/opencv_measurement_service.py"
echo ""

echo -e "${BLUE}📦 Moving Utility Services...${NC}"
move_file "services/minio_path_builder.py" "tier-1/utilities/minio_path_builder.py"
echo ""

echo "=================================================="
echo -e "${GREEN}✅ File migration COMPLETE${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Review moved files: git status"
echo "2. Check for any remaining files: ls services/"
echo "3. Run script 03: python scripts/migration/03_update_imports.py"
echo ""
