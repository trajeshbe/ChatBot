-- ============================================================================
-- Enterprise RAG Chatbot - Master Installation Script
-- ============================================================================
--
-- Purpose:
--   Comprehensive database setup for fresh installations
--   Replaces incremental migration-based approach with single-source setup
--
-- Usage:
--   psql -U postgres -d ragchatbot -f backend/sql/00_CLEAN_INSTALL_MASTER.sql
--
-- Features:
--   - Idempotent (safe to run multiple times)
--   - Dependency-ordered execution
--   - Complete schema + all essential seed data
--   - Production-ready defaults
--
-- Created: 2026-01-07
-- Related: Requirement #9 - Comprehensive Installation Scripts
--
-- ============================================================================

\echo ''
\echo '╔════════════════════════════════════════════════════════════════╗'
\echo '║  Enterprise RAG Chatbot - Clean Database Installation         ║'
\echo '╚════════════════════════════════════════════════════════════════╝'
\echo ''

-- Set client encoding and error handling
\set ON_ERROR_STOP on
\set ECHO queries
SET client_min_messages = WARNING;

-- ============================================================================
-- PRE-FLIGHT CHECKS
-- ============================================================================

\echo ''
\echo '>>> Pre-flight Checks'
\echo ''

-- Verify database
SELECT current_database() AS "Current Database";

-- Check PostgreSQL version (require 12+)
DO $$
BEGIN
    IF (SELECT current_setting('server_version_num')::int < 120000) THEN
        RAISE EXCEPTION 'PostgreSQL 12 or higher required (current: %)', version();
    END IF;
    RAISE NOTICE 'PostgreSQL version: %', version();
END
$$;

\echo ''
\echo '✓ Pre-flight checks passed'
\echo ''

-- ============================================================================
-- STEP 1: Extensions
-- ============================================================================

\echo ''
\echo '>>> [1/13] Installing PostgreSQL Extensions'
\echo ''

\i backend/sql/01_extensions.sql

\echo ''
\echo '✓ Extensions installed'
\echo ''

-- ============================================================================
-- STEP 2: Complete Schema (All 67 Tables)
-- ============================================================================

\echo ''
\echo '>>> [2/13] Creating Complete Database Schema (67 tables)'
\echo ''

\i backend/sql/02_complete_schema.sql

\echo ''
\echo '✓ Schema created'
\echo ''

-- ============================================================================
-- STEP 3: Seed Departments
-- ============================================================================

\echo ''
\echo '>>> [3/13] Seeding Departments (7 departments)'
\echo ''

\i backend/sql/03_seed_departments.sql

\echo ''
\echo '✓ Departments seeded'
\echo ''

-- ============================================================================
-- STEP 4: Seed Teams
-- ============================================================================

\echo ''
\echo '>>> [4/13] Seeding Teams (28 teams)'
\echo ''

\i backend/sql/04_seed_teams.sql

\echo ''
\echo '✓ Teams seeded'
\echo ''

-- ============================================================================
-- STEP 5: Seed Roles
-- ============================================================================

\echo ''
\echo '>>> [5/13] Seeding Roles (5 base roles)'
\echo ''

\i backend/sql/05_seed_roles.sql

\echo ''
\echo '✓ Roles seeded'
\echo ''

-- ============================================================================
-- STEP 6: Seed Admin User
-- ============================================================================

\echo ''
\echo '>>> [6/13] Creating Admin User (admin/admin)'
\echo ''

\i backend/sql/06_seed_admin_user.sql

\echo ''
\echo '✓ Admin user created'
\echo ''

-- ============================================================================
-- STEP 7: Seed Global Project
-- ============================================================================

\echo ''
\echo '>>> [7/13] Creating Global Project (default workspace)'
\echo ''

\i backend/sql/07_seed_global_project.sql

\echo ''
\echo '✓ Global project created'
\echo ''

-- ============================================================================
-- STEP 8: Seed System Configuration
-- ============================================================================

\echo ''
\echo '>>> [8/13] Seeding System Configuration (17 configs)'
\echo ''

\i backend/sql/08_seed_system_config.sql

\echo ''
\echo '✓ System configuration seeded'
\echo ''

