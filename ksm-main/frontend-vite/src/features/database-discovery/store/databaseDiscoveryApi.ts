/**
 * Database Discovery RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  DatabaseInfo,
  EmployeeStats,
  DiscoveryStatistics,
  DatabaseDiscoveryQueryParams,
} from '../types';

export const databaseDiscoveryApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getDatabases: builder.query<DatabaseInfo[], DatabaseDiscoveryQueryParams>({
      query: (params) => `/database-discovery/databases${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: { databases: DatabaseInfo[] } }) => 
        response.data?.databases || [],
      providesTags: ['Qdrant'],
    }),

    getEmployees: builder.query<EmployeeStats[], void>({
      query: () => '/database-discovery/employees',
      transformResponse: (response: { success: boolean; data: { employees: EmployeeStats[] } }) => 
        response.data?.employees || [],
      providesTags: ['Qdrant'],
    }),

    getStatistics: builder.query<DiscoveryStatistics, void>({
      query: () => '/database-discovery/statistics',
      transformResponse: (response: { success: boolean; data: DiscoveryStatistics }) => response.data,
      providesTags: ['Qdrant'],
    }),

    runDiscovery: builder.mutation<{ success: boolean; message?: string; discovered?: number }, void>({
      query: () => ({
        url: '/database-discovery/discover',
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; message?: string; discovered?: number }) => response,
      invalidatesTags: ['Qdrant'],
    }),

    toggleSync: builder.mutation<DatabaseInfo, { databaseId: string; enabled: boolean }>({
      query: ({ databaseId, enabled }) => ({
        url: `/database-discovery/databases/${databaseId}/sync`,
        method: 'PUT',
        body: { sync_enabled: enabled },
      }),
      transformResponse: (response: { success: boolean; data: DatabaseInfo }) => response.data,
      invalidatesTags: ['Qdrant'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetDatabasesQuery,
  useGetEmployeesQuery,
  useGetStatisticsQuery,
  useRunDiscoveryMutation,
  useToggleSyncMutation,
} = databaseDiscoveryApi;

