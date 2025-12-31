"""
RBAC API routes for role, department, module, and permission management.

This module provides REST API endpoints for managing the RBAC system.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.tier_1.infrastructure.database import get_db
from app.tier_1.platform_services.rbac_service import RBACService
from app.schemas.rbac_schemas import (
    # Role schemas
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithPermissions,
    RoleListResponse,
    # Department schemas
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentHierarchy,
    DepartmentListResponse,
    # Module schemas
    ModuleCreate,
    ModuleUpdate,
    ModuleResponse,
    ModuleListResponse,
    # Permission schemas
    RolePermissionCreate,
    RolePermissionUpdate,
    RolePermissionResponse,
    PermissionMatrix,
    # User role schemas
    UserRoleCreate,
    UserRoleUpdate,
    UserRoleResponse,
    UserRoleWithDetails,
    UserPermissionsResponse,
    # Permission check schemas
    PermissionCheckRequest,
    PermissionCheckResponse,
    # Bulk operation schemas
    BulkRoleAssignmentRequest,
    BulkRoleAssignmentResponse,
    BulkPermissionUpdateRequest,
    # Error schemas
    RBACErrorResponse,
)


# Create router
router = APIRouter(
    prefix="/api/v1/rbac",
    tags=["RBAC Management"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        404: {"description": "Resource not found"},
    },
)


# ============================================================================
# DEPENDENCY: Get RBAC Service
# ============================================================================

def get_rbac_service(db: AsyncSession = Depends(get_db)) -> RBACService:
    """Get RBAC service instance."""
    return RBACService(db)


# ============================================================================
# ROLE ENDPOINTS
# ============================================================================

@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
)
async def create_role(
    role: RoleCreate,
    rbac: RBACService = Depends(get_rbac_service),
):
    """
    Create a new role.

    - **name**: Unique role name
    - **description**: Role description
    - **parent_role_id**: Parent role for hierarchy (optional)
    - **is_system_role**: Whether this is a system role (cannot be deleted)
    """
    try:
        new_role = await rbac.create_role(
            name=role.name,
            description=role.description,
            parent_role_id=role.parent_role_id,
            is_system_role=role.is_system_role,
        )
        return RoleResponse.model_validate(new_role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating role: {str(e)}")


@router.get(
    "/roles",
    response_model=RoleListResponse,
    summary="List all roles",
)
async def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_system: bool = Query(True, description="Include system roles"),
    rbac: RBACService = Depends(get_rbac_service),
):
    """List all roles with pagination."""
    try:
        roles = await rbac.get_all_roles()

        # Filter out system roles if requested
        if not include_system:
            roles = [r for r in roles if not r.is_system_role]

        # Pagination
        total = len(roles)
        start = (page - 1) * page_size
        end = start + page_size
        items = roles[start:end]

        return RoleListResponse(
            items=[RoleResponse.model_validate(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing roles: {str(e)}")


@router.get(
    "/roles/{role_id}",
    response_model=RoleResponse,
    summary="Get role by ID",
)
async def get_role(
    role_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Get a specific role by ID."""
    role = rbac.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"Role {role_id} not found")
    return RoleResponse.model_validate(role)


