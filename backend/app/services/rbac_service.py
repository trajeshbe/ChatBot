"""
RBAC Service - Role-Based Access Control Business Logic
Handles permission checking, role management, and access control
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, delete, update
from functools import lru_cache

from app.models.rbac import (
    Role,
    Department,
    Module,
    RoleModulePermission,
    UserRole,
    get_role_by_name,
    get_module_by_code,
    get_user_roles,
    get_user_permissions,
    has_permission as model_has_permission,
)


class RBACService:
    """Service for Role-Based Access Control operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # PERMISSION CHECKING
    # ========================================================================

    def check_permission(
        self,
        user_id: uuid.UUID,
        module_code: str,
        permission_type: str = "read"
    ) -> bool:
        """
        Check if user has a specific permission for a module

        Args:
            user_id: User UUID
            module_code: Module code (e.g., 'rag_chat')
            permission_type: 'read', 'write', 'delete', or 'share'

        Returns:
            bool: True if user has permission
        """
        return model_has_permission(self.db, user_id, module_code, permission_type)

    def get_user_module_permissions(self, user_id: uuid.UUID) -> Dict[str, Dict[str, bool]]:
        """
        Get all module permissions for a user

        Returns:
            dict: {module_code: {can_read: bool, can_write: bool, ...}}
        """
        permissions = get_user_permissions(self.db, user_id)

        result = {}
        for perm in permissions:
            module = self.db.query(Module).filter(Module.id == perm.module_id).first()
            if module and module.is_active:
                if module.code not in result:
                    result[module.code] = {
                        "can_read": False,
                        "can_write": False,
                        "can_delete": False,
                        "can_share": False,
                    }

                # Merge permissions (user has permission if ANY role grants it)
                result[module.code]["can_read"] = result[module.code]["can_read"] or perm.can_read
                result[module.code]["can_write"] = result[module.code]["can_write"] or perm.can_write
                result[module.code]["can_delete"] = result[module.code]["can_delete"] or perm.can_delete
                result[module.code]["can_share"] = result[module.code]["can_share"] or perm.can_share

        return result

    def get_accessible_modules(self, user_id: uuid.UUID) -> List[Module]:
        """
        Get all modules a user can access (has read permission)

        Returns:
            List of Module objects
        """
        permissions = get_user_permissions(self.db, user_id)

        # Get unique module IDs where user has read permission
        module_ids = {perm.module_id for perm in permissions if perm.can_read}

        return (
            self.db.query(Module)
            .filter(
                Module.id.in_(module_ids),
                Module.is_active == True
            )
            .order_by(Module.display_order)
            .all()
        )

    def is_admin(self, user_id: uuid.UUID) -> bool:
        """Check if user has Admin role"""
        roles = get_user_roles(self.db, user_id)
        return any(role.name == "Admin" for role in roles)

    # ========================================================================
    # ROLE MANAGEMENT
    # ========================================================================

    async def create_role(
        self,
        name: str,
        description: str = None,
        parent_role_id: uuid.UUID = None,
        is_system_role: bool = False
    ) -> Role:
        """Create a new role"""
        role = Role(
            name=name,
            description=description,
            parent_role_id=parent_role_id,
            is_system_role=is_system_role
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def get_role(self, role_id: uuid.UUID) -> Optional[Role]:
        """Get role by ID"""
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> List[Role]:
        """Get all roles"""
        result = await self.db.execute(select(Role).order_by(Role.name))
        return list(result.scalars().all())

    async def update_role(self, role_id: uuid.UUID, **kwargs) -> Optional[Role]:
        """Update role attributes"""
        role = await self.get_role(role_id)
        if not role:
            return None

        # Don't allow changing system role flag
        kwargs.pop("is_system_role", None)

        for key, value in kwargs.items():
            if hasattr(role, key):
                setattr(role, key, value)

        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete_role(self, role_id: uuid.UUID) -> bool:
        """Delete role (if not system role)"""
        role = await self.get_role(role_id)
        if not role or role.is_system_role:
            return False

        await self.db.delete(role)
        await self.db.commit()
        return True

    # ========================================================================
    # DEPARTMENT MANAGEMENT
    # ========================================================================

    def create_department(
        self,
        name: str,
        description: str = None,
        parent_department_id: uuid.UUID = None
    ) -> Department:
        """Create a new department"""
        dept = Department(
            name=name,
            description=description,
            parent_department_id=parent_department_id
        )
        self.db.add(dept)
        self.db.commit()
        self.db.refresh(dept)
        return dept

    async def get_department(self, dept_id: uuid.UUID) -> Optional[Department]:
        """Get department by ID"""
        result = await self.db.execute(select(Department).where(Department.id == dept_id))
        return result.scalar_one_or_none()

    def get_all_departments(self, active_only: bool = True) -> List[Department]:
        """Get all departments"""
        query = self.db.query(Department)
        if active_only:
            query = query.filter(Department.is_active == True)
        return query.order_by(Department.name).all()

    def get_department_hierarchy(self) -> List[Dict[str, Any]]:
        """Get departments in hierarchical structure"""
        departments = self.get_all_departments()

        # Build hierarchy
        dept_dict = {dept.id: dept.to_dict() for dept in departments}
        for dept in dept_dict.values():
            dept["children"] = []

        # Nest children under parents
        root_depts = []
        for dept in dept_dict.values():
            if dept["parent_department_id"]:
                parent_id = uuid.UUID(dept["parent_department_id"])
                if parent_id in dept_dict:
                    dept_dict[parent_id]["children"].append(dept)
            else:
                root_depts.append(dept)

        return root_depts

    # ========================================================================
    # MODULE MANAGEMENT
    # ========================================================================

    def create_module(
        self,
        name: str,
        code: str,
        description: str = None,
        icon: str = None,
        route: str = None,
        display_order: int = 0,
        is_active: bool = True
    ) -> Module:
        """Create a new module"""
        module = Module(
            name=name,
            code=code,
            description=description,
            icon=icon,
            route=route,
            display_order=display_order,
            is_active=is_active
        )
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return module

    def get_module(self, module_id: uuid.UUID) -> Optional[Module]:
        """Get module by ID"""
        return self.db.query(Module).filter(Module.id == module_id).first()

    def get_module_by_code(self, code: str) -> Optional[Module]:
        """Get module by code"""
        return get_module_by_code(self.db, code)

    async def get_all_modules(self, active_only: bool = True) -> List[Module]:
        """Get all modules"""
        stmt = select(Module)
        if active_only:
            stmt = stmt.where(Module.is_active == True)
        stmt = stmt.order_by(Module.display_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ========================================================================
    # PERMISSION MANAGEMENT
    # ========================================================================

    def set_role_permissions(
        self,
        role_id: uuid.UUID,
        module_id: uuid.UUID,
        can_read: bool = False,
        can_write: bool = False,
        can_delete: bool = False,
        can_share: bool = False
    ) -> RoleModulePermission:
        """Set permissions for a role-module combination"""
        # Check if permission exists
        perm = (
            self.db.query(RoleModulePermission)
            .filter(
                RoleModulePermission.role_id == role_id,
                RoleModulePermission.module_id == module_id
            )
            .first()
        )

        if perm:
            # Update existing
            perm.can_read = can_read
            perm.can_write = can_write
            perm.can_delete = can_delete
            perm.can_share = can_share
        else:
            # Create new
            perm = RoleModulePermission(
                role_id=role_id,
                module_id=module_id,
                can_read=can_read,
                can_write=can_write,
                can_delete=can_delete,
                can_share=can_share
            )
            self.db.add(perm)

        self.db.commit()
        self.db.refresh(perm)
        return perm

    async def get_role_permissions(self, role_id: uuid.UUID) -> List[RoleModulePermission]:
        """Get all permissions for a role"""
        stmt = select(RoleModulePermission).where(RoleModulePermission.role_id == role_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def delete_role_permission(self, role_id: uuid.UUID, module_id: uuid.UUID) -> bool:
        """Remove permission for a role-module combination"""
        perm = (
            self.db.query(RoleModulePermission)
            .filter(
                RoleModulePermission.role_id == role_id,
                RoleModulePermission.module_id == module_id
            )
            .first()
        )

        if perm:
            self.db.delete(perm)
            self.db.commit()
            return True
        return False

    # ========================================================================
    # USER ROLE ASSIGNMENT
    # ========================================================================

    async def assign_role_to_user(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        department_id: uuid.UUID = None,
        assigned_by: uuid.UUID = None,
        expires_at: datetime = None
    ) -> UserRole:
        """Assign a role to a user"""
        # Check for duplicate assignment
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.is_active == True
        )
        if department_id:
            stmt = stmt.where(UserRole.department_id == department_id)
        else:
            stmt = stmt.where(UserRole.department_id.is_(None))

        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError("User already has this role assigned")

        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            department_id=department_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )
        self.db.add(user_role)
        await self.db.commit()
        await self.db.refresh(user_role)

        # Sync to old users.role enum for backward compatibility
        await self.sync_user_role_to_enum(user_id)

        return user_role

    async def revoke_role_from_user(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        department_id: uuid.UUID = None
    ) -> bool:
        """Revoke a role from a user"""
        # Use SQLAlchemy Core delete statement for async compatibility
        stmt = delete(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        )

        if department_id:
            stmt = stmt.where(UserRole.department_id == department_id)

        result = await self.db.execute(stmt)
        await self.db.commit()

        if result.rowcount > 0:
            # Sync to old users.role enum for backward compatibility
            await self.sync_user_role_to_enum(user_id)

        return result.rowcount > 0

    async def revoke_role_by_id(self, user_role_id: uuid.UUID) -> bool:
        """Revoke a specific role assignment by its ID"""
        import logging
        logger = logging.getLogger(__name__)

        # First, get the user_id for syncing later
        select_stmt = select(UserRole).where(UserRole.id == user_role_id)
        select_result = await self.db.execute(select_stmt)
        user_role = select_result.scalar_one_or_none()

        if not user_role:
            logger.warning(f"user_role with ID {user_role_id} not found")
            return False

        user_id = user_role.user_id

        # Use SQLAlchemy Core delete statement for async compatibility
        delete_stmt = delete(UserRole).where(UserRole.id == user_role_id)
        delete_result = await self.db.execute(delete_stmt)
        await self.db.commit()

        rows_deleted = delete_result.rowcount
        logger.info(f"Deleted {rows_deleted} row(s) for user_role ID: {user_role_id}")

        if rows_deleted > 0:
            # Sync to old users.role enum for backward compatibility
            await self.sync_user_role_to_enum(user_id)

        return rows_deleted > 0

    async def get_user_role_assignments(self, user_id: uuid.UUID, active_only: bool = True) -> List[UserRole]:
        """Get all role assignments for a user"""
        stmt = select(UserRole).where(UserRole.user_id == user_id)
        if active_only:
            stmt = stmt.where(UserRole.is_active == True)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ========================================================================
    # USER MANAGEMENT SYNC
    # ========================================================================

    async def sync_user_role_to_enum(self, user_id: uuid.UUID) -> bool:
        """
        Sync RBAC role back to users.role enum field for backward compatibility.

        Logic:
        - If user has Admin role in RBAC → set users.role = 'ADMIN'
        - If user has Manager/CxO role in RBAC → set users.role = 'ADMIN'
        - If user has User role in RBAC → set users.role = 'USER'
        - If user has ReadOnly role in RBAC → set users.role = 'USER'
        - If user has multiple roles, pick the highest privilege level

        Args:
            user_id: UUID of user to sync

        Returns:
            bool: True if sync successful
        """
        from app.models.database import User

        # Get user's RBAC role assignments
        assignments = await self.get_user_role_assignments(user_id, active_only=True)

        if not assignments:
            return False

        # Get role details for each assignment
        role_names = []
        for assignment in assignments:
            role = await self.get_role(assignment.role_id)
            if role:
                role_names.append(role.name)

        # Determine highest privilege level
        if 'Admin' in role_names or 'CxO' in role_names or 'Manager' in role_names:
            enum_role = 'ADMIN'
        else:
            enum_role = 'USER'

        # Update users.role enum field
        stmt = update(User).where(User.id == user_id).values(role=enum_role)
        await self.db.execute(stmt)
        await self.db.commit()

        return True

    async def sync_all_users_to_enum(self) -> Dict[str, int]:
        """
        Sync all users' RBAC roles back to users.role enum.

        Returns:
            dict: Statistics about the sync operation
        """
        from app.models.database import User

        # Get all users
        stmt = select(User)
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        stats = {
            'total_users': len(users),
            'synced': 0,
            'skipped': 0,
            'errors': 0
        }

        for user in users:
            try:
                success = await self.sync_user_role_to_enum(user.id)
                if success:
                    stats['synced'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                stats['errors'] += 1

        return stats

    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================

    async def get_permission_matrix(self) -> Dict[str, Dict[str, Dict[str, bool]]]:
        """
        Get complete permission matrix

        Returns:
            dict: {role_name: {module_code: {can_read: bool, ...}}}
        """
        roles = await self.get_all_roles()
        modules = await self.get_all_modules()

        matrix = {}
        for role in roles:
            matrix[role.name] = {}
            permissions = await self.get_role_permissions(role.id)

            for module in modules:
                # Find permission for this role-module combo
                perm = next(
                    (p for p in permissions if p.module_id == module.id),
                    None
                )

                matrix[role.name][module.code] = {
                    "can_read": perm.can_read if perm else False,
                    "can_write": perm.can_write if perm else False,
                    "can_delete": perm.can_delete if perm else False,
                    "can_share": perm.can_share if perm else False,
                }

        return matrix


# Note: get_rbac_service dependency is defined in rbac_routes.py
