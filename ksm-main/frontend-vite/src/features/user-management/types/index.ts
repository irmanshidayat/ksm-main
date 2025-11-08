/**
 * User Management Types
 */

export interface User {
  id: number;
  username: string;
  email: string;
  role?: string;
  role_details?: {
    id: number;
    name: string;
    department: string;
    level: number;
    is_management: boolean;
  };
  legacy_role?: string;
  created_at: string;
  is_active?: boolean;
  last_login?: string;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  description: string;
  level: number;
  is_active?: boolean;
}

export interface Role {
  id: number;
  name: string;
  code?: string;
  description: string;
  department_id: number;
  level: number;
  is_management: boolean;
  department?: Department;
}

export interface UserRole {
  id: number;
  user_id: number;
  role_id: number;
  assigned_at: string;
  expires_at?: string;
  role?: Role;
}

export interface UserQueryParams {
  page?: number;
  per_page?: number;
  search?: string;
  role?: string;
  is_active?: boolean;
}

export interface PaginatedUserResponse {
  items: User[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface CreateUserRequest {
  username: string;
  password: string;
  email: string;
  role?: string;
  department_id?: number;
  role_id?: number;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  role?: string;
  department_id?: number;
  role_id?: number;
  is_active?: boolean;
}

