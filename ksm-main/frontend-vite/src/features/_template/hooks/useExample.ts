/**
 * Example Hook
 * Template untuk feature-specific hook
 * 
 * Copy hooks dari frontend CRA:
 * - frontend/src/hooks/use[Feature].ts
 * 
 * Adapt untuk menggunakan:
 * - apiClient dari @/core/api/client
 * - API_ENDPOINTS dari @/core/api/endpoints
 */

import { useState, useEffect } from 'react';
import apiClient from '@/core/api/client';
import { API_ENDPOINTS } from '@/core/api/endpoints';

export const useExample = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get(API_ENDPOINTS.EXAMPLE);
        setData(response.data.data);
      } catch (err) {
        setError('Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};

