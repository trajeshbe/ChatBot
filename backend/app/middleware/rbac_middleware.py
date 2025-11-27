"""
RBAC Middleware - Authentication and Permission Checking

This module provides middleware for FastAPI routes to enforce RBAC permissions.
"""

from typing import Callable, Optional, List
from functools import wraps
from uuid import UUID

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.rbac_service import RBACService
from app.models.database_enhanced import User


# HTTP Bearer token authentication
security = HTTPBearer(auto_error=False)


# ============================================================================
# USER AUTHENTICATION UTILITIES
# ============================================================================

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current authenticated user from request.

    This is a placeholder implementation. In production, you would:
    1. Verify JWT token from credentials.credentials
    2. Extract user_id from token
    3. Look up user in database
    4. Cache user in request.state for reuse

    For now, we'll check for a user_id in session or headers.
    """
    # Check if user is already set in request state (by another middleware)
    if hasattr(request.state, "user"):
        return request.state.user

    # TODO: Implement proper JWT token verification
    # For now, check for user_id in headers (development only!)
    user_id_header = request.headers.get("X-User-ID")
    if user_id_header:
        try:
            user_id = UUID(user_id_header)
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                # Cache in request state
                request.state.user = user
                request.state.db = db
                return user
        except (ValueError, AttributeError):
            pass

    # Check session (if session middleware is enabled)
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        # TODO: Look up user from session
        pass

    return None


async def require_authentication(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Dependency that requires user to be authenticated.

    Raises 401 if user is not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_rbac_service_with_user(
    user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
) -> tuple[RBACService, User]:
    """Get RBAC service and current user together."""
    rbac = RBACService(db)
    return rbac, user


# ============================================================================
# PERMISSION CHECKING DEPENDENCIES
# ============================================================================

class RequirePermission:
    """
    Dependency class to check if user has specific permission.

    Usage:
        @router.get("/api/v1/modules/{module_id}")
        async def get_module(
            module_id: UUID,
            _: None = Depends(RequirePermission("admin_panel", "read"))
        ):
            # User has read permission for admin_panel
            ...
    """

    def __init__(
        self,
        module_code: str,
        permission_type: str = "read",
        raise_on_deny: bool = True,
    ):
        """
        Initialize permission checker.

        Args:
            module_code: Module code to check (e.g., 'rag_chat')
            permission_type: Type of permission ('read', 'write', 'delete', 'share')
            raise_on_deny: Whether to raise HTTPException on denial (default True)
        """
        self.module_code = module_code
        self.permission_type = permission_type
        self.raise_on_deny = raise_on_deny

    async def __call__(
        self,
        user: User = Depends(require_authentication),
        db: Session = Depends(get_db),
    ) -> bool:
        """Check permission and raise exception if denied."""
        rbac = RBACService(db)

        has_permission = rbac.check_permission(
            user_id=user.id,
            module_code=self.module_code,
            permission_type=self.permission_type,
        )

        if not has_permission and self.raise_on_deny:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {self.permission_type} access to {self.module_code} required",
            )

        return has_permission


class RequireAnyPermission:
    """
    Dependency to check if user has ANY of the specified permissions.

    Usage:
        @router.get("/api/v1/data")
        async def get_data(
            _: None = Depends(RequireAnyPermission([
                ("rag_chat", "read"),
                ("file_upload", "read")
            ]))
        ):
            # User has read permission for either rag_chat OR file_upload
            ...
    """

    def __init__(
        self,
        permissions: List[tuple[str, str]],
        raise_on_deny: bool = True,
    ):
        """
        Initialize permission checker.

        Args:
            permissions: List of (module_code, permission_type) tuples
            raise_on_deny: Whether to raise HTTPException on denial
        """
        self.permissions = permissions
        self.raise_on_deny = raise_on_deny

    async def __call__(
        self,
        user: User = Depends(require_authentication),
        db: Session = Depends(get_db),
    ) -> bool:
        """Check if user has any of the permissions."""
        rbac = RBACService(db)

        for module_code, permission_type in self.permissions:
            if rbac.check_permission(user.id, module_code, permission_type):
                return True

        if self.raise_on_deny:
            perm_strings = [f"{p[1]} {p[0]}" for p in self.permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires one of: {', '.join(perm_strings)}",
            )

        return False


class RequireAllPermissions:
    """
    Dependency to check if user has ALL of the specified permissions.

    Usage:
        @router.post("/api/v1/admin/action")
        async def admin_action(
            _: None = Depends(RequireAllPermissions([
                ("admin_panel", "write"),
                ("audit_logs", "read")
            ]))
        ):
            # User has both write permission for admin_panel AND read for audit_logs
            ...
    """

    def __init__(
        self,
        permissions: List[tuple[str, str]],
        raise_on_deny: bool = True,
    ):
        """
        Initialize permission checker.

        Args:
            permissions: List of (module_code, permission_type) tuples
            raise_on_deny: Whether to raise HTTPException on denial
        """
        self.permissions = permissions
        self.raise_on_deny = raise_on_deny

    async def __call__(
        self,
        user: User = Depends(require_authentication),
        db: Session = Depends(get_db),
    ) -> bool:
        """Check if user has all of the permissions."""
        rbac = RBACService(db)

        for module_code, permission_type in self.permissions:
            if not rbac.check_permission(user.id, module_code, permission_type):
                if self.raise_on_deny:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions: {permission_type} access to {module_code} required",
                    )
                return False

        return True


class RequireRole:
    """
    Dependency to check if user has a specific role.

    Usage:
        @router.get("/api/v1/admin/settings")
        async def admin_settings(
            _: None = Depends(RequireRole("Admin"))
        ):
            # User has Admin role
            ...
    """

    def __init__(
        self,
        role_name: str,
        raise_on_deny: bool = True,
    ):
        """
        Initialize role checker.

        Args:
            role_name: Name of required role
            raise_on_deny: Whether to raise HTTPException on denial
        """
        self.role_name = role_name
        self.raise_on_deny = raise_on_deny

    async def __call__(
        self,
        user: User = Depends(require_authentication),
        db: Session = Depends(get_db),
    ) -> bool:
        """Check if user has the role."""
        rbac = RBACService(db)

        # Get user roles
        role_assignments = rbac.get_user_role_assignments(user.id, active_only=True)
        has_role = any(r.role_name == self.role_name for r in role_assignments)

        if not has_role and self.raise_on_deny:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {self.role_name} role required",
            )

        return has_role


class RequireAdmin:
    """
    Dependency to check if user is an admin.

    This is a convenience wrapper around RequireRole("Admin").

    Usage:
        @router.delete("/api/v1/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            _: None = Depends(RequireAdmin())
        ):
            # User is an admin
            ...
    """

    async def __call__(
        self,
        user: User = Depends(require_authentication),
        db: Session = Depends(get_db),
    ) -> bool:
        """Check if user is admin."""
        rbac = RBACService(db)
        is_admin = rbac.is_admin(user.id)

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator privileges required",
            )

        return True


# ============================================================================
# DECORATOR-BASED PERMISSION CHECKING (Alternative to Dependencies)
# ============================================================================

def require_permission(module_code: str, permission_type: str = "read"):
    """
    Decorator to require permission for a route handler.

    This is an alternative to using dependency injection.

    Usage:
        @router.get("/api/v1/data")
        @require_permission("rag_chat", "read")
        async def get_data(request: Request):
            user = request.state.user  # Set by decorator
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, request: Request = None, db: Session = None, **kwargs):
            # Get user from request
            if request is None:
                raise ValueError("Request object required for permission checking")

            if db is None:
                # Create new session if not provided
                db = next(get_db())

            user = await get_current_user(request, db=db)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )

            # Check permission
            rbac = RBACService(db)
            has_perm = rbac.check_permission(user.id, module_code, permission_type)

            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: {permission_type} access to {module_code} required",
                )

            # Set user in request state for use in handler
            request.state.user = user
            request.state.db = db

            return await func(*args, request=request, db=db, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# BACKWARD COMPATIBILITY WITH EXISTING ENUM-BASED SYSTEM
# ============================================================================

async def check_permission_compat(
    user: User,
    module_code: str,
    permission_type: str,
    db: Session,
) -> bool:
    """
    Backward compatible permission check.

    Checks both new RBAC system and legacy enum-based roles.

    Args:
        user: User object
        module_code: Module code to check
        permission_type: Permission type ('read', 'write', 'delete', 'share')
        db: Database session

    Returns:
        bool: True if user has permission
    """
    # Check new RBAC system first
    rbac = RBACService(db)
    if rbac.check_permission(user.id, module_code, permission_type):
        return True

    # Fallback to legacy enum-based check
    from app.models.database_enhanced import UserRole

    # Admin has all permissions
    if user.role == UserRole.ADMIN:
        return True

    # Read permissions
    if permission_type == "read":
        return user.role in [UserRole.ADMIN, UserRole.USER, UserRole.VIEWER]

    # Write permissions
    if permission_type in ["write", "delete", "share"]:
        return user.role in [UserRole.ADMIN, UserRole.USER]

    return False
