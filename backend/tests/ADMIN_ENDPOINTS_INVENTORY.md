# Admin Dashboard CRUD Endpoints Inventory

## Overview
This document provides a comprehensive inventory of all admin dashboard CRUD endpoints for managing users, roles, departments, modules, and permissions.

## Endpoint Categories

### 1. USER MANAGEMENT (main.py)

#### GET /api/v1/admin/users
- **Description**: List all users with department and team information
- **Method**: GET
- **Authentication**: Required
- **Response**: List of users with fields:
  - id, username, email, full_name, role, is_active
  - created_at, last_login
  - department_id, department_name
  - function, team_ids, team_names
- **Test Coverage**: `test_admin_rbac_comprehensive.py` (read operations)
- **Example**:
  ```bash
  curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/admin/users
  ```

#### POST /api/v1/admin/users
- **Description**: Create a new user
- **Method**: POST
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string",
    "full_name": "string",
    "role": "admin|user|readonly"
  }
  ```
- **Response**: Created user object
- **Test Coverage**: `test_admin_rbac_comprehensive.py` (create operations)
- **Notes**: Password is hashed with SHA256 (demo - use bcrypt in production)

#### PATCH /api/v1/admin/users/{user_id}
- **Description**: Update user organizational fields (department, function, teams)
- **Method**: PATCH (NOT PUT!)
- **Authentication**: Required
- **Path Parameter**: user_id (UUID)
- **Request Body** (all fields optional):
  ```json
  {
    "department_id": "uuid-string or null",
    "function": "string",
    "team_ids": ["uuid-string", ...]
  }
  ```
- **Response**: Updated user object
- **Test Coverage**: `test_admin_rbac_fixed.py` (fixed version)
- **Important**: Original test used PUT, should use PATCH

#### DELETE /api/v1/admin/users/{user_id}
- **Status**: ⚠️ NOT IMPLEMENTED
- **Recommendation**: Users should be soft-deleted (is_active=False) rather than hard-deleted
- **Alternative**: Use PATCH to set `is_active: false`

---

### 2. ROLE MANAGEMENT (rbac_routes.py)

#### POST /api/v1/rbac/roles
- **Description**: Create a new role
- **Method**: POST
- **Prefix**: /api/v1/rbac
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "parent_role_id": "uuid-string (optional)",
    "is_system_role": false
  }
  ```
- **Response**: Created role object (201 Created)
- **Test Coverage**: `test_admin_rbac_comprehensive.py`

#### GET /api/v1/rbac/roles
- **Description**: List all roles with pagination
- **Method**: GET
- **Query Parameters**:
  - page (default: 1)
  - page_size (default: 50, max: 100)
  - include_system (default: true)
- **Response**:
  ```json
  {
    "items": [...],
    "total": 0,
    "page": 1,
    "page_size": 50
  }
  ```
- **Test Coverage**: `test_admin_rbac_comprehensive.py`

#### GET /api/v1/rbac/roles/{role_id}
- **Description**: Get specific role by ID
- **Method**: GET
- **Path Parameter**: role_id (UUID)
- **Response**: Single role object
- **Error**: 404 if not found

#### PUT /api/v1/rbac/roles/{role_id}
- **Description**: Update existing role
- **Method**: PUT
- **Path Parameter**: role_id (UUID)
- **Request Body**: RoleUpdate schema (partial fields allowed)
- **Response**: Updated role object
- **Restrictions**: Cannot modify system roles (403 error)

#### DELETE /api/v1/rbac/roles/{role_id}
- **Description**: Delete a role
- **Method**: DELETE
- **Path Parameter**: role_id (UUID)
- **Response**: 204 No Content
- **Restrictions**: Cannot delete system roles (403 error)

---

### 3. DEPARTMENT MANAGEMENT (rbac_routes.py + teams_projects_routes.py)

