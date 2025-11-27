# RBAC Integration Strategy - Backward Compatible

**Date**: 2025-11-27
**Status**: 📋 PLANNING
**Goal**: Enhance existing system WITHOUT breaking it

---

## 🎯 Strategy: Enhance, Don't Replace

### Current Situation Analysis

**Existing:**
- ✅ `users` table with simple role enum (admin, user, viewer, api_user)
- ✅ `chat_sessions` table with user tracking
- ✅ `session_documents` for short-term memory
- ✅ `api_keys` for programmatic access
- ✅ User model in `database_enhanced.py`

**Our RBAC:**
- 🆕 `roles` table (more flexible than enum)
- 🆕 `departments` table (organizational structure)
- 🆕 `modules` table (feature permissions)
- 🆕 `role_module_permissions` table
- 🆕 `user_roles` table (many-to-many)

---

## ✅ Integration Approach

### Option 1: Gradual Migration (RECOMMENDED)

**Phase 1: Add New Tables (Non-Breaking)**
- ✅ Add RBAC tables alongside existing User table
- ✅ Keep existing `users.role` enum column
- ✅ New `user_roles` table for enhanced RBAC
- ✅ Both systems work in parallel

**Phase 2: Sync During Transition**
- Map old enum roles to new Role records
- When user has enum role, auto-create user_roles entry
- Queries check both old and new systems

**Phase 3: Gradual Deprecation**
- New users only use RBAC system
- Existing users migrate on next login
- Eventually remove enum column (later)

### Benefits:
- ✅ Zero downtime
- ✅ Existing code keeps working
- ✅ Can rollback easily
- ✅ Test thoroughly before full switch

---

## 🔧 Modified Migration Plan

### Migration 006 - ENHANCED (Non-Breaking)

```sql
-- DON'T modify existing users table
-- ADD new tables that extend it

-- Create roles table (maps to existing enum values initially)
CREATE TABLE roles (...);

-- Seed roles that match existing enum
INSERT INTO roles (name) VALUES
    ('admin'),   -- matches UserRole.ADMIN
    ('user'),    -- matches UserRole.USER
    ('viewer'),  -- matches UserRole.VIEWER
    ('api_user'); -- matches UserRole.API_USER

-- Add our enhanced roles
INSERT INTO roles (name) VALUES
    ('CxO'),
    ('Manager'),
    ('ReadOnly');

-- Rest of RBAC tables...
```

### Migration 007 - Sync Existing Users

```sql
-- Auto-create user_roles entries for existing users
-- based on their current users.role enum value

INSERT INTO user_roles (user_id, role_id, assigned_at)
SELECT
    u.id,
    r.id,
    NOW()
FROM users u
JOIN roles r ON LOWER(r.name) = LOWER(u.role::text)
WHERE NOT EXISTS (
    -- Don't duplicate if already assigned
    SELECT 1 FROM user_roles ur
    WHERE ur.user_id = u.id AND ur.role_id = r.id
);
```

---

## 🔄 Code Integration Points

### 1. Update User Model (Backward Compatible)

**File**: `backend/app/models/database_enhanced.py`

```python
from app.models.rbac import UserRole as RBACUserRole

class User(Base):
    __tablename__ = "users"

    # Keep existing enum for backward compatibility
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)

    # Add relationship to new RBAC system
    user_roles = relationship("RBACUserRole", back_populates="user")

    def get_roles(self, db):
        """Get user's RBAC roles (new system)"""
        # Check new system first
        if self.user_roles:
            return [ur.role for ur in self.user_roles if ur.is_active]

        # Fallback to enum (legacy)
        from app.models.rbac import get_role_by_name
        legacy_role = get_role_by_name(db, self.role.value)
        return [legacy_role] if legacy_role else []

    @property
    def is_admin(self):
        """Backward compatible admin check"""
        return self.role == UserRole.ADMIN
```

### 2. Permission Check Wrapper

**File**: `backend/app/services/rbac_service.py`

```python
def check_permission_compat(
    self,
    user,  # User object
    module_code: str,
    permission_type: str = "read"
) -> bool:
    """
    Backward compatible permission check
    Checks both new RBAC and legacy enum
    """
    # Check new RBAC system
    has_perm = self.check_permission(user.id, module_code, permission_type)
    if has_perm:
        return True

    # Fallback to legacy admin check
    if user.role == UserRole.ADMIN:
        return True  # Admins have all permissions

    # Fallback to basic role checks
    if permission_type == "read":
        return user.role in [UserRole.ADMIN, UserRole.USER, UserRole.VIEWER]
    elif permission_type == "write":
        return user.role in [UserRole.ADMIN, UserRole.USER]

    return False
```

### 3. Middleware Integration

**File**: `backend/app/middleware/auth_middleware.py` (new)

```python
from fastapi import Request, HTTPException
from app.models.database_enhanced import User
from app.services.rbac_service import RBACService

async def check_module_access(
    request: Request,
    module_code: str,
    permission_type: str = "read"
):
    """Check if current user can access module"""
    user = request.state.user  # Set by auth middleware

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    rbac = RBACService(request.state.db)

    if not rbac.check_permission_compat(user, module_code, permission_type):
        raise HTTPException(
            status_code=403,
            detail=f"No {permission_type} permission for {module_code}"
        )

    return True
```

