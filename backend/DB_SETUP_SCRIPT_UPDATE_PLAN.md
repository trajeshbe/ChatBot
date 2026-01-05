# Database Setup Script Update Plan

**Date**: 2026-01-05
**Target Script**: `/scripts/setup/setup-database-complete-FIXED.sh` (v3.0)
**Purpose**: Update FIXED script to include production seed data corrections

---

## Executive Summary

**Current Status**: ✅ Analysis Complete | ✅ Supplemental Migrations Created | ⏳ Script Update Pending

**Key Findings**:
- Original FIXED script applies all 47 migrations correctly ✅
- **CRITICAL ISSUE**: Seed data in migrations does NOT match production state ❌
- **Solution**: Created 4 supplemental migrations (900-903) to fix seed data
- **Impact**: Without these updates, fresh installs will have wrong departments, teams, and incomplete permissions

**Files Created**:
1. `DB_SEED_DATA_ANALYSIS.md` - Comprehensive 13-section analysis document
2. `900_update_departments_to_production.sql` - Fix department structure (7 → 3 departments)
3. `901_update_teams_to_production.sql` - Replace generic teams with actual business units (28 teams)
4. `902_migrate_modules_schema.sql` - Migrate core modules to new schema (10 modules)
5. `903_seed_tier2_tier3_permissions.sql` - Add missing role-module permissions (16 modules)

---

## Phase Insertion Points in FIXED Script

### Current FIXED Script Structure (12 Phases)

The script currently processes migrations in 12 logical phases. The 4 new migrations should be inserted as follows:

```bash
# PHASE 1: Foundation (8 migrations) ✅
# PHASE 2: RBAC & Organization (5 migrations) ✅
# PHASE 3: Audit Enhancements (2 migrations) ✅
# PHASE 4: Projects & Modules (11 migrations) ✅
# PHASE 5: Agent Tasks (2 migrations) ✅
# PHASE 6: Schema Fixes (5 migrations) ✅
# PHASE 7: Evaluation System (2 migrations) ✅
# PHASE 8: Fine-Tuning System (6 migrations) ✅
# PHASE 9: Tier 2/3 Modules (2 migrations) ✅
# PHASE 10: Dynamic Configuration (1 migration) ✅
# PHASE 11: Export Wizard (1 migration) ✅
# PHASE 12: Additional Features (2 migrations) ✅

# 🆕 PHASE 13: Production Seed Data Corrections (NEW - 4 migrations)
#    - 900_update_departments_to_production.sql
#    - 901_update_teams_to_production.sql
#    - 902_migrate_modules_schema.sql
#    - 903_seed_tier2_tier3_permissions.sql
```

**Reasoning**: These migrations must run AFTER all table structures are created (phases 1-12) because they update seed data that was inserted by earlier migrations.

---

## Detailed Update Instructions

### Step 1: Add New Phase to FIXED Script

Insert after line ~850 (after PHASE 12 completion), before final verification section:

```bash
# ============================================================================
# PHASE 13: Production Seed Data Corrections
# ============================================================================
# Purpose: Update seed data to match current production state
# - Fix department structure (3 departments instead of 7)
# - Replace generic team names with actual business units
# - Migrate core modules to new schema format
# - Add missing role-module permissions for Tier 2/3 modules
# ============================================================================

echo ""
echo "============================================================"
echo "PHASE 13: Production Seed Data Corrections"
echo "============================================================"
echo ""

PHASE_13_MIGRATIONS=(
    "900_update_departments_to_production.sql"
    "901_update_teams_to_production.sql"
    "902_migrate_modules_schema.sql"
    "903_seed_tier2_tier3_permissions.sql"
)

for migration in "${PHASE_13_MIGRATIONS[@]}"; do
    migration_path="$MIGRATIONS_DIR/$migration"

    if [[ ! -f "$migration_path" ]]; then
        echo "❌ ERROR: Migration file not found: $migration"
        echo "   Expected at: $migration_path"
        exit 1
    fi

    echo "→ Applying $migration..."
    if ! psql -U "$DB_USER" -d "$DB_NAME" -f "$migration_path" > /dev/null 2>&1; then
        echo "❌ ERROR: Failed to apply $migration"
        echo "   This migration fixes production seed data"
        echo "   Run: psql -U $DB_USER -d $DB_NAME -f $migration_path"
        exit 1
    fi
    echo "✅ Applied: $migration"
done

echo ""
echo "✅ PHASE 13 Complete: Production seed data corrected"
echo ""
```

