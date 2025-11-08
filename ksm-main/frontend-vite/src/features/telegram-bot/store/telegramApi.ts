/**
 * Telegram Bot Management RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import type { BotStatus, BotSettings, WebhookInfo } from '../types';

export const telegramApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getBotStatus: builder.query<BotStatus, void>({
      query: () => '/telegram/status',
      transformResponse: (response: { success: boolean; data?: BotStatus } | BotStatus) => {
        if ('success' in response && response.success && response.data) {
          return response.data;
        }
        return response as BotStatus;
      },
      providesTags: ['Telegram'],
    }),

    getBotSettings: builder.query<BotSettings, void>({
      query: () => '/telegram/settings',
      transformResponse: (response: { success: boolean; data: BotSettings }) => response.data,
      providesTags: ['Telegram'],
    }),

    getBotSettingsPublic: builder.query<BotSettings, void>({
      query: () => '/telegram/settings/public',
      transformResponse: (response: { success: boolean; data: BotSettings }) => response.data,
      providesTags: ['Telegram'],
    }),

    updateBotSettings: builder.mutation<BotSettings, Partial<BotSettings>>({
      query: (data) => ({
        url: '/telegram/settings',
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: BotSettings }) => response.data,
      invalidatesTags: ['Telegram'],
    }),

    testBot: builder.mutation<{ success: boolean; message: string }, void>({
      query: () => ({
        url: '/telegram/test',
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; message?: string }) => ({
        success: response.success,
        message: response.message || 'Test berhasil',
      }),
    }),

    getWebhookInfo: builder.query<WebhookInfo, void>({
      query: () => '/telegram/webhook-info',
      transformResponse: (response: { success: boolean; data: WebhookInfo }) => response.data,
      providesTags: ['Telegram'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetBotStatusQuery,
  useGetBotSettingsQuery,
  useGetBotSettingsPublicQuery,
  useUpdateBotSettingsMutation,
  useTestBotMutation,
  useGetWebhookInfoQuery,
} = telegramApi;

