#!/usr/bin/env python3
"""
Import Path Updater for Three-Tier Reorganization
Updates all import statements to use new tier-1 structure
"""

import os
import re
from pathlib import Path
from typing import Dict, List

# Comprehensive import mappings
IMPORT_MAPPINGS = {
    # Core Infrastructure
    'from app.core.config': 'from app.tier_1.infrastructure.config',
    'from app.core.database': 'from app.tier_1.infrastructure.database',
    'from app.core.security': 'from app.tier_1.infrastructure.security',
    'import app.core.config': 'import app.tier_1.infrastructure.config',
    'import app.core.database': 'import app.tier_1.infrastructure.database',
    'import app.core.security': 'import app.tier_1.infrastructure.security',

    # LLM Services
    'from app.services.llm_service': 'from app.tier_1.llm.llm_service',
    'from app.services.ollama_model_service': 'from app.tier_1.llm.ollama_model_service',
    'from app.services.ollama_deployment_service': 'from app.tier_1.llm.ollama_deployment_service',
    'from app.services.mcp_server_service': 'from app.tier_1.llm.mcp_server_service',

    # Embedding Services
    'from app.services.embedding_service': 'from app.tier_1.embeddings.embedding_service',
    'from app.services.intelligent_embedding_service': 'from app.tier_1.embeddings.intelligent_embedding_service',
    'from app.services.reranker_service': 'from app.tier_1.embeddings.reranker_service',

    # Document Processing
    'from app.services.document_service': 'from app.tier_1.document_processing.document_service',
    'from app.services.ocr_service': 'from app.tier_1.document_processing.ocr_service',
    'from app.services.vision_service': 'from app.tier_1.document_processing.vision_service',
    'from app.services.hybrid_extraction_service': 'from app.tier_1.document_processing.hybrid_extraction_service',
    'from app.services.content_analyzer': 'from app.tier_1.document_processing.content_analyzer',

    # RAG Services
    'from app.services.rag_service': 'from app.tier_1.rag.rag_service',
    'from app.services.intelligent_retrieval_service': 'from app.tier_1.rag.intelligent_retrieval_service',
    'from app.services.query_reformulation_service': 'from app.tier_1.rag.query_reformulation_service',
    'from app.services.multi_strategy_rag': 'from app.tier_1.rag.multi_strategy_rag',

    # RAG Pipeline
    'from app.rag_pipeline': 'from app.tier_1.rag.pipeline',
    'from app.rag_pipeline.config': 'from app.tier_1.rag.pipeline.config',
    'from app.rag_pipeline.pipeline': 'from app.tier_1.rag.pipeline.pipeline',
    'from app.rag_pipeline.embeddings': 'from app.tier_1.rag.pipeline.embeddings',
    'from app.rag_pipeline.llm': 'from app.tier_1.rag.pipeline.llm',
    'from app.rag_pipeline.retrieval': 'from app.tier_1.rag.pipeline.retrieval',
    'from app.rag_pipeline.reranker': 'from app.tier_1.rag.pipeline.reranker',
    'from app.rag_pipeline.semantic_cache': 'from app.tier_1.rag.pipeline.semantic_cache',
    'from app.rag_pipeline.observability': 'from app.tier_1.rag.pipeline.observability',
    'import app.rag_pipeline': 'import app.tier_1.rag.pipeline',

    # Agents
    'from app.services.agent_service': 'from app.tier_1.agents.agent_service',
    'from app.services.agent_sandbox_manager': 'from app.tier_1.agents.agent_sandbox_manager',
    'from app.services.terminal_session_manager': 'from app.tier_1.agents.terminal_session_manager',
    'from app.services.optimized_state_manager': 'from app.tier_1.agents.optimized_state_manager',
    'from app.services.task_router': 'from app.tier_1.agents.task_router',

    # Agent Engines
    'from app.services.engines': 'from app.tier_1.agents.engines',
    'from app.services.engines.base': 'from app.tier_1.agents.engines.base',
    'from app.services.engines.claude_code_cli_engine': 'from app.tier_1.agents.engines.claude_code_cli_engine',
    'from app.services.engines.codex_cli_engine': 'from app.tier_1.agents.engines.codex_cli_engine',
    'from app.services.engines.default_engine': 'from app.tier_1.agents.engines.default_engine',

    # Platform Services
    'from app.services.auth_service': 'from app.tier_1.platform_services.auth_service',
    'from app.services.rbac_service': 'from app.tier_1.platform_services.rbac_service',
    'from app.services.audit_service': 'from app.tier_1.platform_services.audit_service',
    'from app.services.secrets_service': 'from app.tier_1.platform_services.secrets_service',
    'from app.services.api_usage_tracker': 'from app.tier_1.platform_services.api_usage_tracker',
    'from app.services.tool_usage_tracker': 'from app.tier_1.platform_services.tool_usage_tracker',
    'from app.services.security_guardrails': 'from app.tier_1.platform_services.security_guardrails',

    # Infrastructure Services
    'from app.services.gpu_resource_manager': 'from app.tier_1.infrastructure.gpu_resource_manager',
    'from app.services.minio_path_builder': 'from app.tier_1.infrastructure.minio_path_builder',
    'from app.services.weights_config_service': 'from app.tier_1.infrastructure.weights_config_service',

    # Fine-tuning
    'from app.services.finetuning': 'from app.tier_1.finetuning',
    'from app.services.finetuning.finetuning_service': 'from app.tier_1.finetuning.finetuning_service',
    'from app.services.finetuning.finetuning_sandbox_manager': 'from app.tier_1.finetuning.finetuning_sandbox_manager',
    'from app.services.finetuning.base_trainer': 'from app.tier_1.finetuning.base_trainer',
    'from app.services.finetuning.trainer_factory': 'from app.tier_1.finetuning.trainer_factory',
    'from app.services.finetuning.dataset_preprocessor': 'from app.tier_1.finetuning.dataset_preprocessor',
    'from app.services.finetuning.gpu_pool_manager': 'from app.tier_1.finetuning.gpu_pool_manager',
    'from app.services.finetuning.hyperparameter_tuning_service': 'from app.tier_1.finetuning.hyperparameter_tuning_service',
    'from app.services.finetuning.model_evaluation_service': 'from app.tier_1.finetuning.model_evaluation_service',
    'from app.services.finetuning.model_merge_service': 'from app.tier_1.finetuning.model_merge_service',
    'from app.services.finetuning.model_registry_service': 'from app.tier_1.finetuning.model_registry_service',
    'from app.services.finetuning.training_log_streamer': 'from app.tier_1.finetuning.training_log_streamer',

    # Fine-tuning trainers
    'from app.services.finetuning.trainers': 'from app.tier_1.finetuning.trainers',
    'from app.services.finetuning.trainers.peft_trainer': 'from app.tier_1.finetuning.trainers.peft_trainer',
    'from app.services.finetuning.trainers.rlhf_grpo_trainer': 'from app.tier_1.finetuning.trainers.rlhf_grpo_trainer',
    'from app.services.finetuning.trainers.rlhf_ppo_trainer': 'from app.tier_1.finetuning.trainers.rlhf_ppo_trainer',
    'from app.services.finetuning.trainers.sft_trainer': 'from app.tier_1.finetuning.trainers.sft_trainer',
    'from app.services.finetuning.trainers.unsloth_trainer': 'from app.tier_1.finetuning.trainers.unsloth_trainer',

    # Fine-tuning rewards
    'from app.services.finetuning.rewards': 'from app.tier_1.finetuning.rewards',
    'from app.services.finetuning.rewards.base': 'from app.tier_1.finetuning.rewards.base',
    'from app.services.finetuning.rewards.builtin_rewards': 'from app.tier_1.finetuning.rewards.builtin_rewards',
    'from app.services.finetuning.rewards.calculator': 'from app.tier_1.finetuning.rewards.calculator',
    'from app.services.finetuning.rewards.metrics_emitter': 'from app.tier_1.finetuning.rewards.metrics_emitter',
    'from app.services.finetuning.rewards.utils': 'from app.tier_1.finetuning.rewards.utils',

    # Evaluation
    'from app.services.evaluation_service': 'from app.tier_1.evaluation.evaluation_service',
    'from app.services.ragas_evaluator': 'from app.tier_1.evaluation.ragas_evaluator',
    'from app.services.quality_metrics': 'from app.tier_1.evaluation.quality_metrics',

    # Data Extraction/Scraping
    'from app.services.scraper_service': 'from app.tier_1.data_extraction.scraper_service',
    'from app.services.scraper_strategies': 'from app.tier_1.data_extraction.scraper_strategies',
    'from app.services.template_extraction_service': 'from app.tier_1.data_extraction.template_extraction_service',
    'from app.services.template_parser_service': 'from app.tier_1.data_extraction.template_parser_service',
    'from app.services.scraping_config_service': 'from app.tier_1.data_extraction.scraping_config_service',

    # Web Scraper
    'from app.services.webscraper': 'from app.tier_1.data_extraction.webscraper',

    # NLP Processing
    'from app.services.translation_service': 'from app.tier_1.nlp_processing.translation_service',
    'from app.services.query_classifier': 'from app.tier_1.nlp_processing.query_classifier',
    'from app.services.dynamic_query_classifier': 'from app.tier_1.nlp_processing.dynamic_query_classifier',
    'from app.services.complexity_analyzer_service': 'from app.tier_1.nlp_processing.complexity_analyzer_service',
    'from app.services.task_complexity_analyzer': 'from app.tier_1.nlp_processing.task_complexity_analyzer',
    'from app.services.multi_channel_processor': 'from app.tier_1.nlp_processing.multi_channel_processor',

    # Export
    'from app.services.export_service': 'from app.tier_1.export.export_service',
    'from app.services.project_estimator_service': 'from app.tier_1.export.project_estimator_service',
    'from app.services.multi_analyzer_ensemble': 'from app.tier_1.export.multi_analyzer_ensemble',
    'from app.services.eda_analyzer': 'from app.tier_1.export.eda_analyzer',
    'from app.services.project_estimator': 'from app.tier_1.export.project_estimator',

    # CV Processing
    'from app.services.opencv_measurement_service': 'from app.tier_1.cv_processing.opencv_measurement_service',
}


