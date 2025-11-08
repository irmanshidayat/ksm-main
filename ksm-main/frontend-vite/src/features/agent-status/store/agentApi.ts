/**
 * Agent Status RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import type { AgentStatusData } from '../types';

export const agentApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAgentStatus: builder.query<AgentStatusData, void>({
      query: () => '/agent/status',
      transformResponse: (response: { success: boolean; data?: AgentStatusData } | AgentStatusData) => {
        if ('success' in response && response.success && response.data) {
          return response.data;
        }
        return response as AgentStatusData;
      },
      providesTags: ['Agent'],
      keepUnusedDataFor: 15, // Cache for 15 seconds
    }),

    getAgents: builder.query<AgentStatusData[], void>({
      query: () => '/agent/list',
      transformResponse: (response: { success: boolean; data: AgentStatusData[] }) => response.data,
      providesTags: ['Agent'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetAgentStatusQuery,
  useGetAgentsQuery,
} = agentApi;

