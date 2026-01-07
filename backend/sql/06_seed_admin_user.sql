-- ============================================================================
-- Seed Admin User
-- ============================================================================
--
-- Purpose: Create default admin user for fresh installations
--
-- Admin User Details:
--   Username: admin
--   Password: admin (hashed with bcrypt)
--   Email: admin@example.com
--   Department: Technology (TECH)
--   Team: ITM11
--   Role: admin
--
-- Dependencies:
--   - departments table (Technology department)
--   - teams table (ITM11 team)
--   - roles table (admin role)
--   - users table
--
-- Idempotent: Yes (checks for existing admin user)
--
-- Security Note:
--   ⚠️  CHANGE PASSWORD IN PRODUCTION!
--   This is a default password for initial setup only.
--
-- ============================================================================

DO $$
DECLARE
    tech_dept_id UUID;
    itm11_team_id UUID;
    admin_role_id UUID;
    admin_user_id UUID;
    existing_admin UUID;
BEGIN
    -- ========================================================================
    -- Step 1: Verify dependencies exist
    -- ========================================================================

    -- Get Technology department ID
    SELECT id INTO tech_dept_id FROM departments WHERE code = 'TECH';
    IF tech_dept_id IS NULL THEN
        RAISE EXCEPTION 'Technology department not found. Run 03_seed_departments.sql first.';
    END IF;

    -- Get ITM11 team ID
    SELECT id INTO itm11_team_id FROM teams WHERE code = 'ITM11' AND department_id = tech_dept_id;
    IF itm11_team_id IS NULL THEN
        RAISE EXCEPTION 'ITM11 team not found. Run 04_seed_teams.sql first.';
    END IF;

    -- Get admin role ID
    SELECT id INTO admin_role_id FROM roles WHERE name = 'admin';
    IF admin_role_id IS NULL THEN
        RAISE EXCEPTION 'Admin role not found. Run 05_seed_roles.sql first.';
    END IF;

    -- ========================================================================
    -- Step 2: Check if admin user already exists
    -- ========================================================================

    SELECT id INTO existing_admin FROM users WHERE username = 'admin';

    IF existing_admin IS NOT NULL THEN
        RAISE NOTICE '⚠ Admin user already exists (id: %), skipping creation', existing_admin;
        RETURN;
    END IF;

    -- ========================================================================
    -- Step 3: Create admin user
    -- ========================================================================

    -- Insert admin user
    -- Password: "admin" hashed with bcrypt (rounds=12)
    -- Hash generated with: python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('admin'))"
    INSERT INTO users (
        username,
        email,
        password_hash,
        role,
        department_id,
        team_id,
        is_active,
        created_at,
        updated_at
    ) VALUES (
        'admin',
        'admin@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LezvpFQ5vz1vEI1tG',  -- password: admin
        'admin',
        tech_dept_id,
        itm11_team_id,
        TRUE,
        NOW(),
        NOW()
    )
    RETURNING id INTO admin_user_id;

    RAISE NOTICE '✓ Admin user created (id: %)', admin_user_id;

    -- ========================================================================
    -- Step 4: Assign admin role via user_roles junction table
    -- ========================================================================

    INSERT INTO user_roles (
        id,
        user_id,
        role_id,
        assigned_at,
        assigned_by
    ) VALUES (
        uuid_generate_v4(),
        admin_user_id,
        admin_role_id,
        NOW(),
        admin_user_id  -- Self-assigned during setup
    );

    RAISE NOTICE '✓ Admin role assigned to admin user';

    -- ========================================================================
    -- Step 5: Assign to ITM11 team via user_teams junction table
    -- ========================================================================

    INSERT INTO user_teams (
        id,
        user_id,
        team_id,
        is_primary,
        assigned_at,
        assigned_by
    ) VALUES (
        uuid_generate_v4(),
        admin_user_id,
        itm11_team_id,
        TRUE,  -- Primary team
        NOW(),
        admin_user_id  -- Self-assigned during setup
    );

    RAISE NOTICE '✓ Admin user assigned to ITM11 team (primary)';

    -- ========================================================================
    -- Verification Summary
    -- ========================================================================

    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║  Admin User Created Successfully                       ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';
    RAISE NOTICE 'Login Credentials:';
    RAISE NOTICE '  Username: admin';
    RAISE NOTICE '  Password: admin';
    RAISE NOTICE '  Email: admin@example.com';
    RAISE NOTICE '';
    RAISE NOTICE 'Organization:';
    RAISE NOTICE '  Department: Technology (TECH)';
    RAISE NOTICE '  Team: ITM11';
    RAISE NOTICE '  Role: admin';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  SECURITY WARNING:';
    RAISE NOTICE '  Default password "admin" is NOT secure!';
    RAISE NOTICE '  Change password immediately in production:';
    RAISE NOTICE '    UPDATE users SET password_hash = <new_hash> WHERE username = ''admin'';';
    RAISE NOTICE '';
END
$$;

-- Display admin user details
SELECT
    u.username,
    u.email,
    u.role,
    d.name AS department,
    t.name AS team,
    u.is_active,
    u.created_at
FROM users u
LEFT JOIN departments d ON u.department_id = d.id
LEFT JOIN teams t ON u.team_id = t.id
WHERE u.username = 'admin';
