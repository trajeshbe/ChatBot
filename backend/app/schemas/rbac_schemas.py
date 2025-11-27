"""
Pydantic schemas for RBAC API requests and responses.

This module defines all request/response models for RBAC endpoints.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class RBACBaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ROLE SCHEMAS
# ============================================================================

class RoleBase(RBACBaseSchema):
    """Base role schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_system_role: bool = Field(False, description="System roles cannot be deleted")


class RoleCreate(RoleBase):
    """Schema for creating a new role."""

    parent_role_id: Optional[UUID] = Field(None, description="Parent role for hierarchy")


class RoleUpdate(RBACBaseSchema):
    """Schema for updating a role."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_role_id: Optional[UUID] = None


class RoleResponse(RoleBase):
    """Schema for role response."""

    id: UUID
    parent_role_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class RoleWithPermissions(RoleResponse):
    """Role with permission counts."""

    total_permissions: int = Field(0, description="Total number of module permissions")
    accessible_modules: int = Field(0, description="Number of modules with read access")


# ============================================================================
# DEPARTMENT SCHEMAS
# ============================================================================

class DepartmentBase(RBACBaseSchema):
    """Base department schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class DepartmentCreate(DepartmentBase):
    """Schema for creating a new department."""

    parent_department_id: Optional[UUID] = Field(None, description="Parent department for hierarchy")


class DepartmentUpdate(RBACBaseSchema):
    """Schema for updating a department."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_department_id: Optional[UUID] = None


class DepartmentResponse(DepartmentBase):
    """Schema for department response."""

    id: UUID
    parent_department_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class DepartmentHierarchy(DepartmentResponse):
    """Department with hierarchical children."""

    children: List['DepartmentHierarchy'] = Field(default_factory=list)
    user_count: int = Field(0, description="Number of users in this department")


# ============================================================================
# MODULE SCHEMAS
# ============================================================================

class ModuleBase(RBACBaseSchema):
    """Base module schema."""

    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50, description="Unique module code")
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50, description="Lucide icon name")
    route: Optional[str] = Field(None, max_length=100, description="Frontend route path")


class ModuleCreate(ModuleBase):
    """Schema for creating a new module."""

    display_order: int = Field(0, ge=0, description="Order in navigation")
    is_active: bool = Field(True, description="Whether module is active")


class ModuleUpdate(RBACBaseSchema):
    """Schema for updating a module."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    route: Optional[str] = Field(None, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ModuleResponse(ModuleBase):
    """Schema for module response."""

    id: UUID
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================================
# PERMISSION SCHEMAS
# ============================================================================

class PermissionBase(RBACBaseSchema):
    """Base permission schema."""

    can_read: bool = Field(False, description="Can view/access module")
    can_write: bool = Field(False, description="Can create/edit in module")
    can_delete: bool = Field(False, description="Can delete from module")
    can_share: bool = Field(False, description="Can share resources")


class PermissionSet(PermissionBase):
    """Permission set for a module."""

    module_code: str = Field(..., description="Module code")
    module_name: Optional[str] = Field(None, description="Module display name")


class RolePermissionCreate(PermissionBase):
    """Schema for creating role-module permission."""

    role_id: UUID
    module_id: UUID


class RolePermissionUpdate(PermissionBase):
    """Schema for updating role-module permission."""

    pass


class RolePermissionResponse(PermissionBase):
    """Schema for role-module permission response."""

    id: UUID
    role_id: UUID
    module_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


class PermissionMatrixRow(RBACBaseSchema):
    """Single row in permission matrix."""

    role_id: UUID
    role_name: str
    permissions: Dict[str, PermissionBase] = Field(
        default_factory=dict,
        description="Map of module_code to permissions"
    )


class PermissionMatrix(RBACBaseSchema):
    """Complete permission matrix."""

    roles: List[PermissionMatrixRow]
    modules: List[ModuleResponse]


# ============================================================================
# USER ROLE ASSIGNMENT SCHEMAS
# ============================================================================

class UserRoleBase(RBACBaseSchema):
    """Base user role assignment schema."""

    user_id: UUID
    role_id: UUID
    department_id: Optional[UUID] = None


class UserRoleCreate(UserRoleBase):
    """Schema for assigning role to user."""

    assigned_by: Optional[UUID] = Field(None, description="Admin user who assigned the role")
    expires_at: Optional[datetime] = Field(None, description="Role expiration (for temporary access)")
    notes: Optional[str] = Field(None, max_length=500)


class UserRoleUpdate(RBACBaseSchema):
    """Schema for updating user role assignment."""

    department_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class UserRoleResponse(UserRoleBase):
    """Schema for user role assignment response."""

    id: UUID
    assigned_by: Optional[UUID] = None
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    notes: Optional[str] = None


class UserRoleWithDetails(UserRoleResponse):
    """User role assignment with related details."""

    role_name: str
    department_name: Optional[str] = None
    assigned_by_username: Optional[str] = None


# ============================================================================
# USER PERMISSION SCHEMAS
# ============================================================================

class UserPermissionsResponse(RBACBaseSchema):
    """User's consolidated permissions."""

    user_id: UUID
    username: str
    roles: List[RoleResponse]
    departments: List[DepartmentResponse]
    permissions: Dict[str, PermissionBase] = Field(
        default_factory=dict,
        description="Map of module_code to permissions"
    )
    accessible_modules: List[ModuleResponse] = Field(
        default_factory=list,
        description="Modules user can access (has read permission)"
    )


# ============================================================================
# PERMISSION CHECK SCHEMAS
# ============================================================================

class PermissionCheckRequest(RBACBaseSchema):
    """Request to check if user has permission."""

    user_id: UUID
    module_code: str
    permission_type: str = Field("read", description="read, write, delete, or share")


class PermissionCheckResponse(RBACBaseSchema):
    """Response for permission check."""

    has_permission: bool
    user_id: UUID
    module_code: str
    permission_type: str
    reason: Optional[str] = Field(None, description="Explanation if denied")


# ============================================================================
# BULK OPERATION SCHEMAS
# ============================================================================

class BulkRoleAssignmentRequest(RBACBaseSchema):
    """Bulk assign roles to multiple users."""

    user_ids: List[UUID] = Field(..., min_length=1)
    role_id: UUID
    department_id: Optional[UUID] = None
    assigned_by: Optional[UUID] = None


class BulkRoleAssignmentResponse(RBACBaseSchema):
    """Result of bulk role assignment."""

    successful: int = Field(0, description="Number of successful assignments")
    failed: int = Field(0, description="Number of failed assignments")
    errors: List[str] = Field(default_factory=list)


class BulkPermissionUpdateRequest(RBACBaseSchema):
    """Bulk update permissions for a role."""

    role_id: UUID
    permissions: Dict[str, PermissionBase] = Field(
        ...,
        description="Map of module_code to permission settings"
    )


# ============================================================================
# LIST RESPONSE SCHEMAS
# ============================================================================

class RoleListResponse(RBACBaseSchema):
    """Paginated list of roles."""

    items: List[RoleResponse]
    total: int
    page: int = 1
    page_size: int = 50


class DepartmentListResponse(RBACBaseSchema):
    """Paginated list of departments."""

    items: List[DepartmentResponse]
    total: int
    page: int = 1
    page_size: int = 50


class ModuleListResponse(RBACBaseSchema):
    """Paginated list of modules."""

    items: List[ModuleResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class RBACErrorResponse(RBACBaseSchema):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None


# Update forward references for recursive models
DepartmentHierarchy.model_rebuild()
