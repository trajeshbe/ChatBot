-- ============================================================================
-- Seed Models Registry
-- ============================================================================
--
-- Purpose: Seed unified LLM models registry with popular models
--
-- Model Providers:
--   - Ollama (8 models): Code, Text, Vision models
--   - OpenAI (6 models): GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5 Turbo, O1, O1 Mini
--   - Anthropic (3 models): Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus
--
-- Total Models: 17
--
-- Dependencies: models table
--
-- Idempotent: Yes (ON CONFLICT DO UPDATE)
--
-- Related: Phase 1 - Requirement #2 (Ollama Auto-Registration)
--
-- Note: Ollama models will be auto-discovered and updated by the
--       Model Registry Sync Service in production.
--
-- ============================================================================

-- ============================================================================
-- Ollama Models (8 models)
-- ============================================================================

-- Code Models (3)
INSERT INTO models (
    model_id,
    display_name,
    provider,
    model_type,
    context_length,
    max_tokens,
    supports_functions,
    supports_vision,
    is_default,
    is_active,
    source,
    created_at,
    updated_at
) VALUES
(
    'qwen2.5-coder:7b',
    'Qwen 2.5 Coder 7B',
    'ollama',
    'code',
    32768,
    8192,
    FALSE,
    FALSE,
    TRUE,  -- Default model for agent tasks
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'codellama:7b',
    'CodeLlama 7B',
    'ollama',
    'code',
    16384,
    4096,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'deepseek-coder:6.7b',
    'DeepSeek Coder 6.7B',
    'ollama',
    'code',
    16384,
    4096,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    'manual',
    NOW(),
    NOW()
),

-- Text Models (3)
(
    'llama3.2:3b',
    'Llama 3.2 3B',
    'ollama',
    'text',
    128000,
    8192,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'mistral:7b',
    'Mistral 7B',
    'ollama',
    'text',
    32768,
    8192,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'phi3:mini',
    'Phi-3 Mini',
    'ollama',
    'text',
    128000,
    4096,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    'manual',
    NOW(),
    NOW()
),

-- Vision Models (2)
(
    'llava:7b',
    'LLaVA 7B',
    'ollama',
    'vision',
    4096,
    2048,
    FALSE,
    TRUE,
    FALSE,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'bakllava:7b',
    'BakLLaVA 7B',
    'ollama',
    'vision',
    4096,
    2048,
    FALSE,
    TRUE,
    FALSE,
    TRUE,
    'manual',
    NOW(),
    NOW()
)

