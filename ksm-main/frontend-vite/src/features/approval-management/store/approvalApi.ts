/**
 * Approval Management RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type { ApprovalRequest, ApprovalStats, ApprovalAction, ApprovalQueryParams } from '../types';

export const approvalApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getApprovalRequests: builder.query<{ items: ApprovalRequest[]; total: number; page: number; pages: number }, ApprovalQueryParams>({
      query: (params) => `/approval/requests${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: any }) => {
        const data = response.data;
        if (Array.isArray(data)) {
          return {
            items: data,
            total: data.length,
            page: 1,
            pages: 1,
          };
        }
        return data;
      },
      providesTags: ['Approval'],
    }),

    getApprovalRequestById: builder.query<ApprovalRequest, number>({
      query: (id) => `/approval/requests/${id}`,
      transformResponse: (response: { success: boolean; data: ApprovalRequest }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'Approval', id }],
    }),

    getApprovalStats: builder.query<ApprovalStats, void>({
      query: () => '/approval/stats',
      transformResponse: (response: { success: boolean; data: ApprovalStats }) => response.data,
      providesTags: ['Approval'],
    }),

    approveRequest: builder.mutation<ApprovalRequest, { id: number; comment?: string }>({
      query: ({ id, comment }) => ({
        url: `/approval/requests/${id}/approve`,
        method: 'POST',
        body: { comment },
      }),
      transformResponse: (response: { success: boolean; data: ApprovalRequest }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Approval', id }, 'Approval'],
    }),

    rejectRequest: builder.mutation<ApprovalRequest, { id: number; reason: string }>({
      query: ({ id, reason }) => ({
        url: `/approval/requests/${id}/reject`,
        method: 'POST',
        body: { reason },
      }),
      transformResponse: (response: { success: boolean; data: ApprovalRequest }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Approval', id }, 'Approval'],
    }),

    cancelRequest: builder.mutation<ApprovalRequest, number>({
      query: (id) => ({
        url: `/approval/requests/${id}/cancel`,
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; data: ApprovalRequest }) => response.data,
      invalidatesTags: (_result, _error, id) => [{ type: 'Approval', id }, 'Approval'],
    }),

    getApprovalActions: builder.query<ApprovalAction[], number>({
      query: (requestId) => `/approval/requests/${requestId}/actions`,
      transformResponse: (response: { success: boolean; data: ApprovalAction[] }) => response.data,
      providesTags: (_result, _error, requestId) => [{ type: 'Approval', id: requestId }],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetApprovalRequestsQuery,
  useGetApprovalRequestByIdQuery,
  useGetApprovalStatsQuery,
  useApproveRequestMutation,
  useRejectRequestMutation,
  useCancelRequestMutation,
  useGetApprovalActionsQuery,
} = approvalApi;

