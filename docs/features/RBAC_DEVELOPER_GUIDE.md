# RBAC Developer Quick Reference

**Last Updated**: 2025-11-27
**Target Audience**: Backend & Frontend Developers

---

## 🚀 Quick Start

### 1. Protect an API Endpoint

```python
from fastapi import APIRouter, Depends
from app.middleware import RequirePermission

router = APIRouter()

@router.get("/api/v1/my-feature/data")
async def get_data(
    _: None = Depends(RequirePermission("module_code", "read"))
):
    """This endpoint requires read permission for 'module_code'."""
    return {"data": "sensitive information"}
```

### 2. Check Permission in Code

```python
from app.services.rbac_service import RBACService
from app.core.database import get_db

async def my_function(user_id: UUID, db: Session):
    rbac = RBACService(db)

    if rbac.check_permission(user_id, "rag_chat", "write"):
        # User can write to rag_chat
        pass
    else:
        # User cannot write
        raise HTTPException(status_code=403, detail="Permission denied")
```

### 3. Get User's Accessible Modules

```python
rbac = RBACService(db)
modules = rbac.get_accessible_modules(user_id)

for module in modules:
    print(f"{module.name} - {module.route}")
```

---

## 📋 Permission Checking Patterns

### Pattern 1: Single Permission (Dependency)

**Use Case**: Endpoint requires one specific permission

```python
from app.middleware import RequirePermission

@router.post("/api/v1/upload")
async def upload_file(
    file: UploadFile,
    _: None = Depends(RequirePermission("file_upload", "write"))
):
    """User must have write permission for file_upload."""
    # Upload logic
    pass
```

### Pattern 2: Any Permission (Dependency)

**Use Case**: User needs at least ONE of several permissions

```python
from app.middleware import RequireAnyPermission

@router.get("/api/v1/export")
async def export_data(
    _: None = Depends(RequireAnyPermission([
        ("data_extraction", "write"),
        ("web_scraping", "write"),
        ("admin_panel", "read")
    ]))
):
    """User needs write to extraction/scraping OR admin read."""
    # Export logic
    pass
```

### Pattern 3: All Permissions (Dependency)

**Use Case**: User needs ALL specified permissions

```python
from app.middleware import RequireAllPermissions

@router.post("/api/v1/admin/dangerous-action")
async def dangerous_action(
    _: None = Depends(RequireAllPermissions([
        ("admin_panel", "write"),
        ("audit_logs", "read")
    ]))
):
    """User needs BOTH permissions."""
    # Dangerous action logic
    pass
```

### Pattern 4: Role Check (Dependency)

**Use Case**: Endpoint requires specific role

```python
from app.middleware import RequireRole

@router.get("/api/v1/manager/reports")
async def manager_reports(
    _: None = Depends(RequireRole("Manager"))
):
    """Only users with Manager role can access."""
    # Report logic
    pass
```

### Pattern 5: Admin Only (Dependency)

**Use Case**: Admin-only endpoint

```python
from app.middleware import RequireAdmin

@router.delete("/api/v1/users/{user_id}")
async def delete_user(
    user_id: UUID,
    _: None = Depends(RequireAdmin())
):
    """Only admins can delete users."""
    # Delete logic
    pass
```

### Pattern 6: Decorator-Based Check

**Use Case**: Alternative to dependency injection

```python
from app.middleware import require_permission

@router.get("/api/v1/data")
@require_permission("rag_chat", "read")
async def get_data(request: Request):
    user = request.state.user  # Set by decorator
    # Data retrieval logic
    pass
```

### Pattern 7: Manual Permission Check

**Use Case**: Complex permission logic

```python
from app.middleware import get_current_user
from app.services.rbac_service import RBACService

@router.post("/api/v1/complex-action")
async def complex_action(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rbac = RBACService(db)

    # Custom permission logic
    can_read = rbac.check_permission(user.id, "module_a", "read")
    can_write = rbac.check_permission(user.id, "module_b", "write")

    if can_read and can_write:
        # Proceed
        pass
    elif can_read:
        # Read-only mode
        pass
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
```

