"""
Middleware package for RBAC and authentication.
"""

from app.middleware.rbac_middleware import (
    # Authentication
    get_current_user,
    require_authentication,
    get_rbac_service_with_user,
    # Permission checking dependencies
    RequirePermission,
    RequireAnyPermission,
    RequireAllPermissions,
    RequireRole,
    RequireAdmin,
    # Decorator-based checking
    require_permission,
    # Backward compatibility
    check_permission_compat,
)

__all__ = [
    # Authentication
    "get_current_user",
    "require_authentication",
    "get_rbac_service_with_user",
    # Permission checking dependencies
    "RequirePermission",
    "RequireAnyPermission",
    "RequireAllPermissions",
    "RequireRole",
    "RequireAdmin",
    # Decorator-based checking
    "require_permission",
    # Backward compatibility
    "check_permission_compat",
]
