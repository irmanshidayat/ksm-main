/**
 * Hook untuk manage barang list dengan filters dan pagination
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { 
  useGetBarangListQuery, 
  useGetSuppliersQuery, 
  useGetKategoriQuery 
} from '../store';
import type { Barang, Supplier, FilterParams, PaginationParams } from '../types';

export function useBarangList() {
  // RTK Query hooks
  const [filters, setFilters] = useState<FilterParams>({});
  const [paginationParams, setPaginationParams] = useState<PaginationParams>({
    page: 1,
    per_page: 10
  });
  
  const { 
    data: barangData, 
    isLoading: barangLoading, 
    error: barangError,
    refetch: refetchBarang
  } = useGetBarangListQuery({ ...filters, ...paginationParams });

  const { 
    data: supplierList = [], 
    isLoading: supplierLoading, 
    error: supplierError 
  } = useGetSuppliersQuery();
  
  const { 
    data: kategoriList = [], 
    isLoading: kategoriLoading, 
    error: kategoriError 
  } = useGetKategoriQuery();
  
  // Refs untuk debounce dan abort controller
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Debounce function untuk search realtime
  const debounce = useCallback((func: Function, delay: number) => {
    return (...args: any[]) => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      debounceTimeoutRef.current = setTimeout(() => func.apply(null, args), delay);
    };
  }, []);

  // Update filters dan pagination
  const updateFilters = useCallback((newFilters: FilterParams) => {
    setFilters(newFilters);
    setPaginationParams(prev => ({ ...prev, page: 1 })); // Reset to first page
  }, []);

  const updatePagination = useCallback((newPagination: PaginationParams) => {
    setPaginationParams(newPagination);
  }, []);

  const refetch = useCallback((newFilters?: FilterParams, newPaginationParams?: PaginationParams) => {
    if (newFilters) {
      updateFilters(newFilters);
    }
    if (newPaginationParams) {
      updatePagination(newPaginationParams);
    }
    refetchBarang();
  }, [updateFilters, updatePagination, refetchBarang]);

  // Debounced refetch untuk search realtime
  const debouncedRefetch = useCallback(
    debounce((newFilters?: FilterParams, newPaginationParams?: PaginationParams) => {
      if (newFilters) {
        updateFilters(newFilters);
      }
      if (newPaginationParams) {
        updatePagination(newPaginationParams);
      }
    }, 500),
    [updateFilters, updatePagination, debounce]
  );

  // Cleanup function untuk clear timeout dan abort controller
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const exportData = useCallback(async (filters?: FilterParams) => {
    try {
      const params = new URLSearchParams();
      
      // Apply same filters as fetchData
      if (filters) {
        if (filters.search) params.append('search', filters.search);
        if (filters.kategori_id) params.append('kategori_id', filters.kategori_id.toString());
        if (filters.supplier_id) params.append('supplier_id', filters.supplier_id.toString());
        if (filters.stok_min !== undefined) params.append('stok_min', filters.stok_min.toString());
        if (filters.stok_max !== undefined) params.append('stok_max', filters.stok_max.toString());
        if (filters.harga_min !== undefined) params.append('harga_min', filters.harga_min.toString());
        if (filters.harga_max !== undefined) params.append('harga_max', filters.harga_max.toString());
        if (filters.sort_by) params.append('sort_by', filters.sort_by);
        if (filters.sort_order) params.append('sort_order', filters.sort_order);
      }

      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('KSM_access_token') || localStorage.getItem('token');
      
      const response = await fetch(`${apiUrl}/api/stok-barang/barang/export?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `daftar_barang_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        return true;
      } else {
        throw new Error('Export failed');
      }
    } catch (err) {
      console.error('Error exporting data:', err);
      throw err;
    }
  }, []);

  // Combine loading states
  const loading = barangLoading || supplierLoading || kategoriLoading;
  
  // Combine errors
  const error = barangError || supplierError || kategoriError;
  
  return {
    barangList: barangData?.items || [],
    supplierList,
    kategoriList,
    loading,
    error: error ? 'Terjadi kesalahan saat mengambil data' : null,
    pagination: {
      page: barangData?.page || 1,
      per_page: barangData?.per_page || 10,
      total: barangData?.total || 0,
      pages: barangData?.pages || 0
    },
    refetch,
    debouncedRefetch,
    exportData
  };
}

