/**
 * Permission Management RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  Permission,
  Role,
  PermissionStats,
  PermissionMatrixItem,
  UpdateRolePermissionsRequest,
  LevelPermissionMatrixItem,
  LevelTemplate,
  UpdateLevelTemplateRequest,
} from '../types';

export const permissionApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getPermissionStats: builder.query<PermissionStats, void>({
      query: () => '/permission-management/statistics',
      transformResponse: (response: { success: boolean; data: PermissionStats }) => response.data,
      providesTags: ['Permission'],
    }),

    getRoles: builder.query<Role[], void>({
      query: () => '/role-management/roles-direct',
      transformResponse: (response: { success: boolean; data: Role[] }) => response.data || [],
      providesTags: ['Permission'],
    }),

    getRoleById: builder.query<Role, number>({
      query: (id) => `/role-management/roles/${id}`,
      transformResponse: (response: { success: boolean; data: Role }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'Permission', id: `role-${id}` }],
    }),

    getPermissions: builder.query<Permission[], void>({
      query: () => '/role-management/permissions',
      transformResponse: (response: { success: boolean; data: Permission[] }) => response.data || [],
      providesTags: ['Permission'],
    }),

    getRolePermissions: builder.query<PermissionMatrixItem[], number>({
      query: (roleId) => `/permission-management/roles/${roleId}/permissions`,
      transformResponse: (response: { success: boolean; data: PermissionMatrixItem[] }) => response.data || [],
      providesTags: (_result, _error, roleId) => [{ type: 'Permission', id: `role-${roleId}` }],
    }),

    updateRolePermissions: builder.mutation<{ success: boolean }, { roleId: number; data: UpdateRolePermissionsRequest }>({
      query: ({ roleId, data }) => ({
        url: `/permission-management/roles/${roleId}/permissions`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean }) => response,
      invalidatesTags: (_result, _error, { roleId }) => [{ type: 'Permission', id: `role-${roleId}` }, 'Permission'],
    }),

    bulkUpdatePermissions: builder.mutation<{ success: boolean }, { permissionIds: number[]; isActive: boolean }>({
      query: (data) => ({
        url: '/permission-management/permissions/bulk-update',
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean }) => response,
      invalidatesTags: ['Permission'],
    }),

    // Level Permission Matrix
    getMenus: builder.query<LevelPermissionMatrixItem[], void>({
      query: () => '/permission-management/menus',
      transformResponse: (response: { success: boolean; data: any[] }) => {
        const flattenMenus = (menus: any[], acc: LevelPermissionMatrixItem[] = []): LevelPermissionMatrixItem[] => {
          menus?.forEach((m: any) => {
            acc.push({
              menu_id: m.id,
              menu_name: m.name,
              menu_path: m.path,
              menu_icon: m.icon,
              parent_id: m.parent_id,
              order_index: m.order_index,
              permissions: { 
                can_read: false, 
                can_create: false, 
                can_update: false, 
                can_delete: false,
                show_in_sidebar: true // Default true untuk visibility
              }
            });
            if (Array.isArray(m.sub_menus) && m.sub_menus.length > 0) {
              flattenMenus(m.sub_menus, acc);
            }
          });
          return acc;
        };
        return flattenMenus(response.data || []);
      },
      providesTags: ['Permission'],
    }),

    getLevelTemplate: builder.query<LevelTemplate, number>({
      query: (level) => `/permission-management/level-templates/${level}`,
      transformResponse: (response: { success: boolean; data: LevelTemplate }) => response.data,
      providesTags: (_result, _error, level) => [{ type: 'Permission', id: `level-${level}` }],
    }),

    updateLevelTemplate: builder.mutation<{ success: boolean }, { level: number; data: UpdateLevelTemplateRequest }>({
      query: ({ level, data }) => ({
        url: `/permission-management/level-templates/${level}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean }) => response,
      invalidatesTags: (_result, _error, { level }) => [{ type: 'Permission', id: `level-${level}` }, 'Permission'],
    }),

    // Update global sidebar visibility for a menu (applies to all roles)
    updateMenuSidebarVisibilityGlobal: builder.mutation<
      { success: boolean; data: { menu_id: number; menu_name: string; show_in_sidebar: boolean; updated_permissions: number } },
      { menuId: number; showInSidebar: boolean }
    >({
      query: ({ menuId, showInSidebar }) => ({
        url: `/permission-management/menus/${menuId}/show-in-sidebar-global`,
        method: 'PUT',
        body: { show_in_sidebar: showInSidebar },
      }),
      transformResponse: (response: { success: boolean; data: any }) => response,
      // Invalidate semua cache yang terkait dengan Permission, termasuk getUserMenus
      invalidatesTags: ['Permission'],
    }),

    // Get user accessible menus
    getUserMenus: builder.query<any[], void>({
      query: () => '/permission-management/user-menus',
      transformResponse: (response: { success: boolean; data: any[] }) => response.data || [],
      providesTags: ['Permission'],
    }),

    // Bulk update menu order
    bulkUpdateMenuOrder: builder.mutation<
      { success: boolean; data: { updated_count: number } },
      { menu_orders: Array<{ menu_id: number; order_index: number }> }
    >({
      query: (data) => ({
        url: '/permission-management/menus/bulk-update-order',
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: any }) => response,
      invalidatesTags: ['Permission'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetPermissionStatsQuery,
  useGetRolesQuery,
  useGetRoleByIdQuery,
  useGetPermissionsQuery,
  useGetRolePermissionsQuery,
  useUpdateRolePermissionsMutation,
  useBulkUpdatePermissionsMutation,
  useGetMenusQuery,
  useGetLevelTemplateQuery,
  useUpdateLevelTemplateMutation,
  useUpdateMenuSidebarVisibilityGlobalMutation,
  useGetUserMenusQuery,
  useBulkUpdateMenuOrderMutation,
} = permissionApi;