---

## 🔧 Common Use Cases

### Use Case 1: Conditional UI Rendering (Frontend)

**Scenario**: Show/hide features based on user permissions

```typescript
// Get user's accessible modules
const response = await fetch(`/api/v1/rbac/users/${userId}/accessible-modules`);
const modules = await response.json();

// Check if user can access specific module
const canAccessChat = modules.some((m: Module) => m.code === 'rag_chat');

// Conditionally render
{canAccessChat && (
  <ChatInterface />
)}
```

### Use Case 2: Dynamic Menu Based on Permissions

**Scenario**: Show only menu items user has access to

```typescript
// Get accessible modules
const modules = await fetch(`/api/v1/rbac/users/${userId}/accessible-modules`)
  .then(r => r.json());

// Build menu
const menuItems = modules.map((module: Module) => ({
  label: module.name,
  icon: module.icon,
  route: module.route,
}));

// Render menu
<Sidebar items={menuItems} />
```

### Use Case 3: Bulk Role Assignment

**Scenario**: Assign role to multiple users at once

```python
from app.schemas.rbac_schemas import BulkRoleAssignmentRequest

@router.post("/api/v1/onboarding/assign-roles")
async def onboard_users(
    user_ids: List[UUID],
    rbac: RBACService = Depends(get_rbac_service),
    admin: User = Depends(RequireAdmin())
):
    """Bulk assign User role to new employees."""

    # Get User role
    user_role = rbac.get_role_by_name("User")

    # Assign to all users
    for user_id in user_ids:
        rbac.assign_role_to_user(
            user_id=user_id,
            role_id=user_role.id,
            assigned_by=admin.id
        )

    return {"assigned": len(user_ids)}
```

### Use Case 4: Temporary Elevated Access

**Scenario**: Grant admin access for 2 hours

```python
from datetime import datetime, timedelta

@router.post("/api/v1/admin/grant-temporary-access")
async def grant_temp_access(
    user_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
    _: None = Depends(RequireAdmin())
):
    """Grant temporary admin access for incident response."""

    admin_role = rbac.get_role_by_name("Admin")

    # Grant for 2 hours
    expires_at = datetime.now() + timedelta(hours=2)

    rbac.assign_role_to_user(
        user_id=user_id,
        role_id=admin_role.id,
        expires_at=expires_at
    )

    return {
        "message": "Admin access granted",
        "expires_at": expires_at
    }
```

### Use Case 5: Permission Matrix Export

**Scenario**: Export permissions for audit

```python
@router.get("/api/v1/admin/export-permissions")
async def export_permissions(
    rbac: RBACService = Depends(get_rbac_service),
    _: None = Depends(RequireAdmin())
):
    """Export permission matrix as CSV."""

    matrix = rbac.get_permission_matrix()

    # Convert to CSV
    csv_lines = ["Role,Module,Read,Write,Delete,Share"]

    for role_data in matrix["roles"]:
        role_name = role_data["role_name"]
        for module_code, perms in role_data["permissions"].items():
            csv_lines.append(
                f"{role_name},{module_code},"
                f"{perms['can_read']},{perms['can_write']},"
                f"{perms['can_delete']},{perms['can_share']}"
            )

    return Response(
        content="\n".join(csv_lines),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=permissions.csv"}
    )
```

---

## 🎨 Frontend Examples

### Example 1: Check Permission Before Action

```typescript
async function handleDelete(itemId: string) {
  // Check permission first
  const response = await fetch('/api/v1/rbac/permissions/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: currentUserId,
      module_code: 'file_upload',
      permission_type: 'delete'
    })
  });

  const result = await response.json();

  if (result.has_permission) {
    // Proceed with delete
    await deleteItem(itemId);
  } else {
    alert('You do not have permission to delete files');
  }
}
```

### Example 2: Dynamic Button Visibility