ON CONFLICT (model_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    provider = EXCLUDED.provider,
    model_type = EXCLUDED.model_type,
    context_length = EXCLUDED.context_length,
    max_tokens = EXCLUDED.max_tokens,
    supports_functions = EXCLUDED.supports_functions,
    supports_vision = EXCLUDED.supports_vision,
    is_default = EXCLUDED.is_default,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- ============================================================================
-- OpenAI Models (6 models)
-- ============================================================================

INSERT INTO models (
    model_id,
    display_name,
    provider,
    model_type,
    context_length,
    max_tokens,
    supports_functions,
    supports_vision,
    supports_streaming,
    cost_per_1k_input,
    cost_per_1k_output,
    is_active,
    source,
    created_at,
    updated_at
) VALUES
(
    'gpt-4o',
    'GPT-4o',
    'openai',
    'multimodal',
    128000,
    16384,
    TRUE,
    TRUE,
    TRUE,
    0.00250,
    0.01000,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'gpt-4o-mini',
    'GPT-4o Mini',
    'openai',
    'multimodal',
    128000,
    16384,
    TRUE,
    TRUE,
    TRUE,
    0.00015,
    0.00060,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'gpt-4-turbo',
    'GPT-4 Turbo',
    'openai',
    'multimodal',
    128000,
    4096,
    TRUE,
    TRUE,
    TRUE,
    0.01000,
    0.03000,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'gpt-3.5-turbo',
    'GPT-3.5 Turbo',
    'openai',
    'text',
    16385,
    4096,
    TRUE,
    FALSE,
    TRUE,
    0.00050,
    0.00150,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'o1',
    'O1',
    'openai',
    'text',
    200000,
    100000,
    FALSE,
    FALSE,
    FALSE,
    0.01500,
    0.06000,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'o1-mini',
    'O1 Mini',
    'openai',
    'text',
    128000,
    65536,
    FALSE,
    FALSE,
    FALSE,
    0.00300,
    0.01200,
    TRUE,
    'manual',
    NOW(),
    NOW()
)

ON CONFLICT (model_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    context_length = EXCLUDED.context_length,
    max_tokens = EXCLUDED.max_tokens,
    supports_functions = EXCLUDED.supports_functions,
    supports_vision = EXCLUDED.supports_vision,
    supports_streaming = EXCLUDED.supports_streaming,
    cost_per_1k_input = EXCLUDED.cost_per_1k_input,
    cost_per_1k_output = EXCLUDED.cost_per_1k_output,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- ============================================================================
-- Anthropic Models (3 models)
-- ============================================================================

INSERT INTO models (
    model_id,
    display_name,
    provider,
    model_type,
    context_length,
    max_tokens,
    supports_functions,
    supports_vision,
    supports_streaming,
    cost_per_1k_input,
    cost_per_1k_output,
    is_active,
    source,
    created_at,
    updated_at
) VALUES
(
    'claude-3-5-sonnet-20241022',
    'Claude 3.5 Sonnet',
    'anthropic',
    'multimodal',
    200000,
    8192,
    TRUE,
    TRUE,
    TRUE,
    0.00300,
    0.01500,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'claude-3-5-haiku-20241022',
    'Claude 3.5 Haiku',
    'anthropic',
    'text',
    200000,
    8192,
    TRUE,
    FALSE,
    TRUE,
    0.00080,
    0.00400,
    TRUE,
    'manual',
    NOW(),
    NOW()
),
(
    'claude-3-opus-20240229',
    'Claude 3 Opus',
    'anthropic',
    'multimodal',
    200000,
    4096,
    TRUE,
    TRUE,
    TRUE,
    0.01500,
    0.07500,
    TRUE,
    'manual',
    NOW(),
    NOW()
)

ON CONFLICT (model_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    context_length = EXCLUDED.context_length,
    max_tokens = EXCLUDED.max_tokens,
    supports_functions = EXCLUDED.supports_functions,
    supports_vision = EXCLUDED.supports_vision,
    supports_streaming = EXCLUDED.supports_streaming,
    cost_per_1k_input = EXCLUDED.cost_per_1k_input,
    cost_per_1k_output = EXCLUDED.cost_per_1k_output,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    total_count INTEGER;
    ollama_count INTEGER;
    openai_count INTEGER;
    anthropic_count INTEGER;
    code_count INTEGER;
    text_count INTEGER;
    vision_count INTEGER;
    multimodal_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM models WHERE is_active = TRUE;
    SELECT COUNT(*) INTO ollama_count FROM models WHERE provider = 'ollama' AND is_active = TRUE;
    SELECT COUNT(*) INTO openai_count FROM models WHERE provider = 'openai' AND is_active = TRUE;
    SELECT COUNT(*) INTO anthropic_count FROM models WHERE provider = 'anthropic' AND is_active = TRUE;
    SELECT COUNT(*) INTO code_count FROM models WHERE model_type = 'code' AND is_active = TRUE;
    SELECT COUNT(*) INTO text_count FROM models WHERE model_type = 'text' AND is_active = TRUE;
    SELECT COUNT(*) INTO vision_count FROM models WHERE model_type = 'vision' AND is_active = TRUE;
    SELECT COUNT(*) INTO multimodal_count FROM models WHERE model_type = 'multimodal' AND is_active = TRUE;

    RAISE NOTICE '';
    RAISE NOTICE '✓ Models Registry Seeded:';
    RAISE NOTICE '  Total active models: %', total_count;
    RAISE NOTICE '';
    RAISE NOTICE '  By Provider:';
    RAISE NOTICE '    - Ollama: % models', ollama_count;
    RAISE NOTICE '    - OpenAI: % models', openai_count;
    RAISE NOTICE '    - Anthropic: % models', anthropic_count;
    RAISE NOTICE '';
    RAISE NOTICE '  By Type:';
    RAISE NOTICE '    - Code: % models', code_count;
    RAISE NOTICE '    - Text: % models', text_count;
    RAISE NOTICE '    - Vision: % models', vision_count;
    RAISE NOTICE '    - Multimodal: % models', multimodal_count;
    RAISE NOTICE '';
END
$$;

-- Display all models
SELECT
    provider,
    model_type,
    model_id,
    display_name,
    context_length,
    is_default,
    CASE
        WHEN cost_per_1k_input = 0 OR cost_per_1k_input IS NULL THEN 'Free'
        WHEN cost_per_1k_input < 0.001 THEN 'Very Low'
        WHEN cost_per_1k_input < 0.005 THEN 'Low'
        WHEN cost_per_1k_input < 0.015 THEN 'Medium'
        ELSE 'High'
    END AS cost_tier
FROM models
WHERE is_active = TRUE
ORDER BY provider, model_type, display_name;