#### POST /api/v1/rbac/departments
- **Description**: Create a new department
- **Method**: POST
- **Prefix**: /api/v1/rbac
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string (optional)",
    "parent_department_id": "uuid-string (optional)"
  }
  ```
- **Response**: Created department object (201 Created)

#### GET /api/v1/rbac/departments
- **Description**: List all departments with pagination
- **Method**: GET
- **Prefix**: /api/v1/rbac
- **Query Parameters**:
  - page (default: 1)
  - page_size (default: 50)
- **Response**: Paginated list of departments
- **Test Coverage**: `test_admin_rbac_comprehensive.py`

#### GET /api/v1/rbac/departments/hierarchy
- **Description**: Get departments as hierarchical tree
- **Method**: GET
- **Prefix**: /api/v1/rbac
- **Response**: Nested department hierarchy
- **Test Coverage**: `test_admin_rbac_comprehensive.py`

#### GET /api/v1/rbac/departments/{department_id}
- **Description**: Get specific department by ID
- **Method**: GET
- **Path Parameter**: department_id (UUID)
- **Response**: Single department object
- **Error**: 404 if not found

#### GET /api/v1/departments
- **Description**: Get all active departments (simplified endpoint)
- **Method**: GET
- **Prefix**: /api/v1 (teams_projects_routes.py)
- **Authentication**: Required (get_current_user)
- **Response**: List of active departments only
- **Use Case**: Frontend dropdowns

#### PUT /api/v1/rbac/departments/{department_id}
- **Status**: ⚠️ NOT IMPLEMENTED
- **Recommendation**: Add update endpoint for department name/description changes

#### DELETE /api/v1/rbac/departments/{department_id}
- **Status**: ⚠️ NOT IMPLEMENTED
- **Recommendation**: Add soft-delete (is_active=False)

---

### 4. MODULE MANAGEMENT (rbac_routes.py)

#### POST /api/v1/rbac/modules
- **Description**: Create a new application module
- **Method**: POST
- **Request Body**:
  ```json
  {
    "name": "string",
    "code": "string",
    "description": "string (optional)",
    "icon": "string (optional)",
    "route": "string (optional)",
    "display_order": 0,
    "is_active": true
  }
  ```
- **Response**: Created module object (201 Created)

#### GET /api/v1/rbac/modules
- **Description**: List all modules with pagination
- **Method**: GET
- **Query Parameters**:
  - page (default: 1)
  - page_size (default: 50)
  - active_only (default: false)
- **Response**: Paginated list of modules
- **Test Coverage**: `test_admin_rbac_comprehensive.py`

#### GET /api/v1/rbac/modules/{module_id}
- **Description**: Get specific module by ID
- **Method**: GET
- **Path Parameter**: module_id (UUID)
- **Response**: Single module object
- **Error**: 404 if not found

#### PUT /api/v1/rbac/modules/{module_id}
- **Status**: ⚠️ NOT IMPLEMENTED
- **Recommendation**: Add update endpoint for module metadata

#### DELETE /api/v1/rbac/modules/{module_id}
- **Status**: ⚠️ NOT IMPLEMENTED
- **Recommendation**: Add soft-delete (is_active=False)

---

### 5. PERMISSION MANAGEMENT (rbac_routes.py)

#### GET /api/v1/rbac/permissions/matrix
- **Description**: Get complete permission matrix (roles × modules)
- **Method**: GET
- **Response**:
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
- **Test Coverage**: `test_admin_rbac_comprehensive.py`
- **Note**: Now fully populated after migration 013

#### POST /api/v1/rbac/permissions/role-module
- **Description**: Set permissions for role-module combination
- **Method**: POST
- **Request Body**:
  ```json
  {
    "role_id": "uuid",
    "module_id": "uuid",
    "can_read": true,
    "can_write": false,
    "can_delete": false,
    "can_share": false
  }
  ```
- **Response**: Created permission object (201 Created)

#### PUT /api/v1/rbac/permissions/role-module/{role_id}/{module_id}
- **Description**: Update existing role-module permissions
- **Method**: PUT
- **Path Parameters**: role_id (UUID), module_id (UUID)
- **Request Body**: Permission flags (can_read, can_write, etc.)
- **Response**: Updated permission object

#### POST /api/v1/rbac/permissions/bulk-update
- **Description**: Bulk update permissions for a role across multiple modules
- **Method**: POST
- **Request Body**:
  ```json
  {
    "role_id": "uuid",
    "permissions": {
      "rag_chat": {"can_read": true, "can_write": true, ...},
      "web_scraper": {"can_read": true, "can_write": false, ...}
    }
  }
  ```
- **Response**:
  ```json
  {
    "successful": 5,
    "failed": 0,
    "errors": []
  }
  ```

---

### 6. USER ROLE ASSIGNMENT (rbac_routes.py)

#### POST /api/v1/rbac/user-roles
- **Description**: Assign a role to a user
- **Method**: POST
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
- **Response**: User role assignment object (201 Created)
- **Test Coverage**: `test_admin_rbac_fixed.py` (CORRECTED PATH)
- **Important**: Original test used wrong path `/api/v1/rbac/users/{user_id}/roles`
- **Correct Path**: `/api/v1/rbac/user-roles` (POST body contains user_id)

#### GET /api/v1/rbac/user-roles/{user_id}
- **Description**: Get all role assignments for a user
- **Method**: GET
- **Path Parameter**: user_id (UUID)
- **Query Parameters**:
  - active_only (default: true)
- **Response**: List of user role assignments with details
- **Test Coverage**: `test_admin_rbac_comprehensive.py`

#### DELETE /api/v1/rbac/user-roles/{user_id}/{role_id}
- **Description**: Revoke a specific role from a user
- **Method**: DELETE
- **Path Parameters**: user_id (UUID), role_id (UUID)
- **Response**: 204 No Content
- **Error**: 404 if assignment not found

#### DELETE /api/v1/rbac/user-role-assignment/{user_role_id}
- **Description**: Revoke a role assignment by its unique ID
- **Method**: DELETE
- **Path Parameter**: user_role_id (UUID - the assignment record ID)
- **Response**: 204 No Content
- **Error**: 404 if assignment not found
- **Use Case**: When you have the assignment ID directly

#### POST /api/v1/rbac/user-roles/bulk-assign
- **Description**: Assign a role to multiple users at once
- **Method**: POST
- **Request Body**:
  ```json
  {
    "user_ids": ["uuid1", "uuid2", ...],
    "role_id": "uuid",
    "department_id": "uuid (optional)",
    "assigned_by": "uuid (optional)"
  }
  ```
- **Response**:
  ```json
  {
    "successful": 5,
    "failed": 1,
    "errors": ["User uuid: error message"]
  }
  ```

---

### 7. TEAM MANAGEMENT (teams_projects_routes.py)

#### GET /api/v1/teams
- **Description**: Get all teams, optionally filtered by department
- **Method**: GET
- **Prefix**: /api/v1
- **Authentication**: Required (get_current_user)
- **Query Parameters**:
  - department_id (UUID, optional) - filter by department
- **Response**: List of teams with enriched data:
  - Team details (id, name, code, description)
  - Department name
  - Team lead username
  - Member count (actually project count)
- **Use Case**: Frontend dropdowns after department selection

#### POST /api/v1/teams
- **Status**: ⚠️ NOT IMPLEMENTED
- **Recommendation**: Add team creation endpoint

#### PUT /api/v1/teams/{team_id}
- **Status**: ⚠️ NOT IMPLEMENTED
- **Recommendation**: Add team update endpoint

#### DELETE /api/v1/teams/{team_id}
- **Status**: ⚠️ NOT IMPLEMENTED
- **Recommendation**: Add soft-delete (is_active=False)

---

### 8. PROJECT MANAGEMENT (teams_projects_routes.py)

#### POST /api/v1/projects
- **Description**: Create a new project
- **Method**: POST
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string (optional)",
    "department_id": "uuid",
    "team_id": "uuid"
  }
  ```
