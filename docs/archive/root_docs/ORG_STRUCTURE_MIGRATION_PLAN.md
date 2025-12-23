# Organizational Structure Migration Plan

**Date**: 2025-12-20
**Source**: `org_structure/org.xlsx`
**Status**: ✅ Phase 1 Complete - Admin assigned to ITM11

---

## Current State Analysis

### From org.xlsx

**Divisions** (3):
1. Technology
2. Data Operations
3. Support Functions

**Technology Teams** (7):
- ITM1, ITM2, ITM6, ITM7, ITM9, ITM10, ITM12
- ❌ **ITM11 does NOT exist in org.xlsx!**

**Data Operations Teams** (16):
- Air Business Distribution, ALF, DMS Construction Data Research, DODs, Glenigan FRO, HSJ, HSJ On Medica, Haymarket, Informa Connect - Data Research, LLI Data, Leadership, Leadscale, Political Engagement - Research Support, Quality, Tactical Data, Tactical Data Research

**Support Functions Teams** (2):
- Marketing, Sales

---

## Current Database State

### Departments (Should be Divisions)

```sql
SELECT id, name FROM departments WHERE name IN ('Technology', 'Data Operations', 'Support Functions');

-- Results:
id: 9375d67f-3d0c-4e6f-8e84-ac99cb65641d  | Technology
id: 0f4c1f28-a193-4075-907c-0a5916f2b62f  | Data Operations
id: 11561e77-c20a-41da-8910-543b3d2f390b  | Support Functions
```

✅ **Divisions exist with correct names**

### Teams

```sql
SELECT name, department_id FROM teams WHERE department_id = '9375d67f-3d0c-4e6f-8e84-ac99cb65641d';

-- Results:
Backend Development (custom team, not in org.xlsx)
Frontend Development (custom team, not in org.xlsx)
```

❌ **Technology teams use custom names, not ITM1-ITM12**

### Admin User

```sql
SELECT username, department.name, team.name
FROM users
WHERE username = 'admin';

-- Results:
admin | Technology | Backend Development
```

❌ **Admin is in "Backend Development" (should be ITM11)**

---

## Issues Identified

| Issue | Current | Expected | Priority |
|-------|---------|----------|----------|
| Terminology | "Department" | "Division" | P2 (Optional) |
| ITM11 Team | Does not exist | Must exist for admin | P0 (Critical) |
| Team Names | "Backend Development", "Team 1-12" | ITM1, ITM2, ITM6, ITM7, ITM9, ITM10, ITM12 | P1 (Important) |
| Admin Team | Backend Development | ITM11 | P0 (Critical) |

---

## Migration Strategy

### Option A: Add ITM11 and Update Admin (Minimal Change)

**Pros**:
- Minimal disruption
- Only affects admin user
- No data migration needed

**Steps**:
1. Create ITM11 team under Technology division
2. Update admin user to belong to ITM11
3. Keep existing teams intact

**Cons**:
- Doesn't align with org.xlsx fully
- Mixed naming conventions (ITM11 + Backend Development)

### Option B: Full Org Structure Alignment (Recommended)

**Pros**:
- Perfect alignment with org.xlsx
- Consistent team naming
- Future-proof

**Steps**:
1. Create all teams from org.xlsx
2. Map existing users to correct teams
3. Update admin to ITM11
4. Optionally rename Department → Division

**Cons**:
- More complex migration
- Need to map existing users

---

## Recommended Approach

**Phase 1 (Immediate)**:
1. ✅ Create ITM11 team
2. ✅ Assign admin to ITM11
3. ✅ Keep "Department" terminology (add view/alias for "Division")

**Phase 2 (Optional)**:
1. Create all teams from org.xlsx
2. Add migration mapping for existing users
3. Rename tables/columns for Division terminology

---

## Implementation (Phase 1)

### SQL Migration Script

