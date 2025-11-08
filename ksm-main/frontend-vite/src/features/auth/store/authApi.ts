/**
 * Auth API (RTK Query)
 * Auth endpoints untuk authentication
 */

import { baseApi } from '@/app/store/services/baseApi';

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  success: boolean;
  user: {
    id: number;
    username: string;
    role: string;
    email?: string;
  };
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

interface User {
  id: number;
  username: string;
  role: string;
  email?: string;
}

// Auth API endpoints
export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: ['Auth'],
    }),
    
    logout: builder.mutation<{ success: boolean }, void>({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
      invalidatesTags: ['Auth'],
    }),
    
    refreshToken: builder.mutation<{
      access_token: string;
      refresh_token: string;
      expires_in: number;
    }, { refresh_token: string }>({
      query: ({ refresh_token }) => ({
        url: '/refresh',
        method: 'POST',
        body: { refresh_token },
      }),
    }),
    
    getCurrentUser: builder.query<User, void>({
      query: () => '/auth/me',
      providesTags: ['Auth'],
    }),
    
    validateToken: builder.query<{ valid: boolean }, void>({
      query: () => '/auth/validate',
      providesTags: ['Auth'],
    }),
  }),
  overrideExisting: false,
});

// Export hooks untuk use di components
export const {
  useLoginMutation,
  useLogoutMutation,
  useRefreshTokenMutation,
  useGetCurrentUserQuery,
  useValidateTokenQuery,
} = authApi;

