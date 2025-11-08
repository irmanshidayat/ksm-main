/**
 * Hook untuk manage category list dengan filters
 */

import { useState, useMemo } from 'react';
import { useGetKategoriQuery } from '../store';
import type { Kategori } from '../types';

interface CategoryListFilters {
  search: string;
  sortBy: 'nama_kategori' | 'kode_kategori' | 'created_at';
  sortOrder: 'asc' | 'desc';
}

interface CategoryListState {
  filters: CategoryListFilters;
  setFilters: (filters: Partial<CategoryListFilters>) => void;
  resetFilters: () => void;
  filteredCategories: Kategori[];
  totalCategories: number;
  isLoading: boolean;
  error: any;
}

const initialFilters: CategoryListFilters = {
  search: '',
  sortBy: 'nama_kategori',
  sortOrder: 'asc'
};

export function useCategoryList(): CategoryListState {
  const [filters, setFilters] = useState<CategoryListFilters>(initialFilters);
  
  // Fetch categories from API
  const { 
    data: categories = [], 
    isLoading, 
    error 
  } = useGetKategoriQuery();

  // Filter and sort categories
  const filteredCategories = useMemo(() => {
    let filtered = [...categories];

    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(category => 
        category.nama_kategori.toLowerCase().includes(searchLower) ||
        category.kode_kategori.toLowerCase().includes(searchLower) ||
        (category.deskripsi && category.deskripsi.toLowerCase().includes(searchLower))
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any = a[filters.sortBy];
      let bValue: any = b[filters.sortBy];

      // Handle string comparison
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (filters.sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return filtered;
  }, [categories, filters]);

  const handleSetFilters = (newFilters: Partial<CategoryListFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const handleResetFilters = () => {
    setFilters(initialFilters);
  };

  return {
    filters,
    setFilters: handleSetFilters,
    resetFilters: handleResetFilters,
    filteredCategories,
    totalCategories: categories.length,
    isLoading,
    error
  };
}

