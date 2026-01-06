# Clean Database Installation - SQL Files

**Purpose**: Production-ready SQL files for error-free database installation
**Version**: 1.0
**Date**: 2026-01-05

---

## Overview

This directory contains a complete, tested database schema and seed data exported from a working production instance. These files provide an **error-free alternative** to running migrations, which can fail due to schema evolution issues.

### Why Use This Instead of Migrations?

**Migrations can fail due to**:
- Missing columns in intermediate migration states
- Circular foreign key dependencies
- Schema evolution mismatches
- Seed data inconsistencies

**These SQL files provide**:
- ✅ Complete, tested schema (174KB, 6231 lines)
- ✅ Production-ready seed data (21KB)
- ✅ No migration ordering issues
- ✅ Guaranteed consistency
- ✅ Default admin user (username: admin, password: admin)

---

## Files

| File | Size | Lines | Description |
|------|------|-------|-------------|
| `00_CLEAN_INSTALL_MASTER.sql` | 6.6KB | ~150 | Master script with instructions and admin user creation |
| `01_complete_schema.sql` | 174KB | 6231 | Complete database schema (all tables, types, functions, indexes) |
| `02_essential_data.sql` | 21KB | 181 | Essential seed data (roles, departments, teams, modules, permissions) |

---

## Quick Start

### Option 1: Automated Installation (Recommended)

```bash
# From project root
./scripts/setup/clean-install-database.sh
```

This script will:
1. Check prerequisites
2. Drop and recreate database
3. Install extensions (uuid-ossp, vector)
4. Load complete schema (64 tables)
5. Load seed data (roles, departments, teams, modules)
6. Create admin user
7. Verify installation

**Total time**: ~2 minutes

### Option 2: Manual Installation

```bash
# 1. Drop and recreate database
docker exec rag-postgres psql -U postgres -c "DROP DATABASE IF EXISTS ragchatbot;"
docker exec rag-postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"

# 2. Install extensions
docker exec rag-postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
docker exec rag-postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"vector\";"

# 3. Load schema
docker exec -i rag-postgres psql -U postgres -d ragchatbot < backend/sql/01_complete_schema.sql

# 4. Load seed data (disable triggers for circular FK)
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SET session_replication_role = replica;"
docker exec -i rag-postgres psql -U postgres -d ragchatbot < backend/sql/02_essential_data.sql
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SET session_replication_role = DEFAULT;"

# 5. Create admin user
docker exec rag-postgres psql -U postgres -d ragchatbot << 'EOF'
INSERT INTO users (id, username, email, password_hash, full_name, is_active, is_superuser, created_at, updated_at)
VALUES (
    uuid_generate_v4(),
    'admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY.zQ3QNpZa',
    'System Administrator',
    true,
    true,
    NOW(),
    NOW()
)
ON CONFLICT (username) DO NOTHING;
EOF

# 6. Assign admin role
docker exec rag-postgres psql -U postgres -d ragchatbot << 'EOF'
DO $$
DECLARE
    v_user_id UUID;
    v_role_id UUID;
BEGIN
    SELECT id INTO v_user_id FROM users WHERE username = 'admin';
    SELECT id INTO v_role_id FROM roles WHERE name = 'Admin';
    IF v_user_id IS NOT NULL AND v_role_id IS NOT NULL THEN
        INSERT INTO user_roles (user_id, role_id, assigned_at, assigned_by)
        VALUES (v_user_id, v_role_id, NOW(), v_user_id)
        ON CONFLICT (user_id, role_id) DO NOTHING;
    END IF;
END $$;
EOF
```

---

## What Gets Installed

### Database Structure

- **64 Tables**: All application tables
- **13 Custom Types**: Enums for action_type, user_role, deployment_type, etc.
- **11 Functions**: Helper functions for permissions, updates, caching
- **335+ Indexes**: Including critical vector indexes for RAG
- **113 Foreign Keys**: Complete referential integrity

### Seed Data

**Roles (5)**:
- Admin - Full system access
- CxO - Executive access to analytics and reports
- Manager - Operational access
- User - Standard user access
- ReadOnly - View-only access

**Departments (3)**:
- Data Operations - Data research and operations teams
- Technology - Technology and IT teams
- Support Functions - Support, marketing, sales, and HR

**Teams (28)**:
- Data Operations: 16 teams (AIR Business Distribution, ALF, DMS Construction, DODs, etc.)
- Technology: 10 teams (Backend Development, Frontend Development, ITM1-ITM12)
- Support Functions: 2 teams (Marketing, Sales)

**Modules (26)**:
- Tier 1 (Core): 10 modules (Chat, Upload, Web Scraping, Admin, History, etc.)
- Tier 2 (Domain Verticals): 10 modules (Predictive Analytics, Document Intelligence, etc.)
- Tier 3 (Customer POCs): 6 modules (Construction Monitor, CRU, British Council, etc.)

**Role-Module Permissions**: ~120 permissions mapping roles to modules

### Default Admin User