---

## 📦 Existing Code Preservation

### Files We WON'T Modify:

- ✅ `backend/app/models/database.py` - Keep as-is
- ✅ `backend/app/models/database_enhanced.py` - Only ADD relationships
- ✅ Existing migrations 000-005 - No changes
- ✅ All existing services - Keep working
- ✅ All existing API routes - Keep working

### Files We WILL Enhance:

- 🔄 Add `backend/app/models/rbac.py` - New file
- 🔄 Add `backend/app/services/rbac_service.py` - New file
- 🔄 Add `backend/app/api/routes/rbac_routes.py` - New file
- 🔄 Add relationships to User model - Non-breaking

---

## 🧪 Testing Strategy

### 1. Test Existing Functionality FIRST

```bash
# Before applying RBAC migrations
python -m pytest tests/ -v

# All existing tests should pass
```

### 2. Apply Migrations

```bash
psql -U postgres -d ragchatbot < migrations/006_add_rbac_tables.sql
psql -U postgres -d ragchatbot < migrations/007_seed_rbac_data.sql
```

### 3. Test Existing Functionality AGAIN

```bash
# After applying migrations
python -m pytest tests/ -v

# All tests should STILL pass
```

### 4. Test New RBAC Features

```bash
# Test new permission system
python -m pytest tests/test_rbac.py -v
```

---

## 🚦 Rollback Plan

### If Something Breaks:

**Option 1: Remove New Tables (Safe)**
```sql
DROP TABLE IF EXISTS user_roles CASCADE;
DROP TABLE IF EXISTS role_module_permissions CASCADE;
DROP TABLE IF EXISTS modules CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
```

**Option 2: Restore Backup**
```bash
# Before migration, backup database
pg_dump -U postgres ragchatbot > backup_before_rbac.sql

# Restore if needed
psql -U postgres ragchatbot < backup_before_rbac.sql
```

---

## 📊 Migration Impact Assessment

### Zero Impact (Existing Features):
- ✅ Chat functionality
- ✅ File upload
- ✅ Web scraping
- ✅ Project estimator
- ✅ Evaluation metrics
- ✅ Tool usage dashboard
- ✅ Existing user accounts
- ✅ Existing sessions

### New Capabilities (Opt-In):
- 🆕 Granular module permissions
- 🆕 Department-based access
- 🆕 Multiple roles per user
- 🆕 Permission matrix management
- 🆕 Admin UI for RBAC

---

## ✅ Updated Implementation Plan

### Phase 1: Add RBAC Tables (Non-Breaking)
**Duration**: 1 day

1. Backup database
2. Apply migration 006 (add tables)
3. Apply migration 007 (seed data + sync existing users)
4. Verify existing functionality
5. Test new tables

**Risk**: LOW - Only adding new tables

### Phase 2: Add RBAC Service (Non-Breaking)
**Duration**: 1 day

1. Add rbac_service.py
2. Add backward compatibility methods
3. Keep existing auth working
4. Add unit tests

**Risk**: LOW - Existing code unmodified

### Phase 3: Add API Endpoints (Optional)
**Duration**: 2 days

1. Add RBAC API routes
2. Protect with auth
3. Add Pydantic schemas
4. Document API

**Risk**: LOW - New endpoints don't affect existing

### Phase 4: Add Admin UI (Optional)
**Duration**: 2 days

1. Create admin components
2. Add permission management UI
3. Add user role assignment UI

**Risk**: LOW - New UI components

### Phase 5: Gradual Migration (Optional)
**Duration**: Ongoing

1. Update route protection to use new RBAC
2. Migrate users to new system on login
3. Eventually deprecate enum (Phase 6)

**Risk**: LOW - Controlled rollout

---

## 🎯 Recommended Approach

### Start Small, Prove It Works:

**Week 1:**
- ✅ Add RBAC tables (migrations 006, 007)
- ✅ Test existing features still work
- ✅ Add RBAC service with compat layer
- ✅ Verify backward compatibility

**Week 2:**
- 🔄 Add API endpoints
- 🔄 Add basic admin UI
- 🔄 Test new features
- 🔄 Document everything

**Week 3+:**
- 🔮 Gradually adopt new RBAC
- 🔮 Migrate existing routes (optional)
- 🔮 Full RBAC enforcement (optional)

---

## 💡 Key Principles

1. **No Breaking Changes** - Existing functionality preserved
2. **Backward Compatible** - Old and new systems coexist
3. **Gradual Adoption** - Migrate features one at a time
4. **Easy Rollback** - Can revert at any point
5. **Test Everything** - Verify before and after
6. **Document Changes** - Clear migration guide

---

## ✅ Action Items

### Before Proceeding:

- [ ] Backup production database
- [ ] Run existing test suite
- [ ] Review migration scripts
- [ ] Confirm rollback plan

### During Implementation:

- [ ] Apply migrations incrementally
- [ ] Test after each step
- [ ] Monitor application logs
- [ ] Keep old code paths working

### After Completion:

- [ ] Verify all existing features
- [ ] Test new RBAC features
- [ ] Update documentation
- [ ] Train users on new features

---

**This approach ensures we enhance the system WITHOUT risk! 🎉**
