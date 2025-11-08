/**
 * Permission Management Types
 */

export interface Permission {
  id: number;
  module: string;
  action: string;
  resource_type: string;
  description: string;
  is_system_permission: boolean;
  is_active: boolean;
  created_at: string;
  usage_count?: number;
  roles_count?: number;
}

export interface Role {
  id: number;
  name: string;
  code: string;
  department_id: number;
  department_name?: string;
  level: number;
  description: string;
  is_management: boolean;
  is_system_role: boolean;
  is_active: boolean;
  permissions_count: number;
  users_count: number;
  created_at: string;
  updated_at: string;
}

export interface PermissionStats {
  total_permissions: number;
  total_roles: number;
  active_permissions: number;
  inactive_permissions: number;
  system_permissions: number;
  custom_permissions: number;
  most_used_permissions: Array<{
    permission: string;
    count: number;
  }>;
  recent_activities: Array<{
    id: number;
    action: string;
    user: string;
    role: string;
    timestamp: string;
  }>;
}

export interface PermissionMatrixItem {
  id: number;
  permission_id: number;
  role_id: number;
  is_granted: boolean;
  module: string;
  action: string;
  resource_type: string;
  description: string;
}

export interface UpdateRolePermissionsRequest {
  permissions: Array<{
    permission_id: number;
    is_granted: boolean;
  }>;
}

export interface LevelPermissionMatrixItem {
  menu_id: number;
  menu_name: string;
  menu_path: string;
  menu_icon?: string;
  parent_id?: number | null;
  order_index?: number;
  permissions: {
    can_read: boolean;
    can_create: boolean;
    can_update: boolean;
    can_delete: boolean;
    show_in_sidebar?: boolean;
  };
}

export interface LevelTemplate {
  id: number;
  name: string;
  level: number;
  permissions: Array<{
    menu_id: number;
    permissions: {
      can_read: boolean;
      can_create: boolean;
      can_update: boolean;
      can_delete: boolean;
      show_in_sidebar?: boolean;
    };
  }>;
}

export interface UpdateLevelTemplateRequest {
  name: string;
  permissions: Array<{
    menu_id: number;
    permissions: {
      can_read: boolean;
      can_create: boolean;
      can_update: boolean;
      can_delete: boolean;
      show_in_sidebar?: boolean;
    };
  }>;
}

