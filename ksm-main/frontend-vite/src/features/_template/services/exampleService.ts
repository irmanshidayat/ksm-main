/**
 * Example Service
 * Template untuk feature-specific service
 * 
 * Copy services dari frontend CRA:
 * - frontend/src/services/[feature]Service.ts
 * 
 * Adapt untuk menggunakan:
 * - apiClient dari @/core/api/client
 * - API_ENDPOINTS dari @/core/api/endpoints
 */

import apiClient from '@/core/api/client';
import { API_ENDPOINTS } from '@/core/api/endpoints';

export const exampleService = {
  async getExample() {
    const response = await apiClient.get(API_ENDPOINTS.EXAMPLE);
    return response.data;
  },

  async createExample(data: any) {
    const response = await apiClient.post(API_ENDPOINTS.EXAMPLE, data);
    return response.data;
  },
};