```sql
BEGIN;

-- 1. Get Technology division ID
DO $$
DECLARE
    tech_div_id UUID;
    itm11_team_id UUID;
    admin_user_id UUID;
    backend_team_id UUID;
BEGIN
    -- Get Technology division
    SELECT id INTO tech_div_id
    FROM departments
    WHERE name = 'Technology';

    IF tech_div_id IS NULL THEN
        RAISE EXCEPTION 'Technology division not found';
    END IF;

    RAISE NOTICE 'Technology division ID: %', tech_div_id;

    -- 2. Create ITM11 team (if doesn't exist)
    INSERT INTO teams (id, name, department_id, created_at)
    VALUES (
        gen_random_uuid(),
        'ITM11',
        tech_div_id,
        NOW()
    )
    ON CONFLICT (name, department_id) DO NOTHING
    RETURNING id INTO itm11_team_id;

    -- Get ITM11 ID if it already existed
    IF itm11_team_id IS NULL THEN
        SELECT id INTO itm11_team_id
        FROM teams
        WHERE name = 'ITM11' AND department_id = tech_div_id;
    END IF;

    RAISE NOTICE 'ITM11 team ID: %', itm11_team_id;

    -- 3. Get admin user ID
    SELECT id INTO admin_user_id
    FROM users
    WHERE username = 'admin';

    IF admin_user_id IS NULL THEN
        RAISE EXCEPTION 'Admin user not found';
    END IF;

    RAISE NOTICE 'Admin user ID: %', admin_user_id;

    -- 4. Get current Backend Development team ID
    SELECT id INTO backend_team_id
    FROM teams
    WHERE name = 'Backend Development' AND department_id = tech_div_id;

    RAISE NOTICE 'Backend Development team ID: %', backend_team_id;

    -- 5. Remove admin from Backend Development team
    IF backend_team_id IS NOT NULL THEN
        DELETE FROM user_teams
        WHERE user_id = admin_user_id
        AND team_id = backend_team_id;

        RAISE NOTICE 'Removed admin from Backend Development';
    END IF;

    -- 6. Add admin to ITM11 team
    INSERT INTO user_teams (id, user_id, team_id, is_primary, created_at)
    VALUES (
        gen_random_uuid(),
        admin_user_id,
        itm11_team_id,
        TRUE,  -- Primary team
        NOW()
    )
    ON CONFLICT (user_id, team_id) DO UPDATE
    SET is_primary = TRUE;

    RAISE NOTICE '✅ Admin assigned to ITM11 as primary team';

END $$;

-- 7. Create view for Division terminology (optional)
CREATE OR REPLACE VIEW divisions AS
SELECT id, name, description, created_at
FROM departments;

-- Verify changes
SELECT
    u.username,
    d.name as division,
    t.name as team,
    ut.is_primary
FROM users u
LEFT JOIN departments d ON u.department_id = d.id
LEFT JOIN user_teams ut ON u.id = ut.user_id
LEFT JOIN teams t ON ut.team_id = t.id
WHERE u.username = 'admin';

COMMIT;
```

### Verification Query

```sql
-- Verify admin user assignment
SELECT
    u.username,
    d.name as division,
    t.name as team,
    ut.is_primary as is_primary_team
FROM users u
LEFT JOIN departments d ON u.department_id = d.id
LEFT JOIN user_teams ut ON u.id = ut.user_id
LEFT JOIN teams t ON ut.team_id = t.id
WHERE u.username = 'admin';

-- Expected Result:
-- username | division   | team  | is_primary_team
-- admin    | Technology | ITM11 | t
```

---

## MinIO Path Impact

### Before Migration

```
Technology/Backend-Development/global/admin/documents/file.pdf
```

### After Migration

```
technology/itm11/global/admin/documents/file.pdf
```

**Note**: All path components will be lowercase due to the fix we just implemented!

---

## Testing Checklist

- [x] ITM11 team created in Technology department (code: ITM11)
- [x] Admin user assigned to ITM11 team as primary
- [x] Admin user removed from Backend Development team
- [x] MinIO path builder generates correct path: `technology/itm11/global/admin/documents/test.pdf`
- [x] Database queries use correct team name and code
- [ ] RBAC permissions still work for admin (needs UI testing)
- [ ] No breaking changes to existing functionality (needs UI testing)

---

## Rollback Plan

```sql
-- Rollback: Move admin back to Backend Development
BEGIN;

UPDATE user_teams ut
SET team_id = (SELECT id FROM teams WHERE name = 'Backend Development')
WHERE user_id = (SELECT id FROM users WHERE username = 'admin')
AND team_id = (SELECT id FROM teams WHERE name = 'ITM11');

-- Optionally delete ITM11 if no other users
DELETE FROM teams WHERE name = 'ITM11'
AND id NOT IN (SELECT team_id FROM user_teams);

COMMIT;
```

---

## Phase 2: Full Org Structure Sync (Future)

### Create All Teams from org.xlsx

```python
import pandas as pd

file_path = "org_structure/org.xlsx"
xls = pd.ExcelFile(file_path)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    division_name = sheet_name  # Sheet name is the division
    teams = df['Team Name'].dropna().unique()

    for team_name in teams:
        print(f"INSERT INTO teams (id, name, department_id) ")
        print(f"VALUES (gen_random_uuid(), '{team_name}', ")
        print(f"  (SELECT id FROM departments WHERE name = '{division_name}'));")
```

This will generate SQL for all 25 teams across 3 divisions.

---

## Conclusion

**Immediate Action** (Phase 1):
1. Create ITM11 team
2. Assign admin to ITM11
3. Create divisions view for terminology

**Future Action** (Phase 2):
1. Create all teams from org.xlsx
2. Map users to correct teams
3. Full migration script

**Status**: ✅ Phase 1 COMPLETE - Admin in ITM11, MinIO paths verified

---

**Last Updated**: 2025-12-20
**Created By**: Claude Code AI Assistant
