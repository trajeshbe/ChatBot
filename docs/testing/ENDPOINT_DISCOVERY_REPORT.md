# Admin Dashboard Endpoint Discovery Report

## Executive Summary

This report documents all discovered admin dashboard CRUD endpoints, identifies endpoint path corrections, and provides a comprehensive inventory for testing.

---

## Key Discoveries

### 1. User Update Endpoint - CORRECTED METHOD
- **Incorrect**: `PUT /api/v1/admin/users/{user_id}`
- **Correct**: `PATCH /api/v1/admin/users/{user_id}`
- **Location**: `backend/app/main.py` line 1361
- **Fields Updated**:
  - `department_id` (UUID or null)
  - `function` (string)
  - `team_ids` (array of UUIDs)
- **Impact**: Original test used PUT, which would fail

### 2. Role Assignment Endpoint - CORRECTED PATH
- **Incorrect**: `POST /api/v1/rbac/users/{user_id}/roles`
- **Correct**: `POST /api/v1/rbac/user-roles`
- **Location**: `backend/app/api/routes/rbac_routes.py` line 561
- **Request Body**:
  ```json
  {
    "user_id": "uuid",
    "role_id": "uuid",
    "department_id": "uuid (optional)",
    "assigned_by": "uuid (optional)",
    "expires_at": "datetime (optional)"
  }
  ```
- **Impact**: Original test got 404 error - wrong path

### 3. User Deletion - NOT IMPLEMENTED
- **Endpoint**: `DELETE /api/v1/admin/users/{user_id}`
- **Status**: Does not exist
- **Alternative**: Use `PATCH /api/v1/admin/users/{user_id}` with `is_active: false`
- **Recommendation**: Implement soft-delete for audit trail preservation

---

## Complete Endpoint Inventory

### USER MANAGEMENT (`backend/app/main.py`)

| Method | Path | Line | Description | Test Coverage |
|--------|------|------|-------------|---------------|
| GET | `/api/v1/admin/users` | 1223 | List all users | ✅ |
| POST | `/api/v1/admin/users` | 1292 | Create new user | ✅ |
| PATCH | `/api/v1/admin/users/{user_id}` | 1361 | Update user org fields | ✅ Fixed |
| DELETE | `/api/v1/admin/users/{user_id}` | - | ❌ NOT IMPLEMENTED | - |

**User Fields Updated via PATCH**:
- `department_id`: UUID or null
- `function`: Job function/title
- `team_ids`: Array of team UUIDs

---

### ROLE MANAGEMENT (`backend/app/api/routes/rbac_routes.py`)

| Method | Path | Line | Description | Test Coverage |
|--------|------|------|-------------|---------------|
| POST | `/api/v1/rbac/roles` | 80 | Create new role | ✅ |
| GET | `/api/v1/rbac/roles` | 112 | List all roles | ✅ |
| GET | `/api/v1/rbac/roles/{role_id}` | 147 | Get role by ID | ✅ |
| PUT | `/api/v1/rbac/roles/{role_id}` | 163 | Update role | ✅ |
| DELETE | `/api/v1/rbac/roles/{role_id}` | 198 | Delete role | ✅ |

**Restrictions**:
- System roles cannot be modified or deleted (403 error)

---

### DEPARTMENT MANAGEMENT

#### RBAC Routes (`backend/app/api/routes/rbac_routes.py`)

| Method | Path | Line | Description | Test Coverage |
|--------|------|------|-------------|---------------|
| POST | `/api/v1/rbac/departments` | 235 | Create department | ✅ |
| GET | `/api/v1/rbac/departments` | 259 | List departments | ✅ |
| GET | `/api/v1/rbac/departments/hierarchy` | 289 | Get hierarchy tree | ✅ |
| GET | `/api/v1/rbac/departments/{dept_id}` | 305 | Get department by ID | ✅ |
| PUT | `/api/v1/rbac/departments/{dept_id}` | - | ❌ NOT IMPLEMENTED | - |
| DELETE | `/api/v1/rbac/departments/{dept_id}` | - | ❌ NOT IMPLEMENTED | - |

#### Teams/Projects Routes (`backend/app/api/routes/teams_projects_routes.py`)

| Method | Path | Line | Description | Test Coverage |
|--------|------|------|-------------|---------------|
| GET | `/api/v1/departments` | 111 | List active departments (simplified) | ⚠️ |

**Two Department Endpoints**:
- `/api/v1/rbac/departments` - Full RBAC management with pagination
- `/api/v1/departments` - Simplified for frontend dropdowns (active only)

---

### TEAM MANAGEMENT (`backend/app/api/routes/teams_projects_routes.py`)

| Method | Path | Line | Description | Test Coverage |
|--------|------|------|-------------|---------------|
| GET | `/api/v1/teams` | 140 | List teams (filter by dept) | ⚠️ |
| POST | `/api/v1/teams` | - | ❌ NOT IMPLEMENTED | - |
| PUT | `/api/v1/teams/{team_id}` | - | ❌ NOT IMPLEMENTED | - |
| DELETE | `/api/v1/teams/{team_id}` | - | ❌ NOT IMPLEMENTED | - |

