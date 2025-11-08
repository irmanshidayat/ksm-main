/**
 * Qdrant Knowledge Base RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  Document,
  Collection,
  SearchResult,
  Statistics,
  DocumentsQueryParams,
  CreateCollectionRequest,
  UploadDocumentRequest,
  SearchRequest,
} from '../types';

export const qdrantApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getStatistics: builder.query<Statistics, { company_id?: string }>({
      query: (params) => `/qdrant/stats${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: Statistics }) => response.data,
      providesTags: ['Qdrant'],
    }),

    getDocuments: builder.query<Document[], DocumentsQueryParams>({
      query: (params) => `/qdrant/documents${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: { documents: Document[] } }) => 
        response.data?.documents || [],
      providesTags: ['Qdrant'],
    }),

    getDocumentById: builder.query<Document, number>({
      query: (id) => `/qdrant/documents/${id}`,
      transformResponse: (response: { success: boolean; data: Document }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'Qdrant', id: `doc-${id}` }],
    }),

    uploadDocument: builder.mutation<Document, UploadDocumentRequest>({
      query: (data) => ({
        url: '/qdrant/documents',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Document }) => response.data,
      invalidatesTags: ['Qdrant'],
    }),

    deleteDocument: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/qdrant/documents/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Qdrant', id: `doc-${id}` }, 'Qdrant'],
    }),

    getCollections: builder.query<Collection[], void>({
      query: () => '/qdrant/collections',
      transformResponse: (response: { success: boolean; data: { collections: Collection[] } }) => 
        response.data?.collections || [],
      providesTags: ['Qdrant'],
    }),

    createCollection: builder.mutation<{ success: boolean }, CreateCollectionRequest>({
      query: (data) => ({
        url: '/qdrant/collections',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean }) => response,
      invalidatesTags: ['Qdrant'],
    }),

    deleteCollection: builder.mutation<{ success: boolean }, string>({
      query: (collectionName) => ({
        url: `/qdrant/collections/${collectionName}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Qdrant'],
    }),

    search: builder.mutation<SearchResult[], SearchRequest>({
      query: (data) => ({
        url: '/qdrant/search',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: { results: SearchResult[] } }) => 
        response.data?.results || [],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetStatisticsQuery,
  useGetDocumentsQuery,
  useGetDocumentByIdQuery,
  useUploadDocumentMutation,
  useDeleteDocumentMutation,
  useGetCollectionsQuery,
  useCreateCollectionMutation,
  useDeleteCollectionMutation,
  useSearchMutation,
} = qdrantApi;

