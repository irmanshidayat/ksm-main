/**
 * Notifications RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import type { Notification, NotificationStats } from '../types';

export const notificationApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getNotifications: builder.query<Notification[], { filter?: 'all' | 'unread' | 'read'; priority?: string }>({
      query: (params) => {
        const queryParams = new URLSearchParams();
        if (params.filter) queryParams.append('filter', params.filter);
        if (params.priority) queryParams.append('priority', params.priority);
        const queryString = queryParams.toString();
        return `/notifications${queryString ? `?${queryString}` : ''}`;
      },
      transformResponse: (response: { success: boolean; notifications: Notification[] }) => response.notifications || [],
      providesTags: ['Notification'],
    }),

    getNotificationStats: builder.query<NotificationStats, void>({
      query: () => '/notifications/stats',
      transformResponse: (response: { success: boolean; data: NotificationStats }) => response.data,
      providesTags: ['Notification'],
    }),

    markAsRead: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/notifications/${id}/read`,
        method: 'POST',
      }),
      invalidatesTags: ['Notification'],
    }),

    markAllAsRead: builder.mutation<{ success: boolean }, void>({
      query: () => ({
        url: '/notifications/read-all',
        method: 'POST',
      }),
      invalidatesTags: ['Notification'],
    }),

    deleteNotification: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/notifications/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Notification', id }, 'Notification'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetNotificationsQuery,
  useGetNotificationStatsQuery,
  useMarkAsReadMutation,
  useMarkAllAsReadMutation,
  useDeleteNotificationMutation,
} = notificationApi;