-- ============================================================================
-- STEP 9: Seed Models Registry
-- ============================================================================

\echo ''
\echo '>>> [9/13] Seeding Models Registry (17 LLM models)'
\echo ''

\i backend/sql/09_seed_models_registry.sql

\echo ''
\echo '✓ Models registry seeded'
\echo ''

-- ============================================================================
-- STEP 10: Seed Modules
-- ============================================================================

\echo ''
\echo '>>> [10/13] Seeding Modules (36 modules: Tier 1, 2, 3)'
\echo ''

\i backend/sql/10_seed_modules.sql

\echo ''
\echo '✓ Modules seeded'
\echo ''

-- ============================================================================
-- STEP 11: Seed Prompt Library
-- ============================================================================

\echo ''
\echo '>>> [11/13] Seeding Prompt Library (20+ production prompts)'
\echo ''

\i backend/sql/11_seed_prompt_library.sql

\echo ''
\echo '✓ Prompt library seeded'
\echo ''

-- ============================================================================
-- STEP 12: Seed RBAC Permissions
-- ============================================================================

\echo ''
\echo '>>> [12/13] Seeding RBAC Permissions (role-module matrix)'
\echo ''

\i backend/sql/12_seed_rbac_permissions.sql

\echo ''
\echo '✓ RBAC permissions seeded'
\echo ''

-- ============================================================================
-- STEP 13: Create Performance Indexes
-- ============================================================================

\echo ''
\echo '>>> [13/13] Creating Performance Indexes'
\echo ''

\i backend/sql/13_create_indexes.sql

\echo ''
\echo '✓ Indexes created'
\echo ''

-- ============================================================================
-- POST-INSTALLATION VERIFICATION
-- ============================================================================

\echo ''
\echo '╔════════════════════════════════════════════════════════════════╗'
\echo '║  Installation Complete - Verification Summary                  ║'
\echo '╚════════════════════════════════════════════════════════════════╝'
\echo ''

-- Table count
\echo 'Database Tables:'
SELECT COUNT(*) AS "Total Tables"
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- Seed data counts
\echo ''
\echo 'Seed Data Counts:'
SELECT
    'users' AS table_name, COUNT(*) AS count FROM users
UNION ALL SELECT 'departments', COUNT(*) FROM departments
UNION ALL SELECT 'teams', COUNT(*) FROM teams
UNION ALL SELECT 'roles', COUNT(*) FROM roles
UNION ALL SELECT 'projects', COUNT(*) FROM projects
UNION ALL SELECT 'modules', COUNT(*) FROM modules
UNION ALL SELECT 'prompt_library', COUNT(*) FROM prompt_library
UNION ALL SELECT 'system_config', COUNT(*) FROM system_config
UNION ALL SELECT 'models', COUNT(*) FROM models
ORDER BY table_name;

-- Extensions
\echo ''
\echo 'Extensions:'
SELECT extname AS "Extension", extversion AS "Version"
FROM pg_extension
WHERE extname IN ('uuid-ossp', 'vector')
ORDER BY extname;

-- Admin user verification
\echo ''
\echo 'Admin User:'
SELECT
    username,
    email,
    role,
    (SELECT name FROM departments WHERE id = users.department_id) AS department,
    (SELECT name FROM teams WHERE id = users.team_id) AS team,
    is_active
FROM users
WHERE username = 'admin';

-- Global project verification
\echo ''
\echo 'Global Project:'
SELECT
    name,
    project_type,
    embedding_model,
    embedding_dimensions,
    is_default,
    is_active
FROM projects
WHERE name = 'Global';

\echo ''
\echo '╔════════════════════════════════════════════════════════════════╗'
\echo '║  ✓ Installation Successful!                                    ║'
\echo '╚════════════════════════════════════════════════════════════════╝'
\echo ''
\echo 'Next Steps:'
\echo '  1. Restart backend: docker-compose restart backend'
\echo '  2. Access Frontend: http://localhost:3001'
\echo '  3. Login with credentials:'
\echo '     - Username: admin'
\echo '     - Password: admin'
\echo '     - Department: Technology'
\echo '     - Team: ITM11'
\echo ''
\echo 'Verification:'
\echo '  bash scripts/setup/verify-installation.sh'
\echo ''
