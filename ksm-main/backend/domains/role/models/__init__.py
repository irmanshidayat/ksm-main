"""
Role Models Package
"""

from .role_models import (
    Department,
    Role,
    Permission,
    RolePermission,
    UserRole,
    CrossDepartmentAccess,
    AccessRequest,
    PermissionTemplate,
    WorkflowTemplate,
    AuditLog,
    WorkflowInstance
)

from .menu_models import (
    Menu,
    MenuPermission,
    PermissionAuditLog,
    RoleLevelTemplate
)

__all__ = [
    'Department',
    'Role',
    'Permission',
    'RolePermission',
    'UserRole',
    'CrossDepartmentAccess',
    'AccessRequest',
    'PermissionTemplate',
    'WorkflowTemplate',
    'AuditLog',
    'WorkflowInstance',
    # Menu models
    'Menu',
    'MenuPermission',
    'PermissionAuditLog',
    'RoleLevelTemplate'
]

