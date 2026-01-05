-- Migration 902: Migrate Core Modules to New Schema
-- Created: 2026-01-05
-- Purpose: Update 10 core modules from old schema (name, code) to new schema (module_key, module_name, tier, category)
-- Dependencies: 007_seed_rbac_data.sql, 024_add_modules_management.sql

BEGIN;

-- ============================================================================
-- STEP 1: Check if modules table has new schema columns
-- ============================================================================
DO $$
BEGIN
    -- Add module_key if it doesn't exist (from old 'code' column)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'modules' AND column_name = 'module_key') THEN
        -- This should already exist from 024_add_modules_management.sql
        RAISE NOTICE 'module_key column does not exist - schema migration may not have run';
    END IF;
END $$;

-- ============================================================================
-- STEP 2: Migrate old core modules to new schema format
-- ============================================================================
-- Update existing core modules with new schema fields
UPDATE modules SET
    module_key = 'chat',
    module_name = 'Chat',
    tier = NULL,
    category = NULL,
    module_type = NULL
WHERE module_name = 'RAG Chat' OR (module_key = 'rag_chat' AND tier IS NULL);

UPDATE modules SET
    module_key = 'upload',
    module_name = 'Upload Files'
WHERE module_name = 'File Upload' OR (module_key = 'file_upload' AND tier IS NULL);

UPDATE modules SET
    module_key = 'scrape',
    module_name = 'Web Scraping'
WHERE module_name = 'Web Scraping' OR (module_key = 'web_scraping' AND tier IS NULL);

UPDATE modules SET
    module_key = 'estimator',
    module_name = 'Project Estimator'
WHERE module_name = 'Project Estimator' OR (module_key = 'project_estimator' AND tier IS NULL);

UPDATE modules SET
    module_key = 'evaluation',
    module_name = 'Evaluation'
WHERE module_name = 'Evaluation Metrics' OR (module_key = 'evaluation' AND tier IS NULL);

UPDATE modules SET
    module_key = 'tools',
    module_name = 'Tool Usage'
WHERE module_name = 'Tool Usage Dashboard' OR (module_key = 'tools_dashboard' AND tier IS NULL);

UPDATE modules SET
    module_key = 'weights',
    module_name = 'Weights Config'
WHERE module_name = 'Weights Configuration' OR (module_key = 'weights_config' AND tier IS NULL);

UPDATE modules SET
    module_key = 'admin',
    module_name = 'Admin'
WHERE module_name = 'Admin Panel' OR (module_key = 'admin_panel' AND tier IS NULL);

UPDATE modules SET
    module_key = 'history',
    module_name = 'Chat History'
WHERE module_key = 'history' OR module_name = 'Chat History';

UPDATE modules SET
    module_key = 'model_finetuning',
    module_name = 'Fine-Tuning'
WHERE module_key = 'model_finetuning' OR module_name = 'Fine-Tuning' OR module_name = 'Model Fine-tuning';

-- ============================================================================
-- STEP 3: Verify module count
-- ============================================================================
SELECT
    COALESCE(tier, 0) as tier_level,
    CASE
        WHEN tier IS NULL THEN 'Tier 1 (Core)'
        WHEN tier = 2 THEN 'Tier 2 (Domain Verticals)'
        WHEN tier = 3 THEN 'Tier 3 (Customer POCs)'
    END as tier_name,
    COUNT(*) as module_count
FROM modules
WHERE is_enabled = TRUE OR is_active = TRUE
GROUP BY tier
ORDER BY tier NULLS FIRST;

COMMIT;

-- Expected result:
-- Tier 1 (Core): 10 modules
-- Tier 2 (Domain Verticals): 10 modules
-- Tier 3 (Customer POCs): 6 modules
-- Total: 26 modules
