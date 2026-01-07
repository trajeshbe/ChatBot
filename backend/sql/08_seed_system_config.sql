-- ============================================================================
-- Seed System Configuration
-- ============================================================================
--
-- Purpose: Seed database-driven system configuration
--
-- Configuration Categories:
--   - agent: Agent runtime settings
--   - embedding: Embedding model configuration
--   - ollama: Ollama integration settings
--   - prefect: Prefect workflow orchestration
--   - rag: Retrieval-Augmented Generation settings
--
-- Total Configurations: 17
--
-- Dependencies: system_config table
--
-- Idempotent: Yes (ON CONFLICT DO UPDATE)
--
-- Related: Phase 1 - Requirement #8 (Agent Runtime API from DB)
--
-- ============================================================================

-- Insert system configuration values
INSERT INTO system_config (config_key, config_value, config_type, category, description, is_active, created_at, updated_at) VALUES

-- ============================================================================
-- Agent Runtime Configuration
-- ============================================================================
(
    'agent.runtime.default_model',
    'qwen2.5-coder:7b',
    'string',
    'agent',
    'Default LLM model for agent runtime tasks',
    TRUE,
    NOW(),
    NOW()
),
(
    'agent.runtime.api_base_url',
    'http://ollama:11434',
    'url',
    'agent',
    'Agent runtime API base URL (Ollama endpoint)',
    TRUE,
    NOW(),
    NOW()
),
(
    'agent.runtime.max_iterations',
    '15',
    'integer',
    'agent',
    'Default max iterations for agent tasks',
    TRUE,
    NOW(),
    NOW()
),
(
    'agent.runtime.timeout_seconds',
    '300',
    'integer',
    'agent',
    'Default timeout for agent tasks (seconds)',
    TRUE,
    NOW(),
    NOW()
),

-- ============================================================================
-- Embedding Configuration
-- ============================================================================
(
    'embedding.default_provider',
    'sentence-transformers',
    'string',
    'embedding',
    'Default embedding provider',
    TRUE,
    NOW(),
    NOW()
),
(
    'embedding.default_model',
    'sentence-transformers/all-MiniLM-L6-v2',
    'string',
    'embedding',
    'Default embedding model',
    TRUE,
    NOW(),
    NOW()
),
(
    'embedding.default_dimensions',
    '384',
    'integer',
    'embedding',
    'Default embedding dimensions',
    TRUE,
    NOW(),
    NOW()
),
(
    'embedding.cache_enabled',
    'true',
    'boolean',
    'embedding',
    'Enable Redis embedding cache',
    TRUE,
    NOW(),
    NOW()
),
(
    'embedding.batch_size',
    '32',
    'integer',
    'embedding',
    'Batch size for embedding generation',
    TRUE,
    NOW(),
    NOW()
),

-- ============================================================================
-- Ollama Auto-Discovery Configuration
-- ============================================================================
(
    'ollama.auto_discovery_enabled',
    'true',
    'boolean',
    'ollama',
    'Auto-discover Ollama models and register in UI',
    TRUE,
    NOW(),
    NOW()
),
(
    'ollama.sync_interval_seconds',
    '300',
    'integer',
    'ollama',
    'Interval for Ollama model sync (seconds, default 5 minutes)',
    TRUE,
    NOW(),
    NOW()
),
(
    'ollama.api_base_url',
    'http://ollama:11434',
    'url',
    'ollama',
    'Ollama API base URL for model management',
    TRUE,
    NOW(),
    NOW()
),

-- ============================================================================
-- Prefect Configuration
-- ============================================================================
(
    'prefect.database_schema',
    'prefect',
    'string',
    'prefect',
    'PostgreSQL schema for Prefect tables (database consolidation)',
    TRUE,
    NOW(),
    NOW()
),
(
    'prefect.api_url',
    'http://prefect-server:4200',
    'url',
    'prefect',
    'Prefect Server API URL',
    TRUE,
    NOW(),
    NOW()
),
(
    'prefect.enabled',
    'true',
    'boolean',
    'prefect',
    'Enable Prefect workflow orchestration',
    TRUE,
    NOW(),
    NOW()
),

-- ============================================================================
-- RAG Configuration
-- ============================================================================
(
    'rag.top_k_results',
    '5',
    'integer',
    'rag',
    'Default number of documents to retrieve in RAG queries',
    TRUE,
    NOW(),
    NOW()
),
(
    'rag.similarity_threshold',
    '0.7',
    'float',
    'rag',
    'Minimum cosine similarity score for document retrieval (0.0-1.0)',
    TRUE,
    NOW(),
    NOW()
),
(
    'rag.max_context_length',
    '4000',
    'integer',
    'rag',
    'Maximum context length in tokens for RAG responses',
    TRUE,
    NOW(),
    NOW()
)

ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    config_type = EXCLUDED.config_type,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Verification
DO $$
DECLARE
    config_count INTEGER;
    agent_count INTEGER;
    embedding_count INTEGER;
    ollama_count INTEGER;
    prefect_count INTEGER;
    rag_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO config_count FROM system_config WHERE is_active = TRUE;
    SELECT COUNT(*) INTO agent_count FROM system_config WHERE category = 'agent';
    SELECT COUNT(*) INTO embedding_count FROM system_config WHERE category = 'embedding';
    SELECT COUNT(*) INTO ollama_count FROM system_config WHERE category = 'ollama';
    SELECT COUNT(*) INTO prefect_count FROM system_config WHERE category = 'prefect';
    SELECT COUNT(*) INTO rag_count FROM system_config WHERE category = 'rag';

    RAISE NOTICE '';
    RAISE NOTICE '✓ System Configuration Seeded:';
    RAISE NOTICE '  Total active configs: %', config_count;
    RAISE NOTICE '  - Agent configs: %', agent_count;
    RAISE NOTICE '  - Embedding configs: %', embedding_count;
    RAISE NOTICE '  - Ollama configs: %', ollama_count;
    RAISE NOTICE '  - Prefect configs: %', prefect_count;
    RAISE NOTICE '  - RAG configs: %', rag_count;
    RAISE NOTICE '';
END
$$;

-- Display all configurations
SELECT
    category,
    config_key,
    config_value,
    config_type,
    is_active
FROM system_config
WHERE is_active = TRUE
ORDER BY category, config_key;