### Step 2: Update Total Migration Count

Update line ~40 (version info):

```bash
# FIXED Script v4.0 - Now includes production seed data corrections
# Total migrations: 51 (47 original + 4 production seed data corrections)
```

### Step 3: Update Verification Section

Update the verification section (around line ~900) to check for production state:

```bash
echo "============================================================"
echo "Verification: Database Structure and Seed Data"
echo "============================================================"
echo ""

# Verify table count
TABLE_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
echo "✓ Tables created: $TABLE_COUNT (expected: 64+)"

# Verify roles
ROLE_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM roles;")
echo "✓ Roles created: $ROLE_COUNT (expected: 5)"

# 🆕 Verify production departments
DEPT_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM departments WHERE is_active = TRUE;")
echo "✓ Active departments: $DEPT_COUNT (expected: 3)"

if [[ "$DEPT_COUNT" -ne 3 ]]; then
    echo "⚠️  WARNING: Expected 3 active departments, found $DEPT_COUNT"
    echo "   Production expects: Data Operations, Technology, Support Functions"
fi

# 🆕 Verify production teams
TEAM_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM teams WHERE is_active = TRUE;")
echo "✓ Active teams: $TEAM_COUNT (expected: 28)"

if [[ "$TEAM_COUNT" -ne 28 ]]; then
    echo "⚠️  WARNING: Expected 28 active teams, found $TEAM_COUNT"
fi

# Verify modules
MODULE_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM modules WHERE is_active = TRUE OR is_enabled = TRUE;")
echo "✓ Modules created: $MODULE_COUNT (expected: 26)"

if [[ "$MODULE_COUNT" -ne 26 ]]; then
    echo "⚠️  WARNING: Expected 26 active modules, found $MODULE_COUNT"
fi

# 🆕 Verify role-module permissions coverage
echo ""
echo "Role-Module Permissions Summary:"
psql -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT
    r.name || ': ' || COUNT(DISTINCT m.id) || ' modules' as permission_summary
FROM roles r
LEFT JOIN role_module_permissions rmp ON r.id = rmp.role_id
LEFT JOIN modules m ON rmp.module_id = m.id
GROUP BY r.name
ORDER BY r.name;
"

echo ""
echo "Expected:"
echo "  Admin: 26 modules (full access)"
echo "  CxO: ~24 modules"
echo "  Manager: ~24 modules"
echo "  User: ~15 modules"
echo "  ReadOnly: ~24 modules"
```

### Step 4: Add Production State Verification Function

Add new function after existing helper functions (around line ~150):

