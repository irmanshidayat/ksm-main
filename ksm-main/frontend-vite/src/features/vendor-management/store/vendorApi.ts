/**
 * Vendor Management API
 * RTK Query API slice untuk Vendor Management
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import { API_ENDPOINTS } from '@/core/api/endpoints';
import { ENV } from '@/core/config/env';
import type {
  Vendor,
  VendorListParams,
  VendorListResponse,
  BulkImportRequest,
  BulkImportResponse,
  VendorDashboardData,
  VendorSelfRegistrationRequest,
  VendorSelfRegistrationResponse,
} from '../types';

// Helper function untuk mengekstrak path dari full URL untuk digunakan dengan baseApi
// baseApi sudah punya baseUrl, jadi kita hanya perlu path relatif
const extractApiPath = (fullUrl: string): string => {
  const baseUrl = ENV.API_URL.replace(/\/+$/, '').replace(/\/api\/?$/i, '');
  const apiPrefix = `${baseUrl}/api`;
  if (fullUrl.startsWith(apiPrefix)) {
    return fullUrl.substring(apiPrefix.length);
  }
  // Jika tidak match, return as is (mungkin sudah path)
  return fullUrl;
};

export const vendorApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get vendors list dengan filters dan pagination
    getVendors: builder.query<VendorListResponse, VendorListParams>({
      query: (params) => `/vendor${buildQueryString(params)}`,
      providesTags: (result) => [
        'Vendor',
        ...(result?.items?.map(({ id }) => ({ type: 'Vendor' as const, id })) || []),
      ],
      keepUnusedDataFor: 60, // Cache 60 detik
    }),

    // Get single vendor by ID
    getVendorById: builder.query<Vendor, number>({
      query: (id) => `/vendor/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Vendor', id }],
    }),

    // Get vendor dashboard data
    getVendorDashboard: builder.query<VendorDashboardData, void>({
      query: () => extractApiPath(API_ENDPOINTS.VENDOR.DASHBOARD),
      transformResponse: (response: { success: boolean; data: VendorDashboardData }) => response.data,
      providesTags: ['Vendor'],
    }),

    // Get vendor profile
    getVendorProfile: builder.query<Vendor, void>({
      query: () => '/vendor/profile',
      transformResponse: (response: { success: boolean; data: Vendor }) => response.data,
      providesTags: ['Vendor'],
    }),

    // Update vendor profile
    updateVendorProfile: builder.mutation<Vendor, Partial<Vendor>>({
      query: (data) => ({
        url: '/vendor/profile',
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Vendor'],
    }),

    // Get vendor requests (for vendor to see available requests)
    getVendorRequests: builder.query<any[], { limit?: number; offset?: number; category_filter?: string }>({
      query: (params) => `/vendor/requests${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: any[]; pagination?: any }) => response.data,
      providesTags: ['Vendor'],
    }),

    // Get vendor request detail by ID
    getVendorRequestDetail: builder.query<any, number>({
      query: (requestId) => `/vendor/requests/${requestId}`,
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: (_result, _error, requestId) => [{ type: 'Vendor', id: requestId }],
    }),

    // Upload penawaran
    uploadPenawaran: builder.mutation<any, { requestId: number; data: FormData }>({
      query: ({ requestId, data }) => ({
        url: `/vendor/penawaran/upload`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Vendor'],
    }),

    // Get existing penawaran for a request
    getExistingPenawaran: builder.query<any, number>({
      query: (requestId) => `/vendor/penawaran/request/${requestId}`,
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: (_result, _error, requestId) => [{ type: 'Vendor', id: requestId }],
    }),

    // Get vendor history (penawaran history)
    getVendorHistory: builder.query<any, { page?: number; limit?: number; status?: string; start_date?: string; end_date?: string }>({
      query: (params) => `/vendor/history${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: any[]; pagination?: any; statistics?: any }) => ({
        data: response.data,
        pagination: response.pagination,
        statistics: response.statistics,
      }),
      providesTags: ['Vendor'],
    }),

    // Get vendor orders (pesanan)
    getVendorOrders: builder.query<any, { status?: string; search?: string; page?: number; per_page?: number; sort_by?: string; sort_dir?: string }>({
      query: (params) => `/vendor-orders/my-orders${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: any; pagination?: any; statistics?: any }) => ({
        orders: response.data?.orders || response.data || [],
        pagination: response.pagination,
        statistics: response.statistics,
      }),
      providesTags: ['Vendor'],
    }),

    // Get vendor order detail
    getVendorOrderDetail: builder.query<any, number>({
      query: (orderId) => `/vendor-orders/${orderId}`,
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: (_result, _error, orderId) => [{ type: 'Vendor', id: orderId }],
    }),

    // Get vendor templates
    getVendorTemplates: builder.query<any, void>({
      query: () => '/vendor/templates',
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: ['Vendor'],
    }),

    // Get vendor notifications
    getVendorNotifications: builder.query<any, { limit?: number; unread_only?: boolean }>({
      query: (params) => `/vendor/notifications${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: ['Vendor'],
    }),

    // Get vendor notification statistics
    getVendorNotificationStats: builder.query<any, void>({
      query: () => '/vendor/notifications/statistics',
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: ['Vendor'],
    }),

    // Mark notification as read
    markNotificationAsRead: builder.mutation<any, number>({
      query: (notificationId) => ({
        url: `/vendor/notifications/${notificationId}/read`,
        method: 'PUT',
      }),
      invalidatesTags: ['Vendor'],
    }),

    // Mark all notifications as read
    markAllNotificationsAsRead: builder.mutation<any, void>({
      query: () => ({
        url: '/vendor/notifications/read-all',
        method: 'PUT',
      }),
      invalidatesTags: ['Vendor'],
    }),

    // Confirm vendor order
    confirmVendorOrder: builder.mutation<any, { orderId: number; data: { vendor_notes?: string } }>({
      query: ({ orderId, data }) => ({
        url: `/vendor-orders/${orderId}/confirm`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Vendor'],
    }),

    // Update vendor order status
    updateVendorOrderStatus: builder.mutation<any, { orderId: number; data: { status: string; tracking_number?: string; estimated_delivery_date?: string; notes?: string } }>({
      query: ({ orderId, data }) => ({
        url: `/vendor-orders/${orderId}/status`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Vendor'],
    }),

    // Get vendor order status history
    getVendorOrderStatusHistory: builder.query<any, number>({
      query: (orderId) => `/vendor-orders/${orderId}/history`,
      transformResponse: (response: { success: boolean; data: any }) => response.data,
      providesTags: (_result, _error, orderId) => [{ type: 'Vendor', id: orderId }],
    }),

    // Create new vendor
    createVendor: builder.mutation<Vendor, Partial<Vendor>>({
      query: (data) => ({
        url: '/vendor',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Vendor'],
    }),

    // Update vendor
    updateVendor: builder.mutation<Vendor, { id: number; data: Partial<Vendor> }>({
      query: ({ id, data }) => ({
        url: `/vendor/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Vendor', id },
        'Vendor',
      ],
    }),

    // Delete vendor
    deleteVendor: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/vendor/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [
        { type: 'Vendor', id },
        'Vendor',
      ],
    }),

    // Bulk import vendors
    bulkImportVendor: builder.mutation<BulkImportResponse, BulkImportRequest>({
      query: ({ file }) => {
        const formData = new FormData();
        formData.append('file', file);
        return {
          url: '/vendor/bulk-import',
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: ['Vendor'],
    }),

    // Vendor self registration (public endpoint, no auth required)
    vendorSelfRegister: builder.mutation<VendorSelfRegistrationResponse, VendorSelfRegistrationRequest>({
      query: (data) => ({
        url: '/vendor/self-register',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: VendorSelfRegistrationResponse) => response,
      // No invalidatesTags karena ini public endpoint dan tidak perlu cache
    }),
  }),
  overrideExisting: false,
});

// Export hooks untuk use di components
export const {
  useGetVendorsQuery,
  useGetVendorByIdQuery,
  useGetVendorDashboardQuery,
  useGetVendorProfileQuery,
  useUpdateVendorProfileMutation,
  useGetVendorRequestsQuery,
  useGetVendorRequestDetailQuery,
  useUploadPenawaranMutation,
  useGetExistingPenawaranQuery,
  useGetVendorHistoryQuery,
  useGetVendorOrdersQuery,
  useGetVendorOrderDetailQuery,
  useGetVendorTemplatesQuery,
  useGetVendorNotificationsQuery,
  useGetVendorNotificationStatsQuery,
  useMarkNotificationAsReadMutation,
  useMarkAllNotificationsAsReadMutation,
  useConfirmVendorOrderMutation,
  useUpdateVendorOrderStatusMutation,
  useGetVendorOrderStatusHistoryQuery,
  useCreateVendorMutation,
  useUpdateVendorMutation,
  useDeleteVendorMutation,
  useBulkImportVendorMutation,
  useVendorSelfRegisterMutation,
} = vendorApi;