- **Username**: `admin`
- **Password**: `admin` (bcrypt hashed)
- **Email**: `admin@example.com`
- **Role**: Admin (full access)
- **Superuser**: Yes

⚠️ **SECURITY WARNING**: Change the default password after first login!

---

## Verification

After installation, verify with these queries:

```bash
# Check table count (should be 64+)
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Check roles (should be 5)
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM roles;"

# Check departments (should be 3)
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM departments WHERE is_active = TRUE;"

# Check teams (should be 28)
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM teams WHERE is_active = TRUE;"

# Check modules (should be 26)
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM modules WHERE is_active = TRUE OR is_enabled = TRUE;"

# Check admin user exists
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT username, email, is_superuser FROM users WHERE username = 'admin';"

# Check vector extension
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

**Expected Results**:
```
Tables: 64+
Roles: 5
Departments: 3
Teams: 28
Modules: 26
Users: 1 (admin)
Vector extension: installed
```

---

## Troubleshooting

### Issue: Schema load fails

**Check**: Ensure extensions are installed first
```bash
docker exec rag-postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
docker exec rag-postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"vector\";"
```

### Issue: Data load fails with foreign key errors

**Fix**: Disable triggers temporarily
```bash
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SET session_replication_role = replica;"
# Load data
docker exec -i rag-postgres psql -U postgres -d ragchatbot < backend/sql/02_essential_data.sql
# Re-enable
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SET session_replication_role = DEFAULT;"
```

### Issue: Wrong table/row counts

**Fix**: Regenerate SQL files from working database
```bash
# Export schema
docker exec rag-postgres pg_dump -U postgres -d ragchatbot --schema-only --no-owner --no-acl > backend/sql/01_complete_schema.sql

# Export seed data
docker exec rag-postgres pg_dump -U postgres -d ragchatbot --data-only --no-owner --no-acl -t roles -t departments -t teams -t modules -t role_module_permissions > backend/sql/02_essential_data.sql
```

### Issue: Cannot login with admin credentials

**Fix**: Recreate admin user
```bash
docker exec rag-postgres psql -U postgres -d ragchatbot -c "DELETE FROM users WHERE username = 'admin';"
# Then re-run admin user creation (Step 5 from manual installation)
```

---

## Updating These Files

If the database schema or seed data changes in production:

```bash
# 1. Export updated schema
docker exec rag-postgres pg_dump -U postgres -d ragchatbot \
  --schema-only --no-owner --no-acl \
  > backend/sql/01_complete_schema.sql

# 2. Export updated seed data
docker exec rag-postgres pg_dump -U postgres -d ragchatbot \
  --data-only --no-owner --no-acl \
  -t roles -t departments -t teams -t modules -t role_module_permissions \
  > backend/sql/02_essential_data.sql

# 3. Test on clean database
./scripts/setup/clean-install-database.sh

# 4. Verify all counts match
```

---

## Comparison with Migrations

| Aspect | Migrations (47 files) | Clean SQL Files |
|--------|----------------------|-----------------|
| **Setup Time** | 5-10 minutes | ~2 minutes |
| **Error Rate** | Medium (schema evolution issues) | Low (tested export) |
| **Complexity** | High (order dependencies) | Low (single schema) |
| **Maintenance** | Hard (must update multiple files) | Easy (export from prod) |
| **Debugging** | Difficult (find failing migration) | Easy (single file) |
| **Consistency** | Variable (depends on migration order) | Guaranteed (snapshot) |

**Recommendation**: Use clean SQL files for **fresh installations**. Use migrations for **incremental updates** on existing databases.

---

## Security Notes

### Default Admin Password

The default admin user has password `admin` (hashed with bcrypt).

**Hash**: `$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY.zQ3QNpZa`

**⚠️ CRITICAL**: This is a **known default password**. You MUST change it immediately after first login.

### Change Password After Login

1. Login as `admin` / `admin`
2. Go to Settings → Profile
3. Click "Change Password"
4. Enter new secure password
5. Save

Or via SQL:

```bash
# Generate new bcrypt hash (use a password hashing tool)
NEW_HASH='your_bcrypt_hash_here'

docker exec rag-postgres psql -U postgres -d ragchatbot -c "UPDATE users SET password_hash = '$NEW_HASH' WHERE username = 'admin';"
```

---

## Files Summary

```
backend/sql/
├── README.md                          # This file
├── 00_CLEAN_INSTALL_MASTER.sql       # Master script with admin creation
├── 01_complete_schema.sql            # Complete database schema (174KB)
└── 02_essential_data.sql             # Essential seed data (21KB)
```

**Total Size**: ~200KB

---

## Related Documentation

- [Clean Install Script](../../scripts/setup/clean-install-database.sh) - Automated installation
- [Fresh Installation Guide](../../docs/setup/installation_issues/FRESH_INSTALLATION_COMPLETE_SUMMARY.md)
- [Database Setup Validation](../DB_SETUP_VALIDATION_COMPLETE.md)

---

**Version**: 1.0
**Last Updated**: 2026-01-05
**Status**: ✅ Production Ready
