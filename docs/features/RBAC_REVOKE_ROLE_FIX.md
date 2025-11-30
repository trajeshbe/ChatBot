# RBAC Role Revocation Fix

**Date**: 2025-11-27
**Issue**: Role revocation failing with "Multiple rows were found when one or none was required"
**Status**: ✅ FIXED

---

## Problem Description

When attempting to revoke a role from a user, the system failed with the error:
```
Error revoking role: Multiple rows were found when one or none was required
```

### Root Cause

The DELETE endpoint `/api/v1/rbac/user-roles/{user_id}/{role_id}` was querying by `user_id` + `role_id` combination. When a user had the same role assigned multiple times (e.g., admin user with Admin role assigned 3 times during testing), the query matched multiple rows, causing `scalar_one_or_none()` to fail.

**Code Location**: `backend/app/services/rbac_service.py:408-418`

```python
async def revoke_role_from_user(...):
    stmt = select(UserRole).where(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id  # Can match multiple rows!
    )
    result = await self.db.execute(stmt)
    user_role = result.scalar_one_or_none()  # FAILS when multiple matches
```

---

## Solution

Created a new endpoint that deletes by the specific `user_role.id` instead of `user_id` + `role_id` combination.

### Backend Changes

#### 1. Added New Service Method
**File**: `backend/app/services/rbac_service.py`

```python
async def revoke_role_by_id(self, user_role_id: uuid.UUID) -> bool:
    """Revoke a specific role assignment by its ID"""
    stmt = select(UserRole).where(UserRole.id == user_role_id)
    result = await self.db.execute(stmt)
    user_role = result.scalar_one_or_none()

    if user_role:
        self.db.delete(user_role)
        await self.db.commit()
        return True
    return False
```

**Benefits**:
- Targets exact role assignment
- No ambiguity about which assignment to delete
- Handles duplicates correctly

#### 2. Added New API Endpoint
**File**: `backend/app/api/routes/rbac_routes.py`

```python
@router.delete(
    "/user-role-assignment/{user_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke role assignment by ID",
)
async def revoke_role_assignment_by_id(
    user_role_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Revoke a specific role assignment by its ID."""
    try:
        success = await rbac.revoke_role_by_id(user_role_id)
        if not success:
            raise HTTPException(status_code=404, detail="Role assignment not found")
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error revoking role: {str(e)}")
```

**Endpoint**: `DELETE /api/v1/rbac/user-role-assignment/{user_role_id}`

### Frontend Changes

**File**: `frontend/src/components/admin/UserRoleAssignment.tsx`

**Before**:
```typescript
const handleRevokeRole = async (userRoleId: string) => {
  const userRole = userRoles.find((ur) => ur.id === userRoleId);

  // Used user_id + role_id (ambiguous)
  const response = await fetch(
    `/api/v1/rbac/user-roles/${selectedUser.id}/${userRole.role_id}`,
    { method: 'DELETE' }
  );
};
```

**After**:
```typescript
const handleRevokeRole = async (userRoleId: string) => {
  // Uses specific user_role ID (unambiguous)
  const response = await fetch(
    `/api/v1/rbac/user-role-assignment/${userRoleId}`,
    { method: 'DELETE' }
  );

  await fetchUserRoles(selectedUser.id);
  alert('Role revoked successfully!');
};
```

**Benefits**:
- Simpler code (no need to find role_id first)
- Direct targeting of specific assignment
- Added success feedback alert

---

## Testing

### Test Scenario 1: Revoke Single Role Assignment
1. User has single Admin role assignment
2. Click revoke button
3. **Expected**: Role removed successfully
4. **Actual**: ✅ Works

### Test Scenario 2: Revoke Duplicate Role Assignments
1. Admin user has Admin role assigned 3 times
2. Click revoke on first assignment
3. **Expected**: Only first assignment removed, other 2 remain
4. **Actual**: ✅ Works (previously failed)

### Test Scenario 3: Revoke Different Roles
1. User has multiple different roles (Admin, Manager, User)
2. Click revoke on Manager role
3. **Expected**: Only Manager removed, Admin and User remain
4. **Actual**: ✅ Works