def update_imports_in_file(file_path: Path) -> bool:
    """Update import statements in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
        return False

    original = content

    # Apply all import mappings
    for old_import, new_import in IMPORT_MAPPINGS.items():
        content = content.replace(old_import, new_import)

    # Check if any changes were made
    if content != original:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
        except Exception as e:
            print(f"⚠️  Error writing {file_path}: {e}")
            return False

    return False


def main():
    """Main execution function"""
    print("=" * 80)
    print("Three-Tier Reorganization: Import Path Updater")
    print("=" * 80)
    print()

    backend_path = Path("backend/app")

    if not backend_path.exists():
        print(f"❌ Error: Backend path not found: {backend_path}")
        print("   Please run this script from the project root directory")
        return 1

    # Collect all Python files (excluding tier-1 since those are the moved files)
    files_to_update: List[Path] = []

    # API routes
    files_to_update.extend(backend_path.glob("api/**/*.py"))

    # Tasks
    files_to_update.extend(backend_path.glob("tasks/**/*.py"))

    # Models
    files_to_update.extend(backend_path.glob("models/**/*.py"))

    # Schemas
    files_to_update.extend(backend_path.glob("schemas/**/*.py"))

    # Agents (not in tier-1)
    files_to_update.extend(backend_path.glob("agents/**/*.py"))

    # Middleware
    files_to_update.extend(backend_path.glob("middleware/**/*.py"))

    # MCP
    files_to_update.extend(backend_path.glob("mcp/**/*.py"))

    # Metrics
    files_to_update.extend(backend_path.glob("metrics/**/*.py"))

    # Tools
    files_to_update.extend(backend_path.glob("tools/**/*.py"))

    # Utils
    files_to_update.extend(backend_path.glob("utils/**/*.py"))

    # Main entry points
    files_to_update.extend(backend_path.glob("main*.py"))

    # Root __init__.py
    if (backend_path / "__init__.py").exists():
        files_to_update.append(backend_path / "__init__.py")

    # Also update test files
    tests_path = Path("backend/tests")
    if tests_path.exists():
        files_to_update.extend(tests_path.glob("**/*.py"))

    print(f"📁 Found {len(files_to_update)} Python files to scan")
    print()

    updated_count = 0
    for file_path in files_to_update:
        # Skip tier-1, tier-2, tier-3 directories (those are the moved files)
        if "tier-1" in str(file_path) or "tier-2" in str(file_path) or "tier-3" in str(file_path):
            continue

        if update_imports_in_file(file_path):
            updated_count += 1

    print()
    print("=" * 80)
    print(f"✅ Import update complete!")
    print(f"   Files scanned: {len(files_to_update)}")
    print(f"   Files updated: {updated_count}")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Verify imports: python -m compileall backend/app")
    print("2. Run tests: pytest backend/tests/")
    print("3. Build Docker: docker-compose build backend")
    print()

    return 0


if __name__ == "__main__":
    exit(main())
