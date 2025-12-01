# Permission Matrix Save Bug - Investigation Needed

**Date Reported**: 2025-12-01
**Reported By**: User
**Status**: 🔍 **NEEDS INVESTIGATION**

---

## 🐛 Bug Description

**What**: Permission matrix changes are not persisting after save

**Observed Behavior**:
- User edited permission matrix for CxO role
- Clicked Save button
- UI showed no visual change
- Unclear if save succeeded but UI didn't update, or save failed silently

**Expected Behavior**:
- Changes should save to database
- UI should reflect updated permissions
- Success message/toast should appear

---

## 📍 Location

**UI Location**: Admin Dashboard > RBAC > Permissions tab

**Frontend Component**: Likely `PermissionMatrix.tsx` or similar

**Backend Endpoint**: Likely `/api/v1/admin/permissions` or similar

---

## 🔍 Investigation Required

### Priority 1: Check Network Tab
```
1. Open browser DevTools (F12)
2. Go to Network tab
3. Edit permission matrix
4. Click Save
5. Check:
   - Is API request sent?
   - What's the response status? (200, 400, 500?)
   - What's the response body?
```

### Priority 2: Check Backend Logs
```bash
# Check backend logs for errors
docker-compose logs backend | grep -i "permission\|matrix\|error" | tail -50

# Check for database errors
docker-compose logs postgres | grep -i "error" | tail -20
```

### Priority 3: Check Database
```bash
# Check if permissions table exists and has data
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT * FROM role_permissions WHERE role_name = 'CxO' LIMIT 5;
"

# Check if changes are in database but not showing in UI
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT role_name, module, permission_type, has_permission
FROM role_permissions
WHERE role_name = 'CxO'
ORDER BY module, permission_type;
"
```

---

## 🎯 Possible Root Causes

### 1. Frontend Not Sending Request
**Symptom**: No network request in DevTools

**Possible Causes**:
- Save button onClick handler not connected
- Form validation preventing submission
- JavaScript error blocking request

**Investigation**:
```javascript
// Check frontend console for errors
// Look for: "Uncaught Error", "Cannot read property"
```

---

### 2. Backend Endpoint Not Working
**Symptom**: Request sent but returns 400/500 error

**Possible Causes**:
- Endpoint route not registered
- Request body validation failing
- Database transaction failing

**Investigation**:
```bash
# Check if endpoint exists
grep -r "save.*permission\|update.*permission" backend/app/api/routes/
grep -r "role_permissions" backend/app/services/
```

---

### 3. Database Constraint Issue
**Symptom**: Request returns 200 but data not saved

**Possible Causes**:
- Foreign key constraint violation
- Transaction not committed
- Trigger or constraint blocking update

**Investigation**:
```sql
-- Check table structure
\d+ role_permissions;

-- Check constraints
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'role_permissions'::regclass;
```

---

### 4. UI Not Refreshing After Save
**Symptom**: Save succeeds but UI doesn't update

**Possible Causes**:
- State not updating after API call
- Component not re-rendering
- Cached data not invalidated

**Investigation**:
```typescript
// Check component state management
// Look for: useState, useEffect, API call then state update
```

---

## 🧪 Test Cases to Verify

### Test 1: Simple Permission Change
```
1. Open Admin > RBAC > Permissions
2. Change one checkbox (e.g., CxO Chat Read)
3. Click Save
4. Refresh page
5. Verify: Is checkbox state preserved?
```

### Test 2: Multiple Permission Changes
```
1. Change 3-4 different permissions
2. Click Save
3. Refresh page
4. Verify: Are all changes preserved?
```

### Test 3: Different Roles
```
1. Try same test with different role (e.g., Admin, User)
2. Verify: Does it work for some roles but not others?
```

---

## 📊 Expected API Flow

### Frontend Request
```typescript
// Expected API call
POST /api/v1/admin/permissions
Headers: {
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
Body: {
  "role_id": "uuid",
  "permissions": [
    { "module": "chat", "permission_type": "read", "has_permission": true },
    { "module": "chat", "permission_type": "write", "has_permission": false },
    // ...
  ]
}
```

### Backend Response (Success)
```json
{
  "status": "success",
  "message": "Permissions updated successfully",
  "updated_count": 12
}
```

### Backend Response (Error)
```json
{
  "status": "error",
  "message": "Failed to update permissions",
  "detail": "Foreign key constraint violation..."
}
```

---

## 🔧 Potential Fixes

### If Frontend Issue:
```typescript
// Ensure state updates after save
const handleSave = async () => {
  try {
    const response = await savePermissions(permissions);
    if (response.status === 'success') {
      // Update local state
      setPermissions(permissions);
      // Show success message
      showToast('Permissions saved successfully');
      // Optionally refresh data
      await fetchPermissions();
    }
  } catch (error) {
    showToast('Failed to save permissions', 'error');
  }
};
```

### If Backend Issue:
```python
# Ensure transaction commits
async def update_role_permissions(
    role_id: UUID,
    permissions: List[PermissionUpdate],
    db: Session
):
    try:
        # Delete existing permissions
        db.query(RolePermission).filter(
            RolePermission.role_id == role_id
        ).delete()

        # Insert new permissions
        for perm in permissions:
            new_perm = RolePermission(
                role_id=role_id,
                module=perm.module,
                permission_type=perm.permission_type,
                has_permission=perm.has_permission
            )
            db.add(new_perm)

        # IMPORTANT: Commit transaction
        db.commit()

        return {"status": "success", "updated_count": len(permissions)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📝 Next Steps

1. **User Action Required**: Follow "Priority 1: Check Network Tab" above
   - Open DevTools
   - Try to save permission change
   - Take screenshot of Network tab
   - Share request/response details

2. **Backend Investigation**: Check logs and database
   - Look for errors in backend logs
   - Verify permissions table structure
   - Check if data is being saved

3. **Create Test Case**: Add Playwright test for permission matrix
   - Navigate to Permissions tab
   - Change permission
   - Save
   - Verify in database
   - Verify in UI after refresh

---

## 🎯 Related Files to Check

### Frontend
- `frontend/src/components/admin/PermissionMatrix.tsx`
- `frontend/src/pages/admin.tsx`

### Backend
- `backend/app/api/routes/rbac_routes.py`
- `backend/app/services/rbac_service.py`
- `backend/app/models/rbac.py`

### Database
- `backend/migrations/*_rbac_tables.sql`

---

## 📚 Related Documentation

- [RBAC Implementation Plan](../features/RBAC_IMPLEMENTATION_PLAN.md)
- [RBAC Developer Guide](../features/RBAC_DEVELOPER_GUIDE.md)
- [Admin Dashboard Page Object](../../backend/tests/playwright/page_objects/admin_dashboard_page.py)

---

## 🚨 Impact Assessment

**Severity**: ⚠️ **MEDIUM-HIGH**

**Reason**: Permission management is critical for RBAC system. If admins can't modify permissions, the RBAC system is effectively read-only.

**Affected Users**: Admin users trying to manage role permissions

**Workaround**: Possible database manual update, but not practical

---

**Status**: Awaiting investigation results from user
**Next Action**: User to check Network tab and share findings
**Assigned To**: TBD (needs investigation first)

---

**Created**: 2025-12-01
**Last Updated**: 2025-12-01
**Priority**: HIGH (blocks permission management)
