/**
 * Stok Barang Redux API dengan RTK Query
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  Barang,
  Supplier,
  Kategori,
  BarangListParams,
  BarangListResponse,
  BarangMasukData,
} from '../types';

// Stok Barang API endpoints
export const stokBarangApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get barang list dengan filters dan pagination
    getBarangList: builder.query<BarangListResponse, BarangListParams>({
      query: (params) => `/stok-barang/barang${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: BarangListResponse; message: string }) => {
        return response.data;
      },
      providesTags: (result) => [
        'StokBarang',
        ...(result?.items?.map(({ id }) => ({ type: 'StokBarang' as const, id })) || []),
      ],
      keepUnusedDataFor: 30, // Cache 30 detik
    }),
    
    // Get single barang by ID
    getBarangById: builder.query<Barang, number>({
      query: (id) => `/stok-barang/barang/${id}`,
      transformResponse: (response: { success: boolean; data: Barang; message: string }) => {
        return response.data;
      },
      providesTags: (_result, _error, id) => [{ type: 'StokBarang', id }],
    }),
    
    // Get dashboard data
    getDashboard: builder.query<any, void>({
      query: () => '/stok-barang/dashboard',
      transformResponse: (response: { success: boolean; data: any; message: string }) => {
        return response.data;
      },
      providesTags: ['StokBarang'],
    }),
    
    // Create new barang
    createBarang: builder.mutation<Barang, Partial<Barang>>({
      query: (data) => ({
        url: '/stok-barang/barang',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Barang; message: string }) => {
        return response.data;
      },
      invalidatesTags: ['StokBarang'],
    }),
    
    // Update barang
    updateBarang: builder.mutation<Barang, { id: number; data: Partial<Barang> }>({
      query: ({ id, data }) => ({
        url: `/stok-barang/barang/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Barang; message: string }) => {
        return response.data;
      },
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'StokBarang', id },
        'StokBarang',
      ],
    }),
    
    // Delete barang
    deleteBarang: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/stok-barang/barang/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [
        { type: 'StokBarang', id },
        'StokBarang',
      ],
    }),
    
    // Get suppliers list (static data - cache longer)
    getSuppliers: builder.query<Supplier[], void>({
      query: () => '/stok-barang/supplier',
      transformResponse: (response: { success: boolean; data: Supplier[]; message: string }) => {
        return response.data || [];
      },
      providesTags: ['Supplier'],
      keepUnusedDataFor: 300, // Cache 5 menit
    }),
    
    // Get kategori list (static data - cache longer)
    getKategori: builder.query<Kategori[], void>({
      query: () => '/stok-barang/kategori',
      transformResponse: (response: { success: boolean; data: Kategori[]; message: string }) => {
        return response.data || [];
      },
      providesTags: ['Kategori'],
      keepUnusedDataFor: 300, // Cache 5 menit
    }),
    
    // Export barang data
    exportBarang: builder.mutation<Blob, BarangListParams>({
      query: (params) => ({
        url: `/stok-barang/barang/export${buildQueryString(params)}`,
        method: 'GET',
        responseHandler: (response) => response.blob(),
      }),
    }),

    // Barang Masuk
    createBarangMasuk: builder.mutation<any, any>({
      query: (data) => ({
        url: '/stok-barang/barang-masuk',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: any; message: string }) => {
        return response.data;
      },
      invalidatesTags: ['StokBarang'],
    }),

    // Barang Keluar
    createBarangKeluar: builder.mutation<any, any>({
      query: (data) => ({
        url: '/stok-barang/barang-keluar',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: any; message: string }) => {
        return response.data;
      },
      invalidatesTags: ['StokBarang'],
    }),

    // Create Kategori
    createKategori: builder.mutation<Kategori, Partial<Kategori>>({
      query: (data) => ({
        url: '/stok-barang/kategori',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Kategori; message: string }) => {
        return response.data;
      },
      invalidatesTags: ['Kategori'],
    }),

    // Get Merk List
    getMerkList: builder.query<string[], void>({
      query: () => '/stok-barang/merk',
      transformResponse: (response: { success: boolean; data: string[]; message: string }) => {
        return response.data || [];
      },
      providesTags: ['StokBarang'],
      keepUnusedDataFor: 300,
    }),

    // Get Barang Masuk List
    getBarangMasukList: builder.query<BarangMasukData[], void>({
      query: () => '/stok-barang/barang-masuk',
      transformResponse: (response: { success: boolean; data: BarangMasukData[]; message: string } | BarangMasukData[]) => {
        // Handle both response formats
        if (Array.isArray(response)) {
          return response;
        }
        // Ensure we always return an array
        if (response && typeof response === 'object' && 'data' in response) {
          return Array.isArray(response.data) ? response.data : [];
        }
        return [];
      },
      providesTags: ['StokBarang'],
      keepUnusedDataFor: 30,
    }),
  }),
  overrideExisting: false,
});

// Export hooks untuk use di components
export const {
  useGetBarangListQuery,
  useGetBarangByIdQuery,
  useGetDashboardQuery,
  useCreateBarangMutation,
  useUpdateBarangMutation,
  useDeleteBarangMutation,
  useGetSuppliersQuery,
  useGetKategoriQuery,
  useExportBarangMutation,
  useCreateBarangMasukMutation,
  useCreateBarangKeluarMutation,
  useCreateKategoriMutation,
  useGetMerkListQuery,
  useGetBarangMasukListQuery,
} = stokBarangApi;

