/**
 * Search and Filter Component
 * Component untuk search dan filter barang dengan Tailwind
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Button, Input } from '@/shared/components/ui';
import type { FilterParams } from '../types';

interface SearchAndFilterProps {
  onFilterChange: (filters: FilterParams) => void;
  onReset: () => void;
  kategoriList: any[];
  supplierList: any[];
  loading?: boolean;
  enableRealtimeSearch?: boolean;
}

const SearchAndFilter: React.FC<SearchAndFilterProps> = ({
  onFilterChange,
  onReset,
  kategoriList,
  supplierList,
  loading = false,
  enableRealtimeSearch = true
}) => {
  const [filters, setFilters] = useState<FilterParams>({});
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Debounce function untuk search realtime
  const debounce = useCallback((func: Function, delay: number) => {
    let timeoutId: NodeJS.Timeout;
    return (...args: any[]) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func.apply(null, args), delay);
    };
  }, []);

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce((searchTerm: string) => {
      setIsSearching(true);
      const newFilters = { ...filters, search: searchTerm };
      setFilters(newFilters);
      if (enableRealtimeSearch) {
        onFilterChange(newFilters);
      }
      setTimeout(() => setIsSearching(false), 200);
    }, 500),
    [filters, onFilterChange, enableRealtimeSearch, debounce]
  );

  const handleSearchChange = (value: string) => {
    setSearchValue(value);
    if (enableRealtimeSearch) {
      debouncedSearch(value);
    }
  };

  const handleInputChange = (field: keyof FilterParams, value: any) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
  };

  const handleApplyFilter = () => {
    const newFilters = { ...filters, search: searchValue };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleResetFilter = () => {
    setFilters({});
    setSearchValue('');
    onReset();
  };

  useEffect(() => {
    if (filters.search !== undefined && filters.search !== searchValue) {
      setSearchValue(filters.search || '');
    }
  }, [filters.search]);

  const hasActiveFilters = Object.values(filters).some(value => 
    value !== undefined && value !== null && value !== ''
  ) || searchValue.trim() !== '';

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      {/* Search Section */}
      <div className="flex flex-col md:flex-row gap-4 mb-4">
        <div className="flex-1 relative">
          <Input
            type="text"
            placeholder="Cari kode barang, nama barang, deskripsi, kategori..."
            value={searchValue}
            onChange={(e) => handleSearchChange(e.target.value)}
            disabled={loading}
            className="w-full pr-10"
          />
          {enableRealtimeSearch && searchValue && (
            <span className="absolute right-3 top-2.5 text-gray-400">
              {isSearching ? '⏳' : '✅'}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setIsExpanded(!isExpanded)}
            disabled={loading}
            size="sm"
          >
            🎛️ Filter {hasActiveFilters && `(${Object.keys(filters).length})`}
          </Button>
          {!enableRealtimeSearch && (
            <Button
              variant="primary"
              onClick={handleApplyFilter}
              disabled={loading || isSearching}
              size="sm"
            >
              🔍 Cari
            </Button>
          )}
        </div>
      </div>

      {/* Filter Panel */}
      {isExpanded && (
        <div className="border-t pt-4 mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Kategori Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Kategori</label>
              <select
                value={filters.kategori_id || ''}
                onChange={(e) => handleInputChange('kategori_id', e.target.value ? parseInt(e.target.value) : undefined)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={loading}
              >
                <option value="">Semua Kategori</option>
                {Array.isArray(kategoriList) && kategoriList.map((kategori) => (
                  <option key={kategori.id} value={kategori.id}>
                    {kategori.nama_kategori}
                  </option>
                ))}
              </select>
            </div>

            {/* Supplier Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Supplier</label>
              <select
                value={filters.supplier_id || ''}
                onChange={(e) => handleInputChange('supplier_id', e.target.value ? parseInt(e.target.value) : undefined)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={loading}
              >
                <option value="">Semua Supplier</option>
                {Array.isArray(supplierList) && supplierList.map((supplier) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.nama_supplier}
                  </option>
                ))}
              </select>
            </div>

            {/* Stok Range Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Rentang Stok</label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={filters.stok_min || ''}
                  onChange={(e) => handleInputChange('stok_min', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="flex-1"
                  disabled={loading}
                />
                <span className="self-center text-gray-500">-</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={filters.stok_max || ''}
                  onChange={(e) => handleInputChange('stok_max', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="flex-1"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Harga Range Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Rentang Harga</label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={filters.harga_min || ''}
                  onChange={(e) => handleInputChange('harga_min', e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="flex-1"
                  disabled={loading}
                />
                <span className="self-center text-gray-500">-</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={filters.harga_max || ''}
                  onChange={(e) => handleInputChange('harga_max', e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="flex-1"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Sort Options */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Urutkan Berdasarkan</label>
              <div className="flex gap-2">
                <select
                  value={filters.sort_by || 'nama_barang'}
                  onChange={(e) => handleInputChange('sort_by', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={loading}
                >
                  <option value="nama_barang">Nama Barang</option>
                  <option value="kode_barang">Kode Barang</option>
                  <option value="stok">Jumlah Stok</option>
                  <option value="harga_per_unit">Harga</option>
                  <option value="kategori">Kategori</option>
                </select>
                <select
                  value={filters.sort_order || 'asc'}
                  onChange={(e) => handleInputChange('sort_order', e.target.value as 'asc' | 'desc')}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={loading}
                >
                  <option value="asc">A-Z</option>
                  <option value="desc">Z-A</option>
                </select>
              </div>
            </div>
          </div>

          {/* Filter Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              variant="outline"
              onClick={handleResetFilter}
              disabled={loading}
              size="sm"
            >
              🔄 Reset Filter
            </Button>
            <Button
              variant="primary"
              onClick={handleApplyFilter}
              disabled={loading}
              size="sm"
            >
              ✅ Terapkan Filter
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchAndFilter;