```bash
# ============================================================================
# Function: Verify Production State
# ============================================================================
verify_production_state() {
    echo ""
    echo "============================================================"
    echo "Production State Verification"
    echo "============================================================"
    echo ""

    # Check departments
    echo "→ Checking department structure..."
    DEPT_NAMES=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT name FROM departments WHERE is_active = TRUE ORDER BY name;")
    EXPECTED_DEPTS=("Data Operations" "Support Functions" "Technology")

    for dept in "${EXPECTED_DEPTS[@]}"; do
        if echo "$DEPT_NAMES" | grep -q "$dept"; then
            echo "  ✓ Found: $dept"
        else
            echo "  ❌ MISSING: $dept"
            return 1
        fi
    done

    # Check team distribution
    echo ""
    echo "→ Checking team distribution..."
    psql -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT
        d.name || ': ' || COUNT(t.id) || ' teams' as distribution
    FROM departments d
    LEFT JOIN teams t ON d.id = t.department_id AND t.is_active = TRUE
    WHERE d.is_active = TRUE
    GROUP BY d.name
    ORDER BY d.name;
    "

    # Check module tiers
    echo ""
    echo "→ Checking module tier distribution..."
    psql -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT
        CASE
            WHEN tier IS NULL THEN 'Tier 1 (Core)'
            WHEN tier = 2 THEN 'Tier 2 (Verticals)'
            WHEN tier = 3 THEN 'Tier 3 (POCs)'
        END || ': ' || COUNT(*) || ' modules' as tier_distribution
    FROM modules
    WHERE is_active = TRUE OR is_enabled = TRUE
    GROUP BY tier
    ORDER BY tier NULLS FIRST;
    "

    echo ""
    echo "✅ Production state verification complete"
    echo ""
}
```

Then call this function at the end of the script (before success message):

```bash
# Run production state verification
verify_production_state

echo ""
echo "============================================================"
echo "✅ Database Setup Complete - Production Ready"
echo "============================================================"
```

---

## Testing Checklist

After updating the FIXED script, test on a clean database:

### Pre-Test Setup
```bash
# Backup current database (if exists)
pg_dump -U postgres -d ragchatbot > backup_before_test.sql

# Drop and recreate database
psql -U postgres -c "DROP DATABASE IF EXISTS ragchatbot;"
psql -U postgres -c "CREATE DATABASE ragchatbot;"
```

### Run Updated Script
```bash
cd /path/to/scripts/setup
./setup-database-complete-FIXED.sh
```

### Post-Test Verification

Run these SQL queries to verify production state:

```sql
-- 1. Verify 3 active departments
SELECT name, description FROM departments WHERE is_active = TRUE ORDER BY name;
-- Expected: Data Operations, Support Functions, Technology

-- 2. Verify 28 active teams
SELECT d.name as department, COUNT(t.id) as team_count, string_agg(t.name, ', ') as teams
FROM departments d
LEFT JOIN teams t ON d.id = t.department_id AND t.is_active = TRUE
WHERE d.is_active = TRUE
GROUP BY d.name;
-- Expected: Data Operations (16), Support Functions (2), Technology (10)

-- 3. Verify 26 modules
SELECT tier, COUNT(*) as count FROM modules
WHERE is_active = TRUE OR is_enabled = TRUE
GROUP BY tier ORDER BY tier NULLS FIRST;
-- Expected: NULL/1 (10), 2 (10), 3 (6)

-- 4. Verify role-module permissions
SELECT r.name, COUNT(DISTINCT m.id) as modules_with_access
FROM roles r
LEFT JOIN role_module_permissions rmp ON r.id = rmp.role_id
LEFT JOIN modules m ON rmp.module_id = m.id
GROUP BY r.name ORDER BY r.name;
-- Expected: Admin (26), CxO (~24), Manager (~24), User (~15), ReadOnly (~24)

-- 5. Verify specific module permissions
SELECT r.name as role, m.module_name, rmp.can_read, rmp.can_write
FROM role_module_permissions rmp
JOIN roles r ON rmp.role_id = r.id
JOIN modules m ON rmp.module_id = m.id
WHERE m.tier = 3  -- Check Tier 3 POC modules
ORDER BY r.name, m.module_name;
-- Verify Tier 3 modules have appropriate role permissions
```

### Expected Test Results

✅ **All 51 migrations applied successfully** (47 + 4 new)
✅ **64 tables created**
✅ **5 roles with proper descriptions**
✅ **3 active departments** (Data Operations, Support Functions, Technology)
✅ **28 active teams** with actual business unit names
✅ **26 modules** (10 Tier 1, 10 Tier 2, 6 Tier 3)
✅ **Complete role-module permissions** for all 26 modules
✅ **113 foreign key constraints**
✅ **335 indexes**

---

## Rollback Plan

