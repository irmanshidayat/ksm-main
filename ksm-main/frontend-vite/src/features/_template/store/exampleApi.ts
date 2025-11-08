/**
 * Example API (RTK Query)
 * Template untuk feature-specific RTK Query API
 * 
 * Copy dari frontend CRA:
 * - frontend/src/store/services/[feature]Api.ts
 * 
 * Adapt untuk menggunakan:
 * - baseApi dari @/app/store/services/baseApi
 */

import { baseApi } from '@/app/store/services/baseApi';

export const exampleApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getExample: builder.query({
      query: () => '/example',
      providesTags: ['Example'],
    }),
    createExample: builder.mutation({
      query: (data) => ({
        url: '/example',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Example'],
    }),
  }),
});

export const { useGetExampleQuery, useCreateExampleMutation } = exampleApi;