@router.put(
    "/roles/{role_id}",
    response_model=RoleResponse,
    summary="Update role",
)
async def update_role(
    role_id: UUID,
    role: RoleUpdate,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Update an existing role."""
    try:
        # Check if role exists
        existing = rbac.get_role(role_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Role {role_id} not found")

        # Check if system role
        if existing.is_system_role:
            raise HTTPException(
                status_code=403,
                detail="Cannot modify system roles"
            )

        # Update role
        update_data = role.model_dump(exclude_unset=True)
        updated_role = rbac.update_role(role_id, **update_data)

        return RoleResponse.model_validate(updated_role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating role: {str(e)}")


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete role",
)
async def delete_role(
    role_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
):
    """
    Delete a role.

    System roles cannot be deleted.
    """
    try:
        role = rbac.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail=f"Role {role_id} not found")

        if role.is_system_role:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete system roles"
            )

        rbac.delete_role(role_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting role: {str(e)}")


# ============================================================================
# DEPARTMENT ENDPOINTS
# ============================================================================

@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department",
)
async def create_department(
    department: DepartmentCreate,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Create a new department."""
    try:
        new_dept = rbac.create_department(
            name=department.name,
            description=department.description,
            parent_department_id=department.parent_department_id,
        )
        return DepartmentResponse.model_validate(new_dept)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating department: {str(e)}")


@router.get(
    "/departments",
    response_model=DepartmentListResponse,
    summary="List all departments",
)
async def list_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    rbac: RBACService = Depends(get_rbac_service),
):
    """List all departments with pagination."""
    try:
        departments = await rbac.get_all_departments()

        # Pagination
        total = len(departments)
        start = (page - 1) * page_size
        end = start + page_size
        items = departments[start:end]

        return DepartmentListResponse(
            items=[DepartmentResponse.model_validate(d) for d in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing departments: {str(e)}")


@router.get(
    "/departments/hierarchy",
    response_model=List[DepartmentHierarchy],
    summary="Get department hierarchy tree",
)
async def get_department_hierarchy(
    rbac: RBACService = Depends(get_rbac_service),
):
    """Get departments as hierarchical tree structure."""
    try:
        hierarchy = await rbac.get_department_hierarchy()
        return hierarchy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting hierarchy: {str(e)}")


@router.get(
    "/departments/{department_id}",
    response_model=DepartmentResponse,
    summary="Get department by ID",
)
async def get_department(
    department_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Get a specific department by ID."""
    department = rbac.get_department(department_id)
    if not department:
        raise HTTPException(status_code=404, detail=f"Department {department_id} not found")
    return DepartmentResponse.model_validate(department)


# ============================================================================
# MODULE ENDPOINTS
# ============================================================================

@router.post(
    "/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new module",
)
async def create_module(
    module: ModuleCreate,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Create a new application module."""
    try:
        new_module = rbac.create_module(
            name=module.name,
            code=module.code,
            description=module.description,
            icon=module.icon,
            route=module.route,
            display_order=module.display_order,
            is_active=module.is_active,
        )
        return ModuleResponse.model_validate(new_module)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating module: {str(e)}")


@router.get(
    "/modules",
    response_model=ModuleListResponse,
    summary="List all modules",
)
async def list_modules(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    active_only: bool = Query(False, description="Only return active modules"),
    rbac: RBACService = Depends(get_rbac_service),
):
    """List all application modules."""
    try:
        modules = await rbac.get_all_modules()

        # Filter active only if requested
        if active_only:
            modules = [m for m in modules if m.is_active]

        # Pagination
        total = len(modules)
        start = (page - 1) * page_size
        end = start + page_size
        items = modules[start:end]

        return ModuleListResponse(
            items=[ModuleResponse.model_validate(m) for m in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing modules: {str(e)}")


@router.get(
    "/modules/{module_id}",
    response_model=ModuleResponse,
    summary="Get module by ID",
)
async def get_module(
    module_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Get a specific module by ID."""
    module = rbac.get_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module {module_id} not found")
    return ModuleResponse.model_validate(module)


# ============================================================================
# PERMISSION ENDPOINTS
# ============================================================================

@router.get(
    "/permissions/matrix",
    summary="Get complete permission matrix",
)
async def get_permission_matrix(
    rbac: RBACService = Depends(get_rbac_service),
):
    """
    Get the complete permission matrix showing all role-module permissions.

    Returns a matrix with roles (rows) and modules (columns) with permissions.
    Format: {role_name: {module_code: {can_read, can_write, can_delete, can_share}}}
    """
    try:
        matrix_data = await rbac.get_permission_matrix()
        roles_list = await rbac.get_all_roles()
        modules_list = await rbac.get_all_modules()

        # Transform to expected frontend format
        roles = []
        for role in roles_list:
            role_perms = matrix_data.get(role.name, {})
            roles.append({
                "role_id": str(role.id),
                "role_name": role.name,
                "permissions": role_perms
            })

        modules = [
            {
                "id": str(m.id),
                "name": m.name,
                "code": m.code,
                "description": m.description,
                "icon": m.icon,
                "route": m.route,
                "display_order": m.display_order,
                "is_active": m.is_active
            }
            for m in modules_list
        ]

        return {"roles": roles, "modules": modules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting permission matrix: {str(e)}")


@router.post(
    "/permissions/role-module",
    response_model=RolePermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set role-module permissions",
)
async def set_role_module_permissions(
    permission: RolePermissionCreate,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Set permissions for a role-module combination."""
    try:
        perm = rbac.set_role_permissions(
            role_id=permission.role_id,
            module_id=permission.module_id,
            can_read=permission.can_read,
            can_write=permission.can_write,
            can_delete=permission.can_delete,
            can_share=permission.can_share,
        )
        return RolePermissionResponse.model_validate(perm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting permissions: {str(e)}")


@router.put(
    "/permissions/role-module/{role_id}/{module_id}",
    response_model=RolePermissionResponse,
    summary="Update role-module permissions",
)
async def update_role_module_permissions(
    role_id: UUID,
    module_id: UUID,
    permission: RolePermissionUpdate,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Update existing role-module permissions."""
    try:
        perm = rbac.set_role_permissions(
            role_id=role_id,
            module_id=module_id,
            can_read=permission.can_read,
            can_write=permission.can_write,
            can_delete=permission.can_delete,
            can_share=permission.can_share,
        )
        return RolePermissionResponse.model_validate(perm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating permissions: {str(e)}")


@router.post(
    "/permissions/bulk-update",
    response_model=dict,
    summary="Bulk update permissions for a role",
)
async def bulk_update_permissions(
    request: BulkPermissionUpdateRequest,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Bulk update permissions for a role across multiple modules."""
    try:
        successful = 0
        failed = 0
        errors = []

        for module_code, perms in request.permissions.items():
            try:
                # Get module by code
                module = rbac.get_module_by_code(module_code)
                if not module:
                    errors.append(f"Module {module_code} not found")
                    failed += 1
                    continue

                # Set permissions
                rbac.set_role_permissions(
                    role_id=request.role_id,
                    module_id=module.id,
                    can_read=perms.can_read,
                    can_write=perms.can_write,
                    can_delete=perms.can_delete,
                    can_share=perms.can_share,
                )
                successful += 1
            except Exception as e:
                errors.append(f"Error updating {module_code}: {str(e)}")
                failed += 1

        return {
            "successful": successful,
            "failed": failed,
            "errors": errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk update: {str(e)}")


# ============================================================================
# USER ROLE ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post(
    "/user-roles",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign role to user",
)
async def assign_role_to_user(
    assignment: UserRoleCreate,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Assign a role to a user."""
    try:
        user_role = await rbac.assign_role_to_user(
            user_id=assignment.user_id,
            role_id=assignment.role_id,
            department_id=assignment.department_id,
            assigned_by=assignment.assigned_by,
            expires_at=assignment.expires_at,
        )

        # Get role details for response
        role = await rbac.get_role(user_role.role_id)
        dept = None
        if user_role.department_id:
            dept = await rbac.get_department(user_role.department_id)

        return {
            "id": str(user_role.id),
            "user_id": str(user_role.user_id),
            "role_id": str(user_role.role_id),
            "role_name": role.name if role else "Unknown",
            "department_id": str(user_role.department_id) if user_role.department_id else None,
            "department_name": dept.name if dept else None,
            "assigned_by": str(user_role.assigned_by) if user_role.assigned_by else None,
            "assigned_at": user_role.assigned_at.isoformat() if user_role.assigned_at else None,
            "expires_at": user_role.expires_at.isoformat() if user_role.expires_at else None,
            "is_active": user_role.is_active if hasattr(user_role, 'is_active') else True,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning role: {str(e)}")


@router.get(
    "/user-roles/{user_id}",
    response_model=List[UserRoleWithDetails],
    summary="Get user's role assignments",
)
async def get_user_roles(
    user_id: UUID,
    active_only: bool = Query(True, description="Only return active assignments"),
    rbac: RBACService = Depends(get_rbac_service),
):
    """Get all role assignments for a user."""
    try:
        assignments = await rbac.get_user_role_assignments(user_id, active_only=active_only)

        # Transform to include role and department details
        result = []
        for assignment in assignments:
            role = await rbac.get_role(assignment.role_id)
            dept = None
            if assignment.department_id:
                dept = await rbac.get_department(assignment.department_id)

            result.append({
                "id": str(assignment.id),
                "user_id": str(assignment.user_id),
                "role_id": str(assignment.role_id),
                "role_name": role.name if role else "Unknown",
                "department_id": str(assignment.department_id) if assignment.department_id else None,
                "department_name": dept.name if dept else None,
                "granted_by": str(assignment.assigned_by) if assignment.assigned_by else None,
                "granted_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                "expires_at": assignment.expires_at.isoformat() if assignment.expires_at else None,
                "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                "is_active": assignment.is_active if hasattr(assignment, 'is_active') else True,
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user roles: {str(e)}")


@router.delete(
    "/user-roles/{user_id}/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke role from user",
)
async def revoke_role_from_user(
    user_id: UUID,
    role_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Revoke a role from a user."""
    try:
        success = await rbac.revoke_role_from_user(user_id, role_id)
        if not success:
            raise HTTPException(status_code=404, detail="Role assignment not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error revoking role: {str(e)}")


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


@router.post(
    "/user-roles/bulk-assign",
    response_model=BulkRoleAssignmentResponse,
    summary="Bulk assign role to multiple users",
)
async def bulk_assign_role(
    request: BulkRoleAssignmentRequest,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Assign a role to multiple users at once."""
    successful = 0
    failed = 0
    errors = []

    for user_id in request.user_ids:
        try:
            rbac.assign_role_to_user(
                user_id=user_id,
                role_id=request.role_id,
                department_id=request.department_id,
                assigned_by=request.assigned_by,
            )
            successful += 1
        except Exception as e:
            errors.append(f"User {user_id}: {str(e)}")
            failed += 1

    return BulkRoleAssignmentResponse(
        successful=successful,
        failed=failed,
        errors=errors,
    )


# ============================================================================
# USER MANAGEMENT SYNC ENDPOINTS
# ============================================================================

@router.post(
    "/sync/user/{user_id}",
    summary="Sync user's RBAC role to old users.role enum",
)
async def sync_user_role_to_enum(
    user_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
):
    """
    Sync a specific user's RBAC role back to users.role enum field.

    This ensures backward compatibility with code that uses the old enum field.
    """
    try:
        success = await rbac.sync_user_role_to_enum(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User has no RBAC roles")
        return {"message": "User role synced successfully", "user_id": str(user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing user role: {str(e)}")


@router.post(
    "/sync/all-users",
    summary="Sync all users' RBAC roles to old users.role enum",
)
async def sync_all_users_to_enum(
    rbac: RBACService = Depends(get_rbac_service),
):
    """
    Sync all users' RBAC roles back to users.role enum fields.

    This ensures backward compatibility with code that uses the old enum field.
    """
    try:
        stats = await rbac.sync_all_users_to_enum()
        return {
            "message": "All users synced",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing users: {str(e)}")


# ============================================================================
# USER PERMISSION QUERY ENDPOINTS
# ============================================================================

@router.get(
    "/users/{user_id}/permissions",
    response_model=UserPermissionsResponse,
    summary="Get user's consolidated permissions",
)
async def get_user_permissions(
    user_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
):
    """
    Get all permissions for a user across all their roles.

    Returns consolidated permissions and list of accessible modules.
    """
    try:
        # Get user module permissions
        permissions = rbac.get_user_module_permissions(user_id)

        # Get accessible modules
        accessible_modules = rbac.get_accessible_modules(user_id)

        # Get user roles
        role_assignments = rbac.get_user_role_assignments(user_id)

        # Build response
        return UserPermissionsResponse(
            user_id=user_id,
            username="",  # TODO: Get from user service
            roles=[],  # TODO: Get role details
            departments=[],  # TODO: Get department details
            permissions=permissions,
            accessible_modules=[ModuleResponse.model_validate(m) for m in accessible_modules],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user permissions: {str(e)}")


@router.post(
    "/permissions/check",
    response_model=PermissionCheckResponse,
    summary="Check if user has permission",
)
async def check_permission(
    request: PermissionCheckRequest,
    rbac: RBACService = Depends(get_rbac_service),
):
    """
    Check if a user has a specific permission for a module.

    - **user_id**: User to check
    - **module_code**: Module code (e.g., 'rag_chat')
    - **permission_type**: Type of permission ('read', 'write', 'delete', 'share')
    """
    try:
        has_perm = rbac.check_permission(
            user_id=request.user_id,
            module_code=request.module_code,
            permission_type=request.permission_type,
        )

        reason = None
        if not has_perm:
            reason = f"User does not have {request.permission_type} permission for {request.module_code}"

        return PermissionCheckResponse(
            has_permission=has_perm,
            user_id=request.user_id,
            module_code=request.module_code,
            permission_type=request.permission_type,
            reason=reason,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking permission: {str(e)}")


@router.get(
    "/users/{user_id}/accessible-modules",
    response_model=List[ModuleResponse],
    summary="Get modules accessible to user",
)
async def get_accessible_modules(
    user_id: UUID,
    rbac: RBACService = Depends(get_rbac_service),
):
    """Get list of modules that user can access (has read permission)."""
    try:
        modules = rbac.get_accessible_modules(user_id)
        return [ModuleResponse.model_validate(m) for m in modules]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting accessible modules: {str(e)}")