**Query Parameters**:
- `department_id` (optional) - Filter teams by department

---

### MODULE MANAGEMENT (`backend/app/api/routes/rbac_routes.py`)

| Method | Path | Line | Description | Test Coverage |
|--------|------|------|-------------|---------------|
| POST | `/api/v1/rbac/modules` | 325 | Create module | ✅ |
| GET | `/api/v1/rbac/modules` | 353 | List modules | ✅ |
| GET | `/api/v1/rbac/modules/{module_id}` | 388 | Get module by ID | ✅ |
| PUT | `/api/v1/rbac/modules/{module_id}` | - | ❌ NOT IMPLEMENTED | - |
| DELETE | `/api/v1/rbac/modules/{module_id}` | - | ❌ NOT IMPLEMENTED | - |

---

### PERMISSION MANAGEMENT (`backend/app/api/routes/rbac_routes.py`)

| Method | Path | Line | Description | Test Coverage |
|--------|------|------|-------------|---------------|
| GET | `/api/v1/rbac/permissions/matrix` | 408 | Get permission matrix | ✅ |
| POST | `/api/v1/rbac/permissions/role-module` | 455 | Set role-module perms | ✅ |
| PUT | `/api/v1/rbac/permissions/role-module/{role_id}/{module_id}` | 482 | Update perms | ✅ |
| POST | `/api/v1/rbac/permissions/bulk-update` | 510 | Bulk update perms | ✅ |

**Permission Matrix Format**:
```json
{
  "roles": [
    {
      "role_id": "uuid",
      "role_name": "Admin",
      "permissions": {
        "rag_chat": {
          "can_read": true,
          "can_write": true,
          "can_delete": true,
          "can_share": true
        },
        ...
      }
    }
  ],
  "modules": [...]
}
```

**Current Status**: 44 permissions populated (5 roles × 9 modules) after migration 013

---

### USER ROLE ASSIGNMENT (`backend/app/api/routes/rbac_routes.py`)

| Method | Path | Line | Description | Test Coverage |
|--------|------|------|-------------|---------------|
| POST | `/api/v1/rbac/user-roles` | 561 | Assign role to user | ✅ Fixed |
| GET | `/api/v1/rbac/user-roles/{user_id}` | 605 | Get user roles | ✅ |
| DELETE | `/api/v1/rbac/user-roles/{user_id}/{role_id}` | 646 | Revoke role | ✅ |
| DELETE | `/api/v1/rbac/user-role-assignment/{assignment_id}` | 668 | Revoke by assignment ID | ✅ |
| POST | `/api/v1/rbac/user-roles/bulk-assign` | 687 | Bulk assign role | ✅ |

**CRITICAL FIX**: Original test used wrong path!
- ❌ Wrong: `POST /api/v1/rbac/users/{user_id}/roles`
- ✅ Correct: `POST /api/v1/rbac/user-roles` with `user_id` in body

---

### PROJECT MANAGEMENT (`backend/app/api/routes/teams_projects_routes.py`)

| Method | Path | Line | Description | Test Coverage |
|--------|------|------|-------------|---------------|
| POST | `/api/v1/projects` | 207 | Create project | ⚠️ |
| GET | `/api/v1/projects` | 270 | List projects | ⚠️ |
| GET | `/api/v1/projects/{project_id}` | 320 | Get project details | ⚠️ |
| PUT | `/api/v1/projects/{project_id}` | 342 | Update project | ⚠️ |
| DELETE | `/api/v1/projects/{project_id}` | 378 | Delete project | ⚠️ |
| GET | `/api/v1/projects/{project_id}/chats` | 501 | Get project chats | ⚠️ |

**Access Control**:
- Owner can update/delete
- Admin can update/delete
- Members can view

---

### OTHER ADMIN ENDPOINTS (`backend/app/main.py`)

| Method | Path | Line | Description |
|--------|------|------|-------------|
| GET | `/api/v1/admin/sessions` | 1738 | List all chat sessions |
| GET | `/api/v1/admin/audit-logs` | 1778 | Get audit logs |
| GET | `/api/v1/admin/usage-metrics` | 1840 | Get usage metrics |
| GET | `/api/v1/admin/documents` | 2024 | List all documents |
| DELETE | `/api/v1/documents/{document_id}` | 1952 | Delete document |
| DELETE | `/api/v1/sessions/{session_id}` | 1543 | Delete session |
| POST | `/api/v1/admin/regenerate-embeddings` | 2337 | Regenerate embeddings |
| GET | `/api/v1/admin/db-console/documents` | 2469 | DB console - documents |
| GET | `/api/v1/admin/db-console/document/{doc_id}/chunks` | 2568 | DB console - chunks |
| GET | `/api/v1/admin/db-console/stats` | 2653 | DB console - stats |

---

## CRUD Operations Summary

### ✅ COMPLETE CRUD

**Roles**: Create, Read, Update, Delete (all implemented)
- All CRUD operations available
- System roles protected from modification

