/**
 * Attendance Management RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  AttendanceRecord,
  AttendanceQueryParams,
  PaginatedAttendanceResponse,
  ClockInRequest,
  ClockOutRequest,
  LeaveRequest,
  LeaveRequestQueryParams,
  PaginatedLeaveRequestResponse,
  LeaveRequestSubmit,
  DailyTask,
  TaskQueryParams,
  PaginatedTaskResponse,
  AttendanceStats,
  TodayStatus,
} from '../types';

export const attendanceApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Attendance CRUD
    getAttendances: builder.query<PaginatedAttendanceResponse, AttendanceQueryParams>({
      query: (params) => `/attendance${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: PaginatedAttendanceResponse }) => response.data,
      providesTags: (result) =>
        result && result.items
          ? [...result.items.map(({ id }) => ({ type: 'Attendance' as const, id })), 'Attendance']
          : ['Attendance'],
    }),

    getAttendanceById: builder.query<AttendanceRecord, number>({
      query: (id) => `/attendance/${id}`,
      transformResponse: (response: { success: boolean; data: AttendanceRecord }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'Attendance', id }],
    }),

    clockIn: builder.mutation<AttendanceRecord, ClockInRequest>({
      query: (data) => ({
        url: '/attendance/clock-in',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: AttendanceRecord }) => response.data,
      invalidatesTags: ['Attendance'],
    }),

    clockOut: builder.mutation<AttendanceRecord, ClockOutRequest>({
      query: ({ attendance_id, ...data }) => ({
        url: `/attendance/${attendance_id}/clock-out`,
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: AttendanceRecord }) => response.data,
      invalidatesTags: (_result, _error, { attendance_id }) => [{ type: 'Attendance', id: attendance_id }, 'Attendance'],
    }),

    // Daily Tasks CRUD
    getTasks: builder.query<PaginatedTaskResponse, TaskQueryParams>({
      query: (params) => `/attendance/tasks${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: PaginatedTaskResponse }) => response.data,
      providesTags: (result) =>
        result && result.items
          ? [...result.items.map(({ id }) => ({ type: 'DailyTask' as const, id })), 'DailyTask']
          : ['DailyTask'],
    }),

    getTaskById: builder.query<DailyTask, number>({
      query: (id) => `/attendance/tasks/${id}`,
      transformResponse: (response: { success: boolean; data: DailyTask }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'DailyTask', id }],
    }),

    createTask: builder.mutation<DailyTask, Partial<DailyTask>>({
      query: (data) => ({
        url: '/attendance/tasks',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: DailyTask }) => response.data,
      invalidatesTags: ['DailyTask'],
    }),

    updateTask: builder.mutation<DailyTask, { id: number; data: Partial<DailyTask> }>({
      query: ({ id, data }) => ({
        url: `/attendance/tasks/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: DailyTask }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'DailyTask', id }, 'DailyTask'],
    }),

    deleteTask: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/attendance/tasks/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'DailyTask', id }, 'DailyTask'],
    }),

    completeTask: builder.mutation<DailyTask, number>({
      query: (id) => ({
        url: `/attendance/tasks/${id}/complete`,
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; data: DailyTask }) => response.data,
      invalidatesTags: (_result, _error, id) => [{ type: 'DailyTask', id }, 'DailyTask'],
    }),

    // Leave Requests CRUD
    getLeaveRequests: builder.query<PaginatedLeaveRequestResponse, LeaveRequestQueryParams>({
      query: (params) => `/attendance/leave-requests${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: PaginatedLeaveRequestResponse }) => response.data,
      providesTags: (result) =>
        result && result.items
          ? [...result.items.map(({ id }) => ({ type: 'LeaveRequest' as const, id })), 'LeaveRequest']
          : ['LeaveRequest'],
    }),

    getLeaveRequestById: builder.query<LeaveRequest, number>({
      query: (id) => `/attendance/leave-requests/${id}`,
      transformResponse: (response: { success: boolean; data: LeaveRequest }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'LeaveRequest', id }],
    }),

    createLeaveRequest: builder.mutation<LeaveRequest, LeaveRequestSubmit>({
      query: (data) => ({
        url: '/attendance/leave-requests',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: LeaveRequest }) => response.data,
      invalidatesTags: ['LeaveRequest'],
    }),

    updateLeaveRequest: builder.mutation<LeaveRequest, { id: number; data: Partial<LeaveRequest> }>({
      query: ({ id, data }) => ({
        url: `/attendance/leave-requests/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: LeaveRequest }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'LeaveRequest', id }, 'LeaveRequest'],
    }),

    deleteLeaveRequest: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/attendance/leave-requests/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'LeaveRequest', id }, 'LeaveRequest'],
    }),

    approveLeaveRequest: builder.mutation<LeaveRequest, number>({
      query: (id) => ({
        url: `/attendance/leave-requests/${id}/approve`,
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; data: LeaveRequest }) => response.data,
      invalidatesTags: (_result, _error, id) => [{ type: 'LeaveRequest', id }, 'LeaveRequest'],
    }),

    rejectLeaveRequest: builder.mutation<LeaveRequest, { id: number; reason: string }>({
      query: ({ id, reason }) => ({
        url: `/attendance/leave-requests/${id}/reject`,
        method: 'POST',
        body: { reason },
      }),
      transformResponse: (response: { success: boolean; data: LeaveRequest }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'LeaveRequest', id }, 'LeaveRequest'],
    }),

    // Dashboard & Reports
    getAttendanceDashboard: builder.query<{ stats: AttendanceStats; todayStatus: TodayStatus }, { user_id?: number; date_from?: string; date_to?: string }>({
      query: (params) => `/attendance/dashboard${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: ['Attendance'],
      keepUnusedDataFor: 60, // Cache for 1 minute
    }),

    getTodayStatus: builder.query<TodayStatus, void>({
      query: () => '/attendance/today-status',
      transformResponse: (response: { success: boolean; data: TodayStatus }) => response.data,
      providesTags: ['Attendance'],
    }),

    getAttendanceReport: builder.query<any, {
      user_id?: number;
      date_from: string;
      date_to: string;
      format?: 'json' | 'excel' | 'pdf';
    }>({
      query: (params) => {
        const mappedParams: Record<string, any> = {
          ...params,
          start_date: params.date_from,
          end_date: params.date_to,
        };
        delete mappedParams.date_from;
        delete mappedParams.date_to;
        return `/attendance/report${buildQueryString(mappedParams)}`;
      },
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: ['Attendance'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetAttendancesQuery,
  useGetAttendanceByIdQuery,
  useClockInMutation,
  useClockOutMutation,
  useGetTasksQuery,
  useGetTaskByIdQuery,
  useCreateTaskMutation,
  useUpdateTaskMutation,
  useDeleteTaskMutation,
  useCompleteTaskMutation,
  useGetLeaveRequestsQuery,
  useGetLeaveRequestByIdQuery,
  useCreateLeaveRequestMutation,
  useUpdateLeaveRequestMutation,
  useDeleteLeaveRequestMutation,
  useApproveLeaveRequestMutation,
  useRejectLeaveRequestMutation,
  useGetAttendanceDashboardQuery,
  useGetTodayStatusQuery,
  useGetAttendanceReportQuery,
} = attendanceApi;