- **Response**: Created project with enriched data (201)
- **Validation**: Team must belong to department

#### GET /api/v1/projects
- **Description**: Get all projects accessible by current user
- **Method**: GET
- **Query Parameters**:
  - status (active|archived|closed)
  - department_id (UUID)
  - team_id (UUID)
- **Response**: List of projects (owner, member, or same department)

#### GET /api/v1/projects/{project_id}
- **Description**: Get specific project by ID
- **Method**: GET
- **Path Parameter**: project_id (UUID)
- **Response**: Project with file stats
- **Access Control**: Owner, member, or admin

#### PUT /api/v1/projects/{project_id}
- **Description**: Update project (owner or admin only)
- **Method**: PUT
- **Path Parameter**: project_id (UUID)
- **Request Body**:
  ```json
  {
    "name": "string (optional)",
    "description": "string (optional)",
    "status": "active|archived|closed (optional)"
  }
  ```
- **Response**: Updated project object
- **Access Control**: Owner or admin only

#### DELETE /api/v1/projects/{project_id}
- **Description**: Delete project (owner or admin only)
- **Method**: DELETE
- **Path Parameter**: project_id (UUID)
- **Response**: Success message
- **Access Control**: Owner or admin only

#### GET /api/v1/projects/{project_id}/chats
- **Description**: Get all chat sessions for a project
- **Method**: GET
- **Path Parameter**: project_id (UUID)
- **Response**: List of chat sessions with message counts

