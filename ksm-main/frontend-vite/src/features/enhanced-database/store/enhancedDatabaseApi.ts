/**
 * Enhanced Database RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import type {
  DatabaseInfo,
  PropertyMapping,
  MappingStatistics,
} from '../types';

export const enhancedDatabaseApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getDatabasesWithMappings: builder.query<DatabaseInfo[], void>({
      query: () => '/notion/databases/with-mappings-test',
      transformResponse: (response: { success: boolean; data: DatabaseInfo[] }) => response.data || [],
      providesTags: ['Qdrant'],
    }),

    getMappingStatistics: builder.query<MappingStatistics, void>({
      query: () => '/notion/mapping/statistics-test',
      transformResponse: (response: { success: boolean; data: MappingStatistics }) => response.data,
      providesTags: ['Qdrant'],
    }),

    getDatabaseMappings: builder.query<PropertyMapping[], string>({
      query: (databaseId) => `/notion/mapping/database/${databaseId}`,
      transformResponse: (response: { success: boolean; data: PropertyMapping[] }) => response.data || [],
      providesTags: (_result, _error, databaseId) => [{ type: 'Qdrant', id: `mapping-${databaseId}` }],
    }),

    analyzeDatabaseMapping: builder.mutation<{ success: boolean; message?: string }, string>({
      query: (databaseId) => ({
        url: `/notion/mapping/analyze/${databaseId}`,
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; message?: string }) => response,
      invalidatesTags: (_result, _error, databaseId) => [{ type: 'Qdrant', id: `mapping-${databaseId}` }, 'Qdrant'],
    }),

    updatePropertyMapping: builder.mutation<PropertyMapping, { mappingId: number; data: Partial<PropertyMapping> }>({
      query: ({ mappingId, data }) => ({
        url: `/notion/mapping/${mappingId}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: PropertyMapping }) => response.data,
      invalidatesTags: (_result, _error, { mappingId }) => [{ type: 'Qdrant', id: `mapping-${mappingId}` }, 'Qdrant'],
    }),

    toggleMappingActive: builder.mutation<PropertyMapping, { mappingId: number; isActive: boolean }>({
      query: ({ mappingId, isActive }) => ({
        url: `/notion/mapping/${mappingId}/toggle-active`,
        method: 'PUT',
        body: { is_active: isActive },
      }),
      transformResponse: (response: { success: boolean; data: PropertyMapping }) => response.data,
      invalidatesTags: (_result, _error, { mappingId }) => [{ type: 'Qdrant', id: `mapping-${mappingId}` }, 'Qdrant'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetDatabasesWithMappingsQuery,
  useGetMappingStatisticsQuery,
  useGetDatabaseMappingsQuery,
  useAnalyzeDatabaseMappingMutation,
  useUpdatePropertyMappingMutation,
  useToggleMappingActiveMutation,
} = enhancedDatabaseApi;

