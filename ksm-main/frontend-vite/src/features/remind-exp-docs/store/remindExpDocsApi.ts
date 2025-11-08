/**
 * Remind Exp Docs RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  RemindExpDoc,
  RemindExpDocsStatistics,
  RemindExpDocsQueryParams,
  PaginatedRemindExpDocsResponse,
  CreateRemindExpDocRequest,
} from '../types';

export const remindExpDocsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getDocuments: builder.query<PaginatedRemindExpDocsResponse, RemindExpDocsQueryParams>({
      query: (params) => `/remind-exp-docs${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: RemindExpDoc[]; pagination?: any }) => {
        const data = response.data;
        const pagination = response.pagination || {
          page: 1,
          per_page: 10,
          total: Array.isArray(data) ? data.length : 0,
          pages: 1,
        };
        
        if (Array.isArray(data)) {
          return {
            items: data,
            ...pagination,
          };
        }
        return {
          items: [],
          ...pagination,
        };
      },
      providesTags: ['RemindExpDoc'],
    }),

    getDocumentById: builder.query<RemindExpDoc, number>({
      query: (id) => `/remind-exp-docs/${id}`,
      transformResponse: (response: { success: boolean; data: RemindExpDoc }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'RemindExpDoc', id }],
    }),

    createDocument: builder.mutation<RemindExpDoc, CreateRemindExpDocRequest>({
      query: (data) => ({
        url: '/remind-exp-docs',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: RemindExpDoc }) => response.data,
      invalidatesTags: ['RemindExpDoc'],
    }),

    updateDocument: builder.mutation<RemindExpDoc, { id: number; data: Partial<CreateRemindExpDocRequest> }>({
      query: ({ id, data }) => ({
        url: `/remind-exp-docs/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: RemindExpDoc }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'RemindExpDoc', id }, 'RemindExpDoc'],
    }),

    deleteDocument: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/remind-exp-docs/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'RemindExpDoc', id }, 'RemindExpDoc'],
    }),

    getStatistics: builder.query<RemindExpDocsStatistics, void>({
      query: () => '/remind-exp-docs/statistics',
      transformResponse: (response: { success: boolean; data: RemindExpDocsStatistics }) => response.data,
      providesTags: ['RemindExpDoc'],
    }),

    exportDocuments: builder.mutation<{ download_url: string; filename: string }, RemindExpDocsQueryParams>({
      query: (params) => ({
        url: `/remind-exp-docs/export${buildQueryString(params)}`,
        method: 'GET',
        responseHandler: async (response) => {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          return { download_url: url, filename: `remind-exp-docs-${Date.now()}.xlsx` };
        },
      }),
    }),

    importDocuments: builder.mutation<{ success: boolean; imported: number; errors: string[] }, FormData>({
      query: (formData) => ({
        url: '/remind-exp-docs/import',
        method: 'POST',
        body: formData,
      }),
      transformResponse: (response: { success: boolean; imported?: number; errors?: string[] }) => ({
        success: response.success,
        imported: response.imported || 0,
        errors: response.errors || [],
      }),
      invalidatesTags: ['RemindExpDoc'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetDocumentsQuery,
  useGetDocumentByIdQuery,
  useCreateDocumentMutation,
  useUpdateDocumentMutation,
  useDeleteDocumentMutation,
  useGetStatisticsQuery,
  useExportDocumentsMutation,
  useImportDocumentsMutation,
} = remindExpDocsApi;