```typescript
const UploadButton: React.FC = () => {
  const [canUpload, setCanUpload] = useState(false);

  useEffect(() => {
    // Check permission on component mount
    checkPermission(userId, 'file_upload', 'write')
      .then(setCanUpload);
  }, [userId]);

  if (!canUpload) return null;

  return (
    <button onClick={handleUpload}>
      Upload File
    </button>
  );
};
```

### Example 3: Role-Based Route Protection

```typescript
// Next.js page with role check
export default function AdminPage() {
  const { user } = useAuth();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (user) {
      fetch(`/api/v1/rbac/users/${user.id}/permissions`)
        .then(r => r.json())
        .then(data => {
          const hasAdminRole = data.roles.some(
            (r: Role) => r.name === 'Admin'
          );
          setIsAdmin(hasAdminRole);
        });
    }
  }, [user]);

  if (!user) return <LoginPrompt />;
  if (!isAdmin) return <UnauthorizedPage />;

  return <AdminDashboard />;
}
```

---

## 📚 RBAC Service API Reference

### Permission Checking

```python
# Check single permission
rbac.check_permission(user_id, module_code, permission_type) -> bool

# Get all module permissions for user
rbac.get_user_module_permissions(user_id) -> Dict[str, Dict[str, bool]]

# Get accessible modules
rbac.get_accessible_modules(user_id) -> List[Module]

# Check if user is admin
rbac.is_admin(user_id) -> bool
```

### Role Management

```python
# Create role
rbac.create_role(name, description, parent_role_id, is_system_role) -> Role

# Get role
rbac.get_role(role_id) -> Optional[Role]
rbac.get_role_by_name(name) -> Optional[Role]

# Get all roles
rbac.get_all_roles() -> List[Role]

# Update role
rbac.update_role(role_id, **kwargs) -> Role

# Delete role
rbac.delete_role(role_id) -> None
```

### Department Management

```python
# Create department
rbac.create_department(name, description, parent_department_id) -> Department

# Get department
rbac.get_department(department_id) -> Optional[Department]

# Get all departments
rbac.get_all_departments() -> List[Department]

# Get hierarchy tree
rbac.get_department_hierarchy() -> List[Dict[str, Any]]
```

### Module Management

```python
# Create module
rbac.create_module(name, code, description, icon, route, display_order, is_active) -> Module

# Get module
rbac.get_module(module_id) -> Optional[Module]
rbac.get_module_by_code(code) -> Optional[Module]

# Get all modules
rbac.get_all_modules(active_only=True) -> List[Module]
```

### Permission Management

```python
# Set role-module permissions
rbac.set_role_permissions(
    role_id, module_id,
    can_read, can_write, can_delete, can_share
) -> RoleModulePermission

# Get role permissions
rbac.get_role_permissions(role_id) -> List[RoleModulePermission]

# Get permission matrix
rbac.get_permission_matrix() -> Dict[str, Any]

# Delete role permission
rbac.delete_role_permission(role_id, module_id) -> None
```

### User Role Assignment

```python
# Assign role to user
rbac.assign_role_to_user(
    user_id, role_id,
    department_id=None,
    assigned_by=None,
    expires_at=None
) -> UserRole

# Revoke role from user
rbac.revoke_role_from_user(user_id, role_id) -> None

# Get user's role assignments
rbac.get_user_role_assignments(user_id, active_only=True) -> List[UserRoleWithDetails]
```

---

## 🔐 Permission Types

| Permission Type | Description | Example Use Case |
|----------------|-------------|------------------|
| `read` | View/access module | View chat history |
| `write` | Create/edit content | Upload files, send messages |
| `delete` | Delete content | Delete uploaded documents |
| `share` | Share resources | Share chat sessions, export data |

---

## 📊 Default Roles & Permissions

### Admin Role
- **Permissions**: Full access to all modules (read, write, delete, share)
- **Modules**: All 10 modules
- **Use Case**: System administrators

### CxO Role
- **Permissions**: Read all, write to analytics
- **Modules**: All modules (read), evaluation + tools + rag_chat (write)
- **Use Case**: Executives, view-only with limited editing

