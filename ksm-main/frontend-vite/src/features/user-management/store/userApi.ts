/**
 * User Management RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  User,
  UserQueryParams,
  PaginatedUserResponse,
  CreateUserRequest,
  UpdateUserRequest,
  Department,
  Role,
  UserRole,
} from '../types';

export const userApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Users CRUD
    getUsers: builder.query<PaginatedUserResponse | User[], UserQueryParams | void>({
      query: (params) => {
        if (!params || Object.keys(params).length === 0) {
          return '/auth/users';
        }
        return `/auth/users${buildQueryString(params)}`;
      },
      transformResponse: (response: { success: boolean; data: PaginatedUserResponse | User[] }) => {
        const data = response.data;
        // If it's an array, convert to paginated format
        if (Array.isArray(data)) {
          return {
            items: data,
            page: 1,
            per_page: data.length,
            total: data.length,
            pages: 1,
          };
        }
        return data;
      },
      providesTags: (result) =>
        result
          ? [
              ...(Array.isArray(result)
                ? result.map(({ id }) => ({ type: 'User' as const, id }))
                : result.items.map(({ id }) => ({ type: 'User' as const, id }))),
              'User',
            ]
          : ['User'],
    }),

    getUserById: builder.query<User, number>({
      query: (id) => `/auth/users/${id}`,
      transformResponse: (response: { success: boolean; data: User }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'User', id }],
    }),

    createUser: builder.mutation<User, CreateUserRequest>({
      query: (data) => ({
        url: '/auth/users',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: User }) => response.data,
      invalidatesTags: ['User'],
    }),

    updateUser: builder.mutation<User, { id: number; data: UpdateUserRequest }>({
      query: ({ id, data }) => ({
        url: `/users/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: User }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'User', id }, 'User'],
    }),

    deleteUser: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/users/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'User', id }, 'User'],
    }),

    // Departments
    getDepartments: builder.query<Department[], void>({
      query: () => '/role-management/departments',
      transformResponse: (response: { success: boolean; data: Department[] }) => response.data,
      providesTags: ['Department'],
    }),

    createDepartment: builder.mutation<Department, Partial<Department>>({
      query: (data) => ({
        url: '/role-management/departments',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Department }) => response.data,
      invalidatesTags: ['Department'],
    }),

    // Roles
    getRoles: builder.query<Role[], void>({
      query: () => '/role-management/roles',
      transformResponse: (response: { success: boolean; data: Role[] }) => response.data,
      providesTags: ['Role'],
    }),

    createRole: builder.mutation<Role, Partial<Role>>({
      query: (data) => ({
        url: '/role-management/roles',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Role }) => response.data,
      invalidatesTags: ['Role'],
    }),

    // User Roles
    getUserRoles: builder.query<UserRole[], number>({
      query: (userId) => `/role-management/users/${userId}/roles`,
      transformResponse: (response: { success: boolean; data: UserRole[] }) => response.data,
      providesTags: (_result, _error, userId) => [{ type: 'UserRole', id: userId }],
    }),

    assignRoleToUser: builder.mutation<UserRole, { userId: number; roleId: number }>({
      query: ({ userId, roleId }) => ({
        url: `/role-management/users/${userId}/roles`,
        method: 'POST',
        body: { role_id: roleId },
      }),
      transformResponse: (response: { success: boolean; data: UserRole }) => response.data,
      invalidatesTags: (_result, _error, { userId }) => [{ type: 'UserRole', id: userId }, 'User'],
    }),

    removeRoleFromUser: builder.mutation<{ success: boolean }, { userId: number; userRoleId: number }>({
      query: ({ userId, userRoleId }) => ({
        url: `/role-management/users/${userId}/roles/assignments/${userRoleId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, { userId }) => [{ type: 'UserRole', id: userId }, 'User'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetUsersQuery,
  useGetUserByIdQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeleteUserMutation,
  useGetDepartmentsQuery,
  useCreateDepartmentMutation,
  useGetRolesQuery,
  useCreateRoleMutation,
  useGetUserRolesQuery,
  useAssignRoleToUserMutation,
  useRemoveRoleFromUserMutation,
} = userApi;

