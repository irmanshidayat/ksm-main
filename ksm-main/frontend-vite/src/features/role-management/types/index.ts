/**
 * Role Management Types
 */

export interface Department {
  id: number;
  name: string;
  code: string;
  description: string;
  level: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
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
  permissions_count?: number;
  users_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: number;
  module: string;
  action: string;
  resource_type: string;
  description: string;
  is_system_permission: boolean;
  is_active: boolean;
  created_at: string;
}

export interface RolePermission {
  role_id: number;
  permission_id: number;
  permission?: Permission;
}

export interface CreateDepartmentRequest {
  name: string;
  code: string;
  description?: string;
  level: number;
}

export interface CreateRoleRequest {
  name: string;
  code: string;
  department_id: number;
  description?: string;
  level: number;
  is_management: boolean;
}

export interface UpdateRoleRequest {
  name?: string;
  code?: string;
  department_id?: number;
  description?: string;
  level?: number;
  is_management?: boolean;
  is_active?: boolean;
}

