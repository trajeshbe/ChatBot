"""
Middleware package for RBAC, authentication, and audit logging.
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

from app.middleware.audit_middleware import (
    AuditMiddleware,
    setup_audit_middleware,
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
    # Audit logging
    "AuditMiddleware",
    "setup_audit_middleware",
]
