/**
 * Enhanced Notion Tasks RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  NotionTask,
  EmployeeStatistics,
  Employee,
  NotionTasksQueryParams,
} from '../types';

export const notionApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getTasks: builder.query<NotionTask[], NotionTasksQueryParams>({
      query: (params) => `/notion/enhanced-tasks${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data?: NotionTask[] }) => {
        if (Array.isArray(response?.data)) {
          return response.data;
        }
        return [];
      },
      providesTags: ['Notion'],
    }),

    getStatistics: builder.query<EmployeeStatistics, void>({
      query: () => '/notion/enhanced-statistics',
      transformResponse: (response: { success: boolean; data?: EmployeeStatistics }) => {
        const data = response?.data;
        if (data && typeof data === 'object') {
          return {
            total_employees: data.total_employees ?? 0,
            total_tasks: data.total_tasks ?? 0,
            tasks_by_status: data.tasks_by_status ?? {},
            tasks_by_priority: data.tasks_by_priority ?? {},
            last_sync: data.last_sync ?? new Date().toISOString(),
          };
        }
        return {
          total_employees: 0,
          total_tasks: 0,
          tasks_by_status: {},
          tasks_by_priority: {},
          last_sync: new Date().toISOString(),
        };
      },
      providesTags: ['Notion'],
    }),

    getEmployees: builder.query<Employee[], void>({
      query: () => '/notion/enhanced-employees',
      transformResponse: (response: { success: boolean; data: { employees?: Employee[] } | Employee[] }) => {
        const data = response.data;
        if (Array.isArray(data)) {
          return data;
        }
        if (data && 'employees' in data && Array.isArray(data.employees)) {
          return data.employees;
        }
        return [];
      },
      providesTags: ['Notion'],
    }),

    syncTasks: builder.mutation<{ success: boolean; message?: string }, void>({
      query: () => ({
        url: '/notion/enhanced-sync',
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; message?: string }) => response,
      invalidatesTags: ['Notion'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetTasksQuery,
  useGetStatisticsQuery,
  useGetEmployeesQuery,
  useSyncTasksMutation,
} = notionApi;

