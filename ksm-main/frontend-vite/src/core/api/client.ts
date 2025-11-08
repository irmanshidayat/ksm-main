/**
 * API Client Configuration
 * Axios instance dengan interceptors untuk request/response handling
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { ENV } from '../config/env';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: ENV.API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Add API key if available
    if (ENV.API_KEY && config.headers) {
      config.headers['X-API-Key'] = ENV.API_KEY;
    }

    // Add auth token from localStorage if available
    const token = localStorage.getItem('KSM_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log request in development
    if (ENV.DEBUG) {
      console.log('📤 API Request:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        baseURL: config.baseURL,
      });
    }

    return config;
  },
  (error: AxiosError) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response in development
    if (ENV.DEBUG) {
      console.log('📥 API Response:', {
        status: response.status,
        url: response.config.url,
      });
    }

    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized - Token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh token
        const refreshToken = localStorage.getItem('KSM_refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${ENV.API_URL}/api/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('KSM_access_token', access_token);
          if (newRefreshToken) {
            localStorage.setItem('KSM_refresh_token', newRefreshToken);
          }

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('KSM_access_token');
        localStorage.removeItem('KSM_refresh_token');
        localStorage.removeItem('KSM_user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Log error in development
    if (ENV.DEBUG) {
      console.error('❌ API Error:', {
        status: error.response?.status,
        message: error.message,
        url: error.config?.url,
        data: error.response?.data,
      });
    }

    return Promise.reject(error);
  }
);

export default apiClient;

