/**
 * Email Domain RTK Query API
 */

import { baseApi } from '@/app/store/services/baseApi';

export interface DomainConfig {
  id: number;
  user_id: number;
  domain_name: string;
  smtp_server: string;
  smtp_port: number;
  username: string;
  from_name: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface DomainConfigData {
  domain_name: string;
  smtp_server: string;
  smtp_port: number;
  username: string;
  password: string;
  from_name: string;
  is_default?: boolean;
}

export interface DomainConfigResponse {
  success: boolean;
  message?: string;
  data?: DomainConfig | DomainConfig[];
  count?: number;
  errors?: string[];
}

export interface TestConnectionResponse {
  success: boolean;
  message?: string;
  data?: {
    connected: boolean;
    error?: string;
  };
}

export const emailDomainApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get all domain configs for current user
    getDomainConfigs: builder.query<DomainConfigResponse, void>({
      query: () => '/email-domain/config',
      transformResponse: (response: DomainConfigResponse) => response,
      providesTags: ['EmailDomain'],
    }),

    // Create new domain config
    createDomainConfig: builder.mutation<DomainConfigResponse, DomainConfigData>({
      query: (data) => ({
        url: '/email-domain/config',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: DomainConfigResponse) => response,
      invalidatesTags: ['EmailDomain'],
    }),

    // Update domain config
    updateDomainConfig: builder.mutation<DomainConfigResponse, { id: number; data: Partial<DomainConfigData> }>({
      query: ({ id, data }) => ({
        url: '/email-domain/config',
        method: 'PUT',
        body: { id, ...data },
      }),
      transformResponse: (response: DomainConfigResponse) => response,
      invalidatesTags: ['EmailDomain'],
    }),

    // Delete domain config
    deleteDomainConfig: builder.mutation<DomainConfigResponse, number>({
      query: (id) => ({
        url: `/email-domain/config/${id}`,
        method: 'DELETE',
      }),
      transformResponse: (response: DomainConfigResponse) => response,
      invalidatesTags: ['EmailDomain'],
    }),

    // Test domain connection
    testDomainConnection: builder.mutation<TestConnectionResponse, { id?: number; data?: Partial<DomainConfigData> }>({
      query: (params) => ({
        url: '/email-domain/test',
        method: 'POST',
        body: params,
      }),
      transformResponse: (response: TestConnectionResponse) => response,
    }),

    // Set default domain
    setDefaultDomain: builder.mutation<DomainConfigResponse, number>({
      query: (domainId) => ({
        url: '/email-domain/set-default',
        method: 'POST',
        body: { domain_id: domainId },
      }),
      transformResponse: (response: DomainConfigResponse) => response,
      invalidatesTags: ['EmailDomain'],
    }),
  }),
});

export const {
  useGetDomainConfigsQuery,
  useCreateDomainConfigMutation,
  useUpdateDomainConfigMutation,
  useDeleteDomainConfigMutation,
  useTestDomainConnectionMutation,
  useSetDefaultDomainMutation,
} = emailDomainApi;

