/**
 * Knowledge AI RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import type {
  KnowledgeAIStats,
  ChatRequest,
  ChatResponse,
  SearchRequest,
  SearchResponse,
} from '../types';

export const knowledgeAiApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getStats: builder.query<KnowledgeAIStats, void>({
      query: () => '/knowledge-ai/stats',
      transformResponse: (response: { success: boolean; data: KnowledgeAIStats }) => response.data,
      providesTags: ['KnowledgeAI'],
    }),

    chat: builder.mutation<ChatResponse, ChatRequest>({
      query: (data) => ({
        url: '/knowledge-ai/chat',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: ChatResponse) => response,
    }),

    search: builder.mutation<SearchResponse, SearchRequest>({
      query: (data) => ({
        url: '/knowledge-ai/search',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: SearchResponse) => response,
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetStatsQuery,
  useChatMutation,
  useSearchMutation,
} = knowledgeAiApi;

