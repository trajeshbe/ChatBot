-- ============================================================================
-- Seed Roles
-- ============================================================================
--
-- Purpose: Create base RBAC roles
--
-- Roles:
--   - admin      - Full system access, all modules, all permissions
--   - user       - Standard user access, basic modules
--   - analyst    - Data analysis capabilities, read/execute on analytics modules
--   - engineer   - Technical capabilities, access to fine-tuning and tools
--   - guest      - Read-only access, limited to chat and viewing
--
-- Dependencies: roles table
--
-- Idempotent: Yes (ON CONFLICT DO NOTHING)
--
-- ============================================================================

INSERT INTO roles (name, description, is_active, created_at, updated_at)
VALUES
    (
        'admin',
        'Administrator with full system access and all permissions',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'user',
        'Standard user with basic access to chat and document upload',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'analyst',
        'Data analyst with access to analytics and reporting modules',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'engineer',
        'Technical user with access to fine-tuning, tools, and advanced features',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'guest',
        'Read-only guest access with limited module visibility',
        TRUE,
        NOW(),
        NOW()
    )
ON CONFLICT (name) DO NOTHING;

-- Verification
DO $$
DECLARE
    role_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO role_count FROM roles;
    RAISE NOTICE '✓ Roles seeded: % roles (admin, user, analyst, engineer, guest)', role_count;
END
$$;

-- Display seeded roles
SELECT name, description, is_active
FROM roles
ORDER BY
    CASE name
        WHEN 'admin' THEN 1
        WHEN 'engineer' THEN 2
        WHEN 'analyst' THEN 3
        WHEN 'user' THEN 4
        WHEN 'guest' THEN 5
    END;
