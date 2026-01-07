-- ============================================================================
-- Seed Global Project
-- ============================================================================
--
-- Purpose: Create default "Global" project for all users
--
-- Global Project Details:
--   Name: Global
--   Type: shared
--   Default Embedding: sentence-transformers/all-MiniLM-L6-v2
--   Dimensions: 384
--   Owner: admin user
--   Default: Yes (is_default = TRUE)
--
-- Dependencies:
--   - projects table
--   - users table (admin user must exist)
--
-- Idempotent: Yes (checks for existing Global project)
--
-- Related: Requirement #5 - Default Global Project
--
-- ============================================================================

DO $$
DECLARE
    admin_user_id UUID;
    existing_project UUID;
    global_project_id UUID;
BEGIN
    -- ========================================================================
    -- Step 1: Get admin user ID
    -- ========================================================================

    SELECT id INTO admin_user_id FROM users WHERE username = 'admin';

    IF admin_user_id IS NULL THEN
        RAISE EXCEPTION 'Admin user not found. Run 06_seed_admin_user.sql first.';
    END IF;

    -- ========================================================================
    -- Step 2: Check if Global project already exists
    -- ========================================================================

    SELECT id INTO existing_project FROM projects WHERE name = 'Global';

    IF existing_project IS NOT NULL THEN
        RAISE NOTICE '⚠ Global project already exists (id: %), skipping creation', existing_project;

        -- Ensure it's marked as default
        UPDATE projects
        SET is_default = TRUE, is_active = TRUE
        WHERE id = existing_project;

        RAISE NOTICE '✓ Global project verified as default';
        RETURN;
    END IF;

    -- ========================================================================
    -- Step 3: Create Global project
    -- ========================================================================

    INSERT INTO projects (
        name,
        description,
        project_type,
        owner_id,
        embedding_model,
        embedding_dimensions,
        embedding_provider,
        embedding_use_case,
        similarity_threshold,
        top_k_results,
        is_default,
        is_active,
        created_at,
        updated_at
    ) VALUES (
        'Global',
        'Default project for all users. Shared workspace for general-purpose document processing and chat.',
        'shared',
        admin_user_id,
        'sentence-transformers/all-MiniLM-L6-v2',  -- Default embedding model
        384,                                         -- Embedding dimensions
        'sentence-transformers',                     -- Provider
        'general_text',                              -- Use case
        0.7,                                         -- Similarity threshold
        5,                                           -- Top K results
        TRUE,                                        -- Is default
        TRUE,                                        -- Is active
        NOW(),
        NOW()
    )
    RETURNING id INTO global_project_id;

    RAISE NOTICE '✓ Global project created (id: %)', global_project_id;

    -- ========================================================================
    -- Step 4: Add admin as project member
    -- ========================================================================

    INSERT INTO project_members (
        id,
        project_id,
        user_id,
        role,
        joined_at
    ) VALUES (
        uuid_generate_v4(),
        global_project_id,
        admin_user_id,
        'owner',
        NOW()
    );

    RAISE NOTICE '✓ Admin user added as Global project owner';

    -- ========================================================================
    -- Verification Summary
    -- ========================================================================

    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║  Global Project Created Successfully                   ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';
    RAISE NOTICE 'Project Details:';
    RAISE NOTICE '  Name: Global';
    RAISE NOTICE '  Type: shared';
    RAISE NOTICE '  Owner: admin';
    RAISE NOTICE '  Default: Yes';
    RAISE NOTICE '';
    RAISE NOTICE 'Embedding Configuration:';
    RAISE NOTICE '  Model: sentence-transformers/all-MiniLM-L6-v2';
    RAISE NOTICE '  Dimensions: 384';
    RAISE NOTICE '  Provider: sentence-transformers';
    RAISE NOTICE '  Use Case: general_text';
    RAISE NOTICE '';
    RAISE NOTICE 'RAG Settings:';
    RAISE NOTICE '  Similarity Threshold: 0.7';
    RAISE NOTICE '  Top K Results: 5';
    RAISE NOTICE '';
END
$$;

-- Display Global project details
SELECT
    p.name,
    p.description,
    p.project_type,
    u.username AS owner,
    p.embedding_model,
    p.embedding_dimensions,
    p.is_default,
    p.is_active,
    p.created_at
FROM projects p
LEFT JOIN users u ON p.owner_id = u.id
WHERE p.name = 'Global';
