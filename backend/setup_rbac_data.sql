-- ========================================
-- RBAC Data Setup Script
-- Creates Teams, Users, and Assignments
-- ========================================

-- Get department IDs for reference
DO $$
DECLARE
    dept_enterprise UUID;
    dept_data_ops UUID;
    dept_technology UUID;
    dept_marketing UUID;
    dept_finance UUID;
    dept_hr UUID;

    role_admin UUID;
    role_cxo UUID;
    role_manager UUID;
    role_user UUID;
    role_readonly UUID;

    user_admin UUID;
    user_ceo UUID;
    user_cto UUID;
    user_manager1 UUID;
    user_manager2 UUID;
    user_analyst1 UUID;
    user_analyst2 UUID;
    user_dev1 UUID;
    user_dev2 UUID;
    user_viewer UUID;

    team_exec UUID;
    team_data_eng UUID;
    team_data_sci UUID;
    team_backend UUID;
    team_frontend UUID;
    team_marketing UUID;
BEGIN
    -- Get department IDs
    SELECT id INTO dept_enterprise FROM departments WHERE name = 'Enterprise' LIMIT 1;
    SELECT id INTO dept_data_ops FROM departments WHERE name = 'Data Operations' LIMIT 1;
    SELECT id INTO dept_technology FROM departments WHERE name = 'Technology' LIMIT 1;
    SELECT id INTO dept_marketing FROM departments WHERE name = 'Marketing' LIMIT 1;
    SELECT id INTO dept_finance FROM departments WHERE name = 'Finance' LIMIT 1;
    SELECT id INTO dept_hr FROM departments WHERE name = 'HR' LIMIT 1;

    -- Get role IDs
    SELECT id INTO role_admin FROM roles WHERE name = 'Admin';
    SELECT id INTO role_cxo FROM roles WHERE name = 'CxO';
    SELECT id INTO role_manager FROM roles WHERE name = 'Manager';
    SELECT id INTO role_user FROM roles WHERE name = 'User';
    SELECT id INTO role_readonly FROM roles WHERE name = 'ReadOnly';

    -- ========================================
    -- 1. CREATE TEAMS
    -- ========================================

    -- Executive Team
    team_exec := gen_random_uuid();
    INSERT INTO teams (id, name, code, description, department_id, is_active)
    VALUES (team_exec, 'Executive Team', 'EXEC', 'C-level executives and senior leadership', dept_enterprise, true);

    -- Data Engineering Team
    team_data_eng := gen_random_uuid();
    INSERT INTO teams (id, name, code, description, department_id, is_active)
    VALUES (team_data_eng, 'Data Engineering Team', 'DATA-ENG', 'Data pipeline and infrastructure development', dept_data_ops, true);

    -- Data Science Team
    team_data_sci := gen_random_uuid();
    INSERT INTO teams (id, name, code, description, department_id, is_active)
    VALUES (team_data_sci, 'Data Science Team', 'DATA-SCI', 'Analytics, ML, and AI development', dept_data_ops, true);

    -- Backend Development Team
    team_backend := gen_random_uuid();
    INSERT INTO teams (id, name, code, description, department_id, is_active)
    VALUES (team_backend, 'Backend Development', 'BACKEND', 'API and server-side development', dept_technology, true);

    -- Frontend Development Team
    team_frontend := gen_random_uuid();
    INSERT INTO teams (id, name, code, description, department_id, is_active)
    VALUES (team_frontend, 'Frontend Development', 'FRONTEND', 'UI/UX and client-side development', dept_technology, true);

    -- Marketing Analytics Team
    team_marketing := gen_random_uuid();
    INSERT INTO teams (id, name, code, description, department_id, is_active)
    VALUES (team_marketing, 'Marketing Analytics', 'MKT-ANALYTICS', 'Marketing data analysis and reporting', dept_marketing, true);

    RAISE NOTICE '✅ Created 6 teams';

    -- ========================================
    -- 2. CREATE USERS
    -- ========================================

    -- Get existing admin user
    SELECT id INTO user_admin FROM users WHERE username = 'admin';

    -- CEO (CxO role)
    INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified, department_id)
    VALUES (
        'ceo',
        'ceo@example.com',
        'Chief Executive Officer',
        '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin'
        'admin', -- Using admin enum value for CxO
        true,
        true,
        dept_enterprise
    )
    RETURNING id INTO user_ceo;

    -- CTO (Manager role)
    INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified, department_id)
    VALUES (
        'cto',
        'cto@example.com',
        'Chief Technology Officer',
        '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin'
        'admin',
        true,
        true,
        dept_technology
    )
    RETURNING id INTO user_cto;

    -- Data Engineering Manager
    INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified, department_id)
    VALUES (
        'data_manager',
        'data.manager@example.com',
        'Sarah Johnson - Data Engineering Manager',
        '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin'
        'user',
        true,
        true,
        dept_data_ops
    )
    RETURNING id INTO user_manager1;

    -- Marketing Manager
    INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified, department_id)
    VALUES (
        'marketing_manager',
        'marketing.manager@example.com',
        'Michael Chen - Marketing Manager',
        '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin'
        'user',
        true,
        true,
        dept_marketing
    )
    RETURNING id INTO user_manager2;

    -- Data Analyst 1
    INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified, department_id)
    VALUES (
        'analyst1',
        'analyst1@example.com',
        'Emma Davis - Senior Data Analyst',
        '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin'
        'user',
        true,
        true,
        dept_data_ops
    )
    RETURNING id INTO user_analyst1;

    -- Data Analyst 2
    INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified, department_id)
    VALUES (
        'analyst2',
        'analyst2@example.com',
        'James Wilson - Data Analyst',
        '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin'
        'user',
        true,
        true,
        dept_data_ops
    )
    RETURNING id INTO user_analyst2;

    -- Backend Developer
    INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified, department_id)
    VALUES (
        'backend_dev',
        'backend.dev@example.com',
        'Alex Rodriguez - Backend Developer',
        '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin'
        'user',
        true,
        true,
        dept_technology
    )
    RETURNING id INTO user_dev1;

    -- Frontend Developer
    INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified, department_id)
    VALUES (
        'frontend_dev',
        'frontend.dev@example.com',
        'Lisa Anderson - Frontend Developer',
        '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin'
        'user',
        true,
        true,
        dept_technology
    )
    RETURNING id INTO user_dev2;

    -- Read-Only User
    INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified, department_id)
    VALUES (
        'viewer',
        'viewer@example.com',
        'Guest Viewer',
        '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin'
        'viewer',
        true,
        true,
        dept_enterprise
    )
    RETURNING id INTO user_viewer;

    RAISE NOTICE '✅ Created 9 new users (10 total including admin)';

    -- ========================================
    -- 3. ASSIGN USERS TO TEAMS
    -- ========================================

    -- Executive Team
    INSERT INTO user_teams (id, user_id, team_id, is_primary) VALUES (gen_random_uuid(), user_ceo, team_exec, true);
    INSERT INTO user_teams (id, user_id, team_id, is_primary) VALUES (gen_random_uuid(), user_cto, team_exec, false);

    -- Data Engineering Team
    INSERT INTO user_teams (id, user_id, team_id, is_primary) VALUES (gen_random_uuid(), user_manager1, team_data_eng, true);
    INSERT INTO user_teams (id, user_id, team_id, is_primary) VALUES (gen_random_uuid(), user_analyst1, team_data_eng, true);

    -- Data Science Team
    INSERT INTO user_teams (id, user_id, team_id, is_primary) VALUES (gen_random_uuid(), user_analyst2, team_data_sci, true);

    -- Backend Development Team
    INSERT INTO user_teams (id, user_id, team_id, is_primary) VALUES (gen_random_uuid(), user_cto, team_backend, true);
    INSERT INTO user_teams (id, user_id, team_id, is_primary) VALUES (gen_random_uuid(), user_dev1, team_backend, true);

    -- Frontend Development Team
    INSERT INTO user_teams (id, user_id, team_id, is_primary) VALUES (gen_random_uuid(), user_dev2, team_frontend, true);

    -- Marketing Analytics Team
    INSERT INTO user_teams (id, user_id, team_id, is_primary) VALUES (gen_random_uuid(), user_manager2, team_marketing, true);

    RAISE NOTICE '✅ Assigned users to teams';

    -- ========================================
    -- 4. ASSIGN ROLES TO USERS
    -- ========================================

    -- Admin role
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_admin, role_admin);

    -- CxO roles
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_ceo, role_cxo);
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_cto, role_cxo);

    -- Manager roles
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_manager1, role_manager);
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_manager2, role_manager);

    -- User roles
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_analyst1, role_user);
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_analyst2, role_user);
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_dev1, role_user);
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_dev2, role_user);

    -- Read-Only role
    INSERT INTO user_roles (id, user_id, role_id) VALUES (gen_random_uuid(), user_viewer, role_readonly);

    RAISE NOTICE '✅ Assigned roles to users';

    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ RBAC Setup Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Summary:';
    RAISE NOTICE '  - Departments: 35 (from migrations)';
    RAISE NOTICE '  - Teams: 6';
    RAISE NOTICE '  - Roles: 5';
    RAISE NOTICE '  - Users: 10';
    RAISE NOTICE '';
    RAISE NOTICE 'Login Credentials (all use password: admin):';
    RAISE NOTICE '  - admin / admin (System Admin)';
    RAISE NOTICE '  - ceo / admin (CEO - Executive)';
    RAISE NOTICE '  - cto / admin (CTO - Technology)';
    RAISE NOTICE '  - data_manager / admin (Data Engineering Manager)';
    RAISE NOTICE '  - marketing_manager / admin (Marketing Manager)';
    RAISE NOTICE '  - analyst1 / admin (Senior Data Analyst)';
    RAISE NOTICE '  - analyst2 / admin (Data Analyst)';
    RAISE NOTICE '  - backend_dev / admin (Backend Developer)';
    RAISE NOTICE '  - frontend_dev / admin (Frontend Developer)';
    RAISE NOTICE '  - viewer / admin (Read-Only User)';
    RAISE NOTICE '========================================';
END $$;