---

### 9. PERMISSION QUERY ENDPOINTS (rbac_routes.py)

#### GET /api/v1/rbac/users/{user_id}/permissions
- **Description**: Get consolidated permissions for a user
- **Method**: GET
- **Path Parameter**: user_id (UUID)
- **Response**:
  ```json
  {
    "user_id": "uuid",
    "username": "string",
    "roles": [...],
    "departments": [...],
    "permissions": {...},
    "accessible_modules": [...]
  }
  ```
- **Test Coverage**: `test_admin_rbac_comprehensive.py`

#### POST /api/v1/rbac/permissions/check
- **Description**: Check if user has specific permission
- **Method**: POST
- **Request Body**:
  ```json
  {
    "user_id": "uuid",
    "module_code": "rag_chat",
    "permission_type": "read|write|delete|share"
  }
  ```
- **Response**:
  ```json
  {
    "has_permission": true,
    "user_id": "uuid",
    "module_code": "rag_chat",
    "permission_type": "read",
    "reason": "string (if denied)"
  }
  ```

#### GET /api/v1/rbac/users/{user_id}/accessible-modules
- **Description**: Get modules that user can access (has read permission)
- **Method**: GET
- **Path Parameter**: user_id (UUID)
- **Response**: List of accessible modules

---

### 10. RBAC SYNC ENDPOINTS (rbac_routes.py)

#### POST /api/v1/rbac/sync/user/{user_id}
- **Description**: Sync user's RBAC role back to users.role enum field
- **Method**: POST
- **Path Parameter**: user_id (UUID)
- **Response**: Success message with user_id
- **Purpose**: Backward compatibility with old enum field

#### POST /api/v1/rbac/sync/all-users
- **Description**: Sync all users' RBAC roles to users.role enum
- **Method**: POST
- **Response**: Statistics of sync operation
- **Purpose**: Bulk backward compatibility sync

---

### 11. OTHER ADMIN ENDPOINTS (main.py)

#### GET /api/v1/admin/sessions
- **Description**: Get all chat sessions (admin view)
- **Method**: GET
- **Response**: List of all chat sessions with user info

#### GET /api/v1/admin/audit-logs
- **Description**: Get audit logs with filtering
- **Method**: GET
- **Query Parameters**:
  - limit, offset (pagination)
  - start_date, end_date (date filtering)
- **Response**: Paginated audit log entries

#### GET /api/v1/admin/usage-metrics
- **Description**: Get usage metrics and statistics
- **Method**: GET
- **Query Parameters**:
  - start_date, end_date
- **Response**: Aggregated usage metrics

#### GET /api/v1/admin/documents
- **Description**: Get all documents (admin view)
- **Method**: GET
- **Response**: List of all uploaded documents

#### DELETE /api/v1/documents/{document_id}
- **Description**: Delete a specific document
- **Method**: DELETE
- **Path Parameter**: document_id (UUID)
- **Response**: Success message

#### DELETE /api/v1/sessions/{session_id}
- **Description**: Delete a chat session
- **Method**: DELETE
- **Path Parameter**: session_id (string)
- **Response**: Success message

---

## Summary of Missing CRUD Operations

### Users
- ✅ Create (POST /api/v1/admin/users)
- ✅ Read (GET /api/v1/admin/users)
- ✅ Update (PATCH /api/v1/admin/users/{user_id})
- ❌ Delete (NOT IMPLEMENTED - recommend soft-delete via PATCH)

### Roles
- ✅ Create (POST /api/v1/rbac/roles)
- ✅ Read (GET /api/v1/rbac/roles, GET /api/v1/rbac/roles/{role_id})
- ✅ Update (PUT /api/v1/rbac/roles/{role_id})
- ✅ Delete (DELETE /api/v1/rbac/roles/{role_id})