### Manager Role
- **Permissions**: Access to most features, no admin
- **Modules**: 8 modules (no admin_panel, audit_logs)
- **Write Access**: rag_chat, file_upload, web_scraping, data_extraction, project_estimator, evaluation, tools_dashboard, weights_config
- **Use Case**: Team managers

### User Role
- **Permissions**: Standard access to core features
- **Modules**: 7 modules (core features only)
- **Write Access**: rag_chat, file_upload, web_scraping, data_extraction, project_estimator
- **Use Case**: Regular users

### ReadOnly Role
- **Permissions**: Read-only access
- **Modules**: 8 modules (all except admin_panel, audit_logs)
- **Write Access**: None
- **Use Case**: Observers, auditors

---

## 🛠️ Migration Guide

### Adding a New Module

**1. Add to Database:**
```sql
INSERT INTO modules (name, code, description, icon, route, display_order) VALUES
    ('My New Feature', 'my_feature', 'Description of feature', 'Icon', '/my-feature', 11);
```

**2. Set Permissions:**
```sql
-- Grant Admin full access
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT r.id, m.id, TRUE, TRUE, TRUE, TRUE
FROM roles r, modules m
WHERE r.name = 'Admin' AND m.code = 'my_feature';

-- Grant User read/write access
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT r.id, m.id, TRUE, TRUE, FALSE, FALSE
FROM roles r, modules m
WHERE r.name = 'User' AND m.code = 'my_feature';
```

**3. Protect Routes:**
```python
from app.middleware import RequirePermission

@router.get("/api/v1/my-feature/data")
async def get_my_feature_data(
    _: None = Depends(RequirePermission("my_feature", "read"))
):
    # Feature logic
    pass
```

### Migrating Existing Route to RBAC

**Before:**
```python
@router.get("/api/v1/data")
async def get_data():
    return {"data": "sensitive"}
```

**After:**
```python
from app.middleware import RequirePermission

@router.get("/api/v1/data")
async def get_data(
    _: None = Depends(RequirePermission("existing_module", "read"))
):
    return {"data": "sensitive"}
```

---

## 🐛 Troubleshooting

### Issue: Permission Check Always Fails

**Cause**: User doesn't have role assigned or module doesn't exist

**Solution**:
```bash
# Check if user has roles
curl http://localhost:8000/api/v1/rbac/user-roles/{user_id}

# Check if module exists
curl http://localhost:8000/api/v1/rbac/modules

# Assign role manually
curl -X POST http://localhost:8000/api/v1/rbac/user-roles \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "role_id": "role-uuid"
  }'
```

### Issue: RBAC Routes Not Registered

**Cause**: Import error or router not included in main.py

**Solution**:
```bash
# Check backend logs
docker-compose logs backend | grep "RBAC"

# Should see: "✓ RBAC Management API router registered..."

# If not, check for import errors
docker-compose logs backend | grep "ImportError"
```

### Issue: 401 Unauthorized on Protected Endpoint

**Cause**: User not authenticated

**Solution**:
```bash
# For development, pass X-User-ID header
curl http://localhost:8000/api/v1/protected \
  -H "X-User-ID: your-user-uuid"

# In production, pass JWT token
curl http://localhost:8000/api/v1/protected \
  -H "Authorization: Bearer your-jwt-token"
```

---

## 📖 Additional Resources

- **API Documentation**: http://localhost:8000/api/docs (Swagger UI)
- **GraphQL Playground**: http://localhost:8000/graphql
- **Phase 1 Docs**: `docs/features/RBAC_PHASE1_COMPLETE.md`
- **Phase 2 Docs**: `docs/features/RBAC_PHASE2_COMPLETE.md`
- **Integration Strategy**: `docs/features/RBAC_INTEGRATION_STRATEGY.md`
- **FAANG Design**: `docs/architecture/FAANG_LEVEL_RBAC_DESIGN.md`

---

**Happy Coding! 🚀**
