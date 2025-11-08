/**
 * Role Management RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import type {
  Department,
  Role,
  Permission,
  RolePermission,
  CreateDepartmentRequest,
  CreateRoleRequest,
  UpdateRoleRequest,
} from '../types';

export const roleApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Departments CRUD
    getDepartments: builder.query<Department[], void>({
      query: () => '/role-management/departments',
      transformResponse: (response: { success: boolean; data: Department[] }) => response.data,
      providesTags: ['Department'],
    }),

    getDepartmentById: builder.query<Department, number>({
      query: (id) => `/role-management/departments/${id}`,
      transformResponse: (response: { success: boolean; data: Department }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'Department', id }],
    }),

    createDepartment: builder.mutation<Department, CreateDepartmentRequest>({
      query: (data) => ({
        url: '/role-management/departments',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Department }) => response.data,
      invalidatesTags: ['Department'],
    }),

    updateDepartment: builder.mutation<Department, { id: number; data: Partial<Department> }>({
      query: ({ id, data }) => ({
        url: `/role-management/departments/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Department }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Department', id }, 'Department'],
    }),

    deleteDepartment: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/role-management/departments/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Department', id }, 'Department'],
    }),

    // Roles CRUD
    getRoles: builder.query<Role[], void>({
      query: () => '/role-management/roles',
      transformResponse: (response: { success: boolean; data: Role[] }) => response.data,
      providesTags: ['Role'],
    }),

    getRoleById: builder.query<Role, number>({
      query: (id) => `/role-management/roles/${id}`,
      transformResponse: (response: { success: boolean; data: Role }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'Role', id }],
    }),

    createRole: builder.mutation<Role, CreateRoleRequest>({
      query: (data) => ({
        url: '/role-management/roles',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Role }) => response.data,
      invalidatesTags: ['Role'],
    }),

    updateRole: builder.mutation<Role, { id: number; data: UpdateRoleRequest }>({
      query: ({ id, data }) => ({
        url: `/role-management/roles/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Role }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Role', id }, 'Role'],
    }),

    deleteRole: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/role-management/roles/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Role', id }, 'Role'],
    }),

    // Permissions
    getPermissions: builder.query<Permission[], void>({
      query: () => '/role-management/permissions',
      transformResponse: (response: { success: boolean; data: Permission[] }) => response.data,
      providesTags: ['Permission'],
    }),

    // Role Permissions
    getRolePermissions: builder.query<RolePermission[], number>({
      query: (roleId) => `/role-management/roles/${roleId}/permissions`,
      transformResponse: (response: { success: boolean; data: RolePermission[] }) => response.data,
      providesTags: (_result, _error, roleId) => [{ type: 'Role', id: roleId }],
    }),

    assignPermissionToRole: builder.mutation<RolePermission, { roleId: number; permissionId: number }>({
      query: ({ roleId, permissionId }) => ({
        url: `/role-management/roles/${roleId}/permissions`,
        method: 'POST',
        body: { permission_id: permissionId },
      }),
      transformResponse: (response: { success: boolean; data: RolePermission }) => response.data,
      invalidatesTags: (_result, _error, { roleId }) => [{ type: 'Role', id: roleId }, 'Role'],
    }),

    removePermissionFromRole: builder.mutation<{ success: boolean }, { roleId: number; permissionId: number }>({
      query: ({ roleId, permissionId }) => ({
        url: `/role-management/roles/${roleId}/permissions/${permissionId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, { roleId }) => [{ type: 'Role', id: roleId }, 'Role'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetDepartmentsQuery,
  useGetDepartmentByIdQuery,
  useCreateDepartmentMutation,
  useUpdateDepartmentMutation,
  useDeleteDepartmentMutation,
  useGetRolesQuery,
  useGetRoleByIdQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,
  useGetPermissionsQuery,
  useGetRolePermissionsQuery,
  useAssignPermissionToRoleMutation,
  useRemovePermissionFromRoleMutation,
} = roleApi;