---

## Files Modified

### Backend
```
backend/app/services/rbac_service.py        (+13 lines)
  - Added revoke_role_by_id() method

backend/app/api/routes/rbac_routes.py       (+19 lines)
  - Added DELETE /user-role-assignment/{user_role_id} endpoint
```

### Frontend
```
frontend/src/components/admin/UserRoleAssignment.tsx  (modified)
  - Updated handleRevokeRole to use new endpoint
  - Simplified logic (removed userRole lookup)
  - Added success feedback
```

---

## Deployment Steps

1. **Backend**:
   ```bash
   docker-compose restart backend
   ```

2. **Frontend**:
   ```bash
   docker-compose restart frontend
   ```

3. **Verify**:
   - Navigate to Admin → RBAC → User Role Assignment
   - Select admin user
   - Click revoke on one of the duplicate Admin roles
   - Should see success message and role removed from list

---

## Backward Compatibility

The old endpoint `/api/v1/rbac/user-roles/{user_id}/{role_id}` is still available for backward compatibility. However, it will fail if there are duplicate role assignments.

**Recommendation**: Frontend should use the new endpoint exclusively.

---

## Future Improvements

### 1. Prevent Duplicate Assignments
Already implemented in `assign_role_to_user`:

```python
# Check for duplicate assignment
stmt = select(UserRole).where(
    UserRole.user_id == user_id,
    UserRole.role_id == role_id,
    UserRole.is_active == True
)
result = await self.db.execute(stmt)
existing = result.scalar_one_or_none()

if existing:
    raise ValueError("User already has this role assigned")
```

### 2. Clean Up Existing Duplicates
Run cleanup script to remove duplicate role assignments:

```sql
-- Find duplicates
SELECT user_id, role_id, COUNT(*) as count
FROM user_roles
WHERE is_active = true
GROUP BY user_id, role_id
HAVING COUNT(*) > 1;

-- Keep only the oldest assignment per user-role combo
DELETE FROM user_roles
WHERE id NOT IN (
  SELECT MIN(id)
  FROM user_roles
  WHERE is_active = true
  GROUP BY user_id, role_id
);
```

### 3. Add Database Unique Constraint
Prevent duplicates at database level:

```sql
CREATE UNIQUE INDEX idx_user_role_unique
ON user_roles(user_id, role_id)
WHERE is_active = true;
```

---

## Success Metrics

- ✅ Role revocation works for single assignments
- ✅ Role revocation works for duplicate assignments
- ✅ Specific assignment targeted (no ambiguity)
- ✅ User receives success feedback
- ✅ UI refreshes to show updated role list
- ✅ Backward compatibility maintained

---

## Related Documentation

- **RBAC Phase 1-2 Summary**: `RBAC_PHASE1_2_SUMMARY.md`
- **RBAC Implementation Status**: `RBAC_IMPLEMENTATION_STATUS.md`
- **RBAC Developer Guide**: `RBAC_DEVELOPER_GUIDE.md`

---

## Verification Results

**Date**: 2025-11-27

### Database Test
- ✅ Admin user had 3 duplicate Admin role assignments
- ✅ Deleted 2 assignments using new endpoint
- ✅ Now has 1 Admin role (correct state)
- ✅ Deletions persisted correctly to database

### API Test
```bash
# Before: 3 rows
SELECT COUNT(*) FROM user_roles WHERE user_id = 'f754df7e-71d2-477a-ba94-1ed44fa37291';
# Result: 3

# After deleting 2 assignments: 1 row
SELECT COUNT(*) FROM user_roles WHERE user_id = 'f754df7e-71d2-477a-ba94-1ed44fa37291';
# Result: 1
```

### UI Test
- ✅ Frontend "Failed to fetch" error resolved
- ✅ User can revoke roles successfully
- ✅ Revoked roles no longer reappear
- ✅ UI refreshes correctly showing updated role list

**Fix Verified**: 2025-11-27 ✅
**Status**: Complete and working in production
**User Confirmation**: "its working now"
