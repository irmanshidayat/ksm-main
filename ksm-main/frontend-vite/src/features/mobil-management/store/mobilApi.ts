/**
 * Mobil Management RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  Mobil,
  MobilReservation,
  MobilQueryParams,
  ReservationQueryParams,
  PaginatedMobilResponse,
  PaginatedReservationResponse,
  MobilAvailabilityCheck,
} from '../types';

export const mobilApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Mobil CRUD
    getMobils: builder.query<PaginatedMobilResponse, MobilQueryParams>({
      query: (params) => `/mobil/mobils${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: PaginatedMobilResponse }) => response.data,
      providesTags: (result) =>
        result && result.items && Array.isArray(result.items)
          ? [...result.items.map(({ id }) => ({ type: 'Mobil' as const, id })), 'Mobil']
          : ['Mobil'],
    }),

    getMobilById: builder.query<Mobil, number>({
      query: (id) => `/mobil/mobils/${id}`,
      transformResponse: (response: { success: boolean; data: Mobil }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'Mobil', id }],
    }),

    createMobil: builder.mutation<Mobil, Partial<Mobil>>({
      query: (data) => ({
        url: '/mobil/mobils',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Mobil }) => response.data,
      invalidatesTags: ['Mobil'],
    }),

    updateMobil: builder.mutation<Mobil, { id: number; data: Partial<Mobil> }>({
      query: ({ id, data }) => ({
        url: `/mobil/mobils/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: Mobil }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Mobil', id }, 'Mobil'],
    }),

    deleteMobil: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/mobil/mobils/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Mobil', id }, 'Mobil'],
    }),

    // Reservations CRUD
    getReservations: builder.query<PaginatedReservationResponse, ReservationQueryParams>({
      query: (params) => `/mobil/requests${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: PaginatedReservationResponse }) => response.data,
      providesTags: (result) =>
        result && result.items && Array.isArray(result.items)
          ? [...result.items.map(({ id }) => ({ type: 'MobilReservation' as const, id })), 'MobilReservation']
          : ['MobilReservation'],
    }),

    getReservationById: builder.query<MobilReservation, number>({
      query: (id) => `/mobil/requests/${id}`,
      transformResponse: (response: { success: boolean; data: MobilReservation }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'MobilReservation', id }],
    }),

    createReservation: builder.mutation<MobilReservation, Partial<MobilReservation>>({
      query: (data) => ({
        url: '/mobil/requests',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: MobilReservation }) => response.data,
      invalidatesTags: ['MobilReservation', 'Mobil'],
    }),

    updateReservation: builder.mutation<MobilReservation, { id: number; data: Partial<MobilReservation> }>({
      query: ({ id, data }) => ({
        url: `/mobil/requests/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: MobilReservation }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [{ type: 'MobilReservation', id }, 'MobilReservation'],
    }),

    deleteReservation: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/mobil/requests/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'MobilReservation', id }, 'MobilReservation'],
    }),

    // Calendar data
    getMobilCalendar: builder.query<any, { month: number; year: number }>({
      query: ({ month, year }) => `/mobil/calendar?month=${month}&year=${year}`,
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: ['MobilReservation'],
      keepUnusedDataFor: 0, // Tidak cache untuk data real-time
    }),

    // Check availability
    checkMobilAvailability: builder.query<MobilAvailabilityCheck, {
      mobil_id: number;
      start_date: string;
      end_date: string;
      exclude_reservation_id?: number;
    }>({
      query: (params) => `/mobil/availability${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: MobilAvailabilityCheck }) => response.data,
      providesTags: ['MobilReservation'],
    }),

    // Get my reservations
    getMyReservations: builder.query<PaginatedReservationResponse, ReservationQueryParams>({
      query: (params) => `/mobil/requests/my${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: PaginatedReservationResponse }) => response.data,
      providesTags: (result) =>
        result && result.items && Array.isArray(result.items)
          ? [...result.items.map(({ id }) => ({ type: 'MobilReservation' as const, id })), 'MobilReservation']
          : ['MobilReservation'],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetMobilsQuery,
  useGetMobilByIdQuery,
  useCreateMobilMutation,
  useUpdateMobilMutation,
  useDeleteMobilMutation,
  useGetReservationsQuery,
  useGetReservationByIdQuery,
  useCreateReservationMutation,
  useUpdateReservationMutation,
  useDeleteReservationMutation,
  useGetMobilCalendarQuery,
  useCheckMobilAvailabilityQuery,
  useGetMyReservationsQuery,
} = mobilApi;