If updated script fails, rollback steps:

```bash
# 1. Stop any running processes
docker-compose down

# 2. Restore from backup
psql -U postgres -c "DROP DATABASE IF EXISTS ragchatbot;"
psql -U postgres -c "CREATE DATABASE ragchatbot;"
psql -U postgres -d ragchatbot < backup_before_test.sql

# 3. Revert FIXED script to v3.0
git checkout scripts/setup/setup-database-complete-FIXED.sh

# 4. Restart services
docker-compose up -d
```

---

## Migration Order Reference

Complete execution order for all 51 migrations:

**PHASE 1: Foundation**
1. 000_base_schema.sql
2. 001_add_rbac_and_audit.sql
3. 002_fix_embedding_dimensions.sql
4. 003_fix_query_cache_default.sql
5. 004_add_api_credentials.sql
6. 004_add_scraping_configs.sql
7. 004_add_saved_css_templates.sql
8. 005_add_tool_usage_tracking.sql

**PHASE 2: RBAC & Organization**
9. 006_add_modules_and_projects.sql
10. 006_add_rbac_tables.sql
11. 007_seed_rbac_data.sql ← Seeds initial roles, departments, modules
12. 008_normalize_departments_teams.sql ← Creates 7 departments + 33 generic teams
13. 008_update_department_structure.sql

**PHASE 3-12**: [... existing migrations 14-47 ...]

**🆕 PHASE 13: Production Seed Data Corrections**
48. 900_update_departments_to_production.sql ← Fix to 3 departments
49. 901_update_teams_to_production.sql ← Replace with 28 actual team names
50. 902_migrate_modules_schema.sql ← Migrate core modules to new schema
51. 903_seed_tier2_tier3_permissions.sql ← Add Tier 2/3 permissions

---

## Files Modified

### New Files Created:
- `backend/migrations/900_update_departments_to_production.sql`
- `backend/migrations/901_update_teams_to_production.sql`
- `backend/migrations/902_migrate_modules_schema.sql`
- `backend/migrations/903_seed_tier2_tier3_permissions.sql`
- `backend/DB_SEED_DATA_ANALYSIS.md` (analysis document)
- `backend/DB_SETUP_SCRIPT_UPDATE_PLAN.md` (this document)

### Files to be Modified:
- `scripts/setup/setup-database-complete-FIXED.sh` (update from v3.0 to v4.0)

### Files for Reference:
- `backend/migrations/007_seed_rbac_data.sql` (original seed data)
- `backend/migrations/008_normalize_departments_teams.sql` (generic teams)
- `backend/migrations/024_add_modules_management.sql` (Tier 2/3 modules)

---

## Summary of Changes

| Component | Before (v3.0) | After (v4.0) | Impact |
|-----------|---------------|--------------|--------|
| **Total Migrations** | 47 | 51 (+4) | Complete |
| **Departments** | 7 (generic) | 3 (production) | CRITICAL |
| **Teams** | 33 (generic "Team 1", "Team 2") | 28 (actual business units) | HIGH |
| **Modules** | 26 (schema mismatch) | 26 (unified schema) | MEDIUM |
| **Role-Module Permissions** | 45 (Tier 1 only) | ~120 (all tiers) | HIGH |
| **Production Ready** | ❌ NO | ✅ YES | CRITICAL |

---

## Next Steps

1. ✅ **Review this plan** - Ensure all changes are understood
2. ⏳ **Update FIXED script** - Apply changes outlined in Step 1-4
3. ⏳ **Test on clean database** - Run full test cycle
4. ⏳ **Verify production state** - Run all verification queries
5. ⏳ **Update documentation** - Mark v4.0 as production-ready
6. ⏳ **Commit changes** - Commit updated script and new migrations

---

**Status**: ✅ Plan Complete - Ready for Implementation
**Estimated Time to Implement**: 30-45 minutes
**Risk Level**: LOW (changes are additive, original migrations unchanged)
**Rollback Available**: YES (via backup and git)

