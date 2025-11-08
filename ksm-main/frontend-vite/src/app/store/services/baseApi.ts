/**
 * Base API Configuration dengan RTK Query
 * Centralized API setup untuk semua feature APIs
 */

import { createApi, fetchBaseQuery, BaseQueryFn, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../index';
import { ENV } from '@/core/config/env';

// Custom baseQuery dengan error handling untuk 401
const baseQuery = fetchBaseQuery({
  baseUrl: `${ENV.API_URL}/api`,
  prepareHeaders: (headers, { getState }) => {
    // Get token dari Redux state, fallback ke localStorage
    const state = getState() as RootState;
    let token = state.auth?.token;
    
    // Fallback ke localStorage jika token tidak ada di Redux state
    if (!token) {
      token = localStorage.getItem('KSM_access_token');
    }
    
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    
    // Add API key if available
    if (ENV.API_KEY) {
      headers.set('X-API-Key', ENV.API_KEY);
    }
    
    headers.set('Content-Type', 'application/json');
    return headers;
  },
});

// BaseQuery dengan retry logic untuk 401
const baseQueryWithReauth: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  let result = await baseQuery(args, api, extraOptions);
  
  // Handle 401 Unauthorized
  if (result.error && result.error.status === 401) {
    // Try to refresh token
    const refreshToken = localStorage.getItem('KSM_refresh_token');
    
    if (refreshToken) {
      try {
        // Make refresh request without using baseQuery to avoid recursion
        const refreshResponse = await fetch(`${ENV.API_URL}/api/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        
        if (refreshResponse.ok) {
          const refreshData = await refreshResponse.json();
          const { access_token, refresh_token: newRefreshToken } = refreshData;
          
          // Update tokens in localStorage
          localStorage.setItem('KSM_access_token', access_token);
          if (newRefreshToken) {
            localStorage.setItem('KSM_refresh_token', newRefreshToken);
          }
          
          // Retry original query with new token
          result = await baseQuery(args, api, extraOptions);
        } else {
          // Refresh failed, logout user
          localStorage.removeItem('KSM_access_token');
          localStorage.removeItem('KSM_refresh_token');
          localStorage.removeItem('KSM_user');
          window.location.href = '/login';
        }
      } catch (error) {
        // Refresh failed, logout user
        localStorage.removeItem('KSM_access_token');
        localStorage.removeItem('KSM_refresh_token');
        localStorage.removeItem('KSM_user');
        window.location.href = '/login';
      }
    } else {
      // No refresh token, logout user
      localStorage.removeItem('KSM_access_token');
      localStorage.removeItem('KSM_refresh_token');
      localStorage.removeItem('KSM_user');
      window.location.href = '/login';
    }
  }
  
  return result;
};

// Base API configuration dengan RTK Query
export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    'Auth',
    'User',
    'Vendor', 
    'StokBarang', 
    'Supplier', 
    'Kategori',
    'RequestPembelian', 
    'VendorPenawaran', 
    'VendorOrder',
    'Mobil', 
    'MobilReservation',
    'Attendance', 
    'DailyTask', 
    'LeaveRequest',
    'User',
    'UserRole',
    'EmailDomain',
    'Department',
    'Role',
    'Permission',
    'Notification',
    'Approval',
    'Telegram',
    'Agent',
    'RemindExpDoc',
    'Notion',
    'Qdrant',
    'KnowledgeAI',
    'Permission',
  ],
  endpoints: () => ({}),
});

// Base API is configured, hooks are exported from individual API files