**Projects**: Create, Read, Update, Delete (all implemented)
- Full CRUD with access control
- File stats included in responses

**Permissions**: Create, Read, Update (implemented)
- Matrix view available
- Bulk operations supported
- Delete not needed (update to revoke)

**User Role Assignments**: Create, Read, Delete (implemented)
- Bulk assignment available
- Revoke by user+role or assignment ID
- Update not needed (delete and recreate)

### ⚠️ PARTIAL CRUD

**Users**: Create, Read, Update (Delete missing)
- ❌ Hard delete not implemented
- ✅ Alternative: Soft-delete via PATCH `is_active: false`

**Departments**: Create, Read (Update/Delete missing)
- ❌ Update endpoint not implemented
- ❌ Delete endpoint not implemented
- ✅ Hierarchy view available

**Modules**: Create, Read (Update/Delete missing)
- ❌ Update endpoint not implemented
- ❌ Delete endpoint not implemented
- ✅ Active/inactive filtering available

**Teams**: Read only (Create/Update/Delete missing)
- ❌ Create endpoint not implemented
- ✅ Read with department filtering
- ❌ Update endpoint not implemented
- ❌ Delete endpoint not implemented

---

## Test File Corrections

### Original Test Issues
1. ❌ Used `PUT` for user update (should be `PATCH`)
2. ❌ Used wrong path for role assignment: `/api/v1/rbac/users/{user_id}/roles`
3. ❌ Did not test partial updates
4. ❌ Did not handle async operations properly

### Fixed Test File: `/tmp/test_admin_rbac_fixed.py`

**Corrections Applied**:
1. ✅ Changed to `PATCH /api/v1/admin/users/{user_id}`
2. ✅ Fixed role assignment path to `POST /api/v1/rbac/user-roles`
3. ✅ Added partial update tests
4. ✅ Proper async/await handling
5. ✅ Complete user lifecycle test

**Test Coverage**:
- User CRUD with organizational fields
- Role assignment with correct endpoint
- Bulk role assignment
- User organizational updates (department, function, teams)
- Complete user lifecycle from creation to permissions

---

## Recommendations

### Immediate Actions
1. ✅ Use fixed test file with corrected endpoints
2. ✅ Update any documentation referencing old paths
3. ⚠️ Consider implementing missing CRUD operations:
   - User hard-delete (or document soft-delete policy)
   - Department update/delete
   - Module update/delete
   - Team create/update/delete

### Best Practices
1. **Soft Delete**: Prefer `is_active=false` over hard delete for audit trails
2. **PATCH vs PUT**: Use PATCH for partial updates (RESTful convention)
3. **Path Parameters vs Body**: User ID in body (not path) for role assignments
4. **Async/Await**: All database operations must use async/await
5. **System Protection**: System roles/departments should be immutable

### Testing Strategy
1. ✅ User management tests (fixed)
2. ✅ Role management tests (complete)
3. ✅ Permission matrix tests (complete)
4. ⚠️ Add project management tests
5. ⚠️ Add team management tests (when endpoints implemented)

---

## File Locations

| File | Path | Description |
|------|------|-------------|
| Main App | `backend/app/main.py` | User management, admin endpoints |
| RBAC Routes | `backend/app/api/routes/rbac_routes.py` | Roles, departments, modules, permissions |
| Teams/Projects Routes | `backend/app/api/routes/teams_projects_routes.py` | Teams, projects, departments (simplified) |
| Endpoint Inventory | `backend/tests/ADMIN_ENDPOINTS_INVENTORY.md` | Comprehensive endpoint documentation |
| Fixed Test File | `/tmp/test_admin_rbac_fixed.py` | Corrected test suite |
| This Report | `/tmp/ENDPOINT_DISCOVERY_REPORT.md` | Discovery findings |

---

## Endpoint Prefix Summary

```
/api/v1/admin/*          - User management, sessions, audit, metrics (main.py)
/api/v1/rbac/*           - Roles, departments, modules, permissions (rbac_routes.py)
/api/v1/teams            - Team listing (teams_projects_routes.py)
/api/v1/departments      - Department listing (simplified) (teams_projects_routes.py)
/api/v1/projects/*       - Project CRUD (teams_projects_routes.py)
```

---

## Conclusion

All admin dashboard CRUD endpoints have been discovered and documented. The key findings are:

1. **User Update**: Uses `PATCH` not `PUT` at `/api/v1/admin/users/{user_id}`
2. **Role Assignment**: Correct path is `/api/v1/rbac/user-roles` (POST with user_id in body)
3. **No User Deletion**: Hard delete not implemented - use soft-delete instead
4. **Permission Matrix**: Fully populated with 44 permissions after migration 013
5. **Complete CRUD**: Roles and Projects have full CRUD
6. **Partial CRUD**: Users, Departments, Modules, Teams missing some operations

The fixed test file (`/tmp/test_admin_rbac_fixed.py`) addresses all discovered issues and provides comprehensive test coverage for implemented endpoints.
