/**
 * Request Pembelian RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';
import { buildQueryString } from '@/core/utils';
import type {
  RequestPembelian,
  RequestPembelianListParams,
  RequestPembelianListResponse,
  VendorPenawaran,
  VendorAnalysisResult,
  VendorCatalogItem,
  VendorCatalogListParams,
  VendorCatalogListResponse,
  EmailAttachment,
} from '../types';

export const requestPembelianApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get request pembelian list
    getRequestPembelianList: builder.query<RequestPembelianListResponse, RequestPembelianListParams>({
      query: (params) => `/request-pembelian${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: RequestPembelianListResponse }) => response.data,
      providesTags: (result) => [
        'RequestPembelian',
        ...(result?.items?.map(({ id }) => ({ type: 'RequestPembelian' as const, id })) || []),
      ],
      keepUnusedDataFor: 30,
    }),

    // Get single request pembelian by ID
    getRequestPembelianById: builder.query<RequestPembelian, number>({
      query: (id) => `/request-pembelian/requests/${id}`,
      transformResponse: (response: { success: boolean; data: RequestPembelian }) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'RequestPembelian', id }],
    }),

    // Get dashboard stats
    getRequestPembelianDashboardStats: builder.query<{ success: boolean; data: any }, void>({
      query: () => '/request-pembelian/dashboard/stats',
      transformResponse: (response: { success: boolean; data: any }) => response,
      providesTags: ['RequestPembelian'],
    }),

    // Create new request pembelian
    createRequestPembelian: builder.mutation<RequestPembelian, Partial<RequestPembelian>>({
      query: (data) => ({
        url: '/request-pembelian/requests',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: RequestPembelian }) => response.data,
      invalidatesTags: ['RequestPembelian'],
    }),

    // Update request pembelian
    updateRequestPembelian: builder.mutation<RequestPembelian, { id: number; data: Partial<RequestPembelian> }>({
      query: ({ id, data }) => ({
        url: `/request-pembelian/requests/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data: RequestPembelian }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'RequestPembelian', id },
        'RequestPembelian',
      ],
    }),

    // Delete request pembelian
    deleteRequestPembelian: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({
        url: `/request-pembelian/requests/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [
        { type: 'RequestPembelian', id },
        'RequestPembelian',
      ],
    }),

    // Submit request
    submitRequestPembelian: builder.mutation<RequestPembelian, number>({
      query: (id) => ({
        url: `/request-pembelian/requests/${id}/submit`,
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; data: RequestPembelian }) => response.data,
      invalidatesTags: (_result, _error, id) => [
        { type: 'RequestPembelian', id },
        'RequestPembelian',
      ],
    }),

    // Start vendor upload
    startVendorUpload: builder.mutation<RequestPembelian, number>({
      query: (id) => ({
        url: `/request-pembelian/requests/${id}/start-vendor-upload`,
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; data: RequestPembelian }) => response.data,
      invalidatesTags: (_result, _error, id) => [
        { type: 'RequestPembelian', id },
        'RequestPembelian',
      ],
    }),

    // Start analysis
    startAnalysis: builder.mutation<RequestPembelian, number>({
      query: (id) => ({
        url: `/request-pembelian/requests/${id}/start-analysis`,
        method: 'POST',
      }),
      transformResponse: (response: { success: boolean; data: RequestPembelian }) => response.data,
      invalidatesTags: (_result, _error, id) => [
        { type: 'RequestPembelian', id },
        'RequestPembelian',
      ],
    }),

    // Approve request
    approveRequestPembelian: builder.mutation<RequestPembelian, { id: number; approved_by?: number }>({
      query: ({ id, approved_by }) => ({
        url: `/request-pembelian/requests/${id}/approve`,
        method: 'POST',
        body: { approved_by },
      }),
      transformResponse: (response: { success: boolean; data: RequestPembelian }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'RequestPembelian', id },
        'RequestPembelian',
      ],
    }),

    // Reject request
    rejectRequestPembelian: builder.mutation<RequestPembelian, { id: number; rejected_by?: number; reason: string }>({
      query: ({ id, rejected_by, reason }) => ({
        url: `/request-pembelian/requests/${id}/reject`,
        method: 'POST',
        body: { rejected_by, reason },
      }),
      transformResponse: (response: { success: boolean; data: RequestPembelian }) => response.data,
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'RequestPembelian', id },
        'RequestPembelian',
      ],
    }),

    // Get vendor penawarans for a request
    getVendorPenawarans: builder.query<VendorPenawaran[], number>({
      query: (requestId) => `/request-pembelian/requests/${requestId}/penawarans`,
      transformResponse: (response: { success: boolean; data: VendorPenawaran[] }) => response.data,
      providesTags: (_result, _error, requestId) => [
        { type: 'VendorPenawaran', id: requestId },
        'VendorPenawaran',
      ],
    }),

    // Get vendor analysis
    getVendorAnalysis: builder.query<VendorAnalysisResult, number>({
      query: (requestId) => `/analysis/results/${requestId}`,
      transformResponse: (response: { success: boolean; data: VendorAnalysisResult }) => response.data,
      providesTags: (_result, _error, requestId) => [
        { type: 'VendorAnalysis', id: requestId },
      ],
    }),

    // Upload penawaran (with FormData for files)
    uploadPenawaranWithFiles: builder.mutation<any, { vendorId: number; requestId: number; data: FormData }>({
      query: ({ vendorId, requestId, data }) => ({
        url: `/vendor/${vendorId}/penawaran/upload`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: (_result, _error, { requestId }) => [
        { type: 'VendorPenawaran', id: requestId },
        'VendorPenawaran',
        'RequestPembelian',
      ],
    }),

    // Get all vendor catalog items (for Tab 2)
    getAllVendorCatalogItems: builder.query<VendorCatalogListResponse, VendorCatalogListParams>({
      query: (params) => `/vendor-catalog/all${buildQueryString(params)}`,
      transformResponse: (response: { success: boolean; data: VendorCatalogItem[]; pagination: any; message?: string }) => ({
        success: response.success,
        data: response.data || [],
        pagination: response.pagination || { page: 1, per_page: 10, total: 0, pages: 1, has_next: false, has_prev: false },
        message: response.message,
      }),
      providesTags: ['VendorPenawaran'],
      keepUnusedDataFor: 30,
    }),

    // Update vendor catalog item
    updateVendorCatalogItem: builder.mutation<{ success: boolean; data?: VendorCatalogItem; message?: string }, { id: number; data: Partial<VendorCatalogItem> }>({
      query: ({ id, data }) => ({
        url: `/vendor-catalog/items/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: { success: boolean; data?: VendorCatalogItem; message?: string }) => response,
      invalidatesTags: ['VendorPenawaran'],
    }),

    // Delete vendor catalog item
    deleteVendorCatalogItem: builder.mutation<{ success: boolean; message?: string }, number>({
      query: (id) => ({
        url: `/vendor-catalog/items/${id}`,
        method: 'DELETE',
      }),
      transformResponse: (response: { success: boolean; message?: string }) => response,
      invalidatesTags: ['VendorPenawaran'],
    }),

    // Send email to vendor
    sendVendorEmail: builder.mutation<{ success: boolean; message?: string }, { vendor_email: string; vendor_name: string; items: any[]; subject?: string; custom_message?: string; cc_emails?: string[]; bcc_emails?: string[] }>({
      query: (data) => ({
        url: `/email/send-vendor-email`,
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: { success: boolean; message?: string }) => response,
    }),

    // Get email attachments for request
    getRequestAttachments: builder.query<EmailAttachment[], number>({
      query: (requestId) => `/email/get-attachments?request_pembelian_id=${requestId}&status=active`,
      transformResponse: (response: { success: boolean; data: EmailAttachment[] }) => response.data || [],
      providesTags: (_result, _error, requestId) => [
        { type: 'RequestPembelian', id: requestId },
        'EmailAttachment',
      ],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetRequestPembelianListQuery,
  useGetRequestPembelianByIdQuery,
  useGetRequestPembelianDashboardStatsQuery,
  useCreateRequestPembelianMutation,
  useUpdateRequestPembelianMutation,
  useDeleteRequestPembelianMutation,
  useSubmitRequestPembelianMutation,
  useStartVendorUploadMutation,
  useStartAnalysisMutation,
  useApproveRequestPembelianMutation,
  useRejectRequestPembelianMutation,
  useGetVendorPenawaransQuery,
  useGetVendorAnalysisQuery,
  useGetAllVendorCatalogItemsQuery,
  useUpdateVendorCatalogItemMutation,
  useDeleteVendorCatalogItemMutation,
  useSendVendorEmailMutation,
  useGetRequestAttachmentsQuery,
} = requestPembelianApi;