### Departments
- ✅ Create (POST /api/v1/rbac/departments)
- ✅ Read (GET /api/v1/rbac/departments, GET /api/v1/rbac/departments/hierarchy)
- ❌ Update (NOT IMPLEMENTED)
- ❌ Delete (NOT IMPLEMENTED - recommend soft-delete)

### Teams
- ❌ Create (NOT IMPLEMENTED)
- ✅ Read (GET /api/v1/teams)
- ❌ Update (NOT IMPLEMENTED)
- ❌ Delete (NOT IMPLEMENTED)

### Modules
- ✅ Create (POST /api/v1/rbac/modules)
- ✅ Read (GET /api/v1/rbac/modules, GET /api/v1/rbac/modules/{module_id})
- ❌ Update (NOT IMPLEMENTED)
- ❌ Delete (NOT IMPLEMENTED - recommend soft-delete)

### Permissions
- ✅ Create/Set (POST /api/v1/rbac/permissions/role-module)
- ✅ Read (GET /api/v1/rbac/permissions/matrix)
- ✅ Update (PUT /api/v1/rbac/permissions/role-module/{role_id}/{module_id})
- ✅ Bulk Update (POST /api/v1/rbac/permissions/bulk-update)

### User Role Assignments
- ✅ Create (POST /api/v1/rbac/user-roles)
- ✅ Read (GET /api/v1/rbac/user-roles/{user_id})
- ❌ Update (NOT IMPLEMENTED - delete and recreate instead)
- ✅ Delete (DELETE /api/v1/rbac/user-roles/{user_id}/{role_id})
- ✅ Bulk Assign (POST /api/v1/rbac/user-roles/bulk-assign)

### Projects
- ✅ Create (POST /api/v1/projects)
- ✅ Read (GET /api/v1/projects, GET /api/v1/projects/{project_id})
- ✅ Update (PUT /api/v1/projects/{project_id})
- ✅ Delete (DELETE /api/v1/projects/{project_id})

---

## Test Coverage Map

| Endpoint Category | Test File | Status |
|------------------|-----------|--------|
| User Management | `test_admin_rbac_fixed.py` | ✅ Fixed PATCH |
| Role Management | `test_admin_rbac_comprehensive.py` | ✅ Complete |
| Department Management | `test_admin_rbac_comprehensive.py` | ✅ Complete |
| Module Management | `test_admin_rbac_comprehensive.py` | ✅ Complete |
| Permission Matrix | `test_admin_rbac_comprehensive.py` | ✅ Complete |
| User Role Assignment | `test_admin_rbac_fixed.py` | ✅ Fixed Path |
| Team Management | Not covered | ⚠️ Needs tests |
| Project Management | Not covered | ⚠️ Needs tests |
| Permission Queries | `test_admin_rbac_comprehensive.py` | ✅ Complete |

---

## Key Discoveries

1. **User Update**: Uses PATCH not PUT at `/api/v1/admin/users/{user_id}`
2. **Role Assignment**: Correct path is `/api/v1/rbac/user-roles` (POST with user_id in body), not `/api/v1/rbac/users/{user_id}/roles`
3. **No User Deletion**: DELETE endpoint not implemented - use PATCH to set `is_active: false`
4. **Permission Matrix**: Now fully populated with 44 permissions (5 roles × 9 modules) after migration 013
5. **Two Department Endpoints**: `/api/v1/rbac/departments` (full RBAC) vs `/api/v1/departments` (simplified for frontend)
6. **Async Operations**: All RBAC read operations now properly use async/await

---

## Testing Recommendations

1. ✅ Test user PATCH updates (department, function, teams)
2. ✅ Test role assignment with correct endpoint
3. ⚠️ Add tests for team management endpoints (when implemented)
4. ⚠️ Add tests for project CRUD operations
5. ⚠️ Add tests for department/module update operations (when implemented)
6. ✅ Test permission matrix with all 44 populated permissions
7. ✅ Test bulk operations (role assignment, permission updates)

---

## Endpoint Prefix Summary

- **Admin Endpoints**: `/api/v1/admin/*` (users, sessions, audit, metrics)
- **RBAC Endpoints**: `/api/v1/rbac/*` (roles, departments, modules, permissions)
- **Teams/Projects**: `/api/v1/teams`, `/api/v1/projects`, `/api/v1/departments`
- **All require authentication** except health check endpoints
