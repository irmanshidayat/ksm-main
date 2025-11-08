/**
 * Category List Page
 * Halaman untuk melihat daftar kategori barang
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCategoryList } from '../hooks';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { Kategori } from '../types';

const CategoryListPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    filters,
    setFilters,
    resetFilters,
    filteredCategories,
    totalCategories,
    isLoading,
    error
  } = useCategoryList();

  const [expandedCategory, setExpandedCategory] = useState<number | null>(null);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ search: e.target.value });
  };

  const handleSortChange = (sortBy: 'nama_kategori' | 'kode_kategori' | 'created_at') => {
    const newSortOrder = filters.sortBy === sortBy && filters.sortOrder === 'asc' ? 'desc' : 'asc';
    setFilters({ sortBy, sortOrder: newSortOrder });
  };

  const toggleExpanded = (categoryId: number) => {
    setExpandedCategory(expandedCategory === categoryId ? null : categoryId);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (error) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="mb-6">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📂 Daftar Kategori Barang</h1>
          <p className="text-gray-600">Kelola kategori barang yang tersedia</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <span className="text-4xl mb-4 block">⚠️</span>
          <h3 className="text-lg font-semibold text-red-800 mb-2">Terjadi Kesalahan</h3>
          <p className="text-red-600 mb-4">Gagal memuat data kategori. Silakan coba lagi.</p>
          <Button onClick={() => window.location.reload()}>
            🔄 Coba Lagi
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📂 Daftar Kategori Barang</h1>
        <p className="text-gray-600">Kelola kategori barang yang tersedia</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
          <div className="flex items-center space-x-4">
            <div className="text-4xl">📂</div>
            <div>
              <h3 className="text-sm font-medium text-gray-600">Total Kategori</h3>
              <p className="text-2xl font-bold text-gray-800">{totalCategories}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
          <div className="flex items-center space-x-4">
            <div className="text-4xl">🔍</div>
            <div>
              <h3 className="text-sm font-medium text-gray-600">Kategori Ditampilkan</h3>
              <p className="text-2xl font-bold text-gray-800">{filteredCategories.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="space-y-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Cari kategori berdasarkan nama, kode, atau deskripsi..."
              value={filters.search}
              onChange={handleSearchChange}
              className="block w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Urutkan berdasarkan:</label>
              <select 
                value={filters.sortBy}
                onChange={(e) => handleSortChange(e.target.value as any)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="nama_kategori">Nama Kategori</option>
                <option value="kode_kategori">Kode Kategori</option>
                <option value="created_at">Tanggal Dibuat</option>
              </select>
              <button 
                className={`p-1.5 rounded-lg border ${
                  filters.sortOrder === 'asc' 
                    ? 'bg-blue-100 border-blue-300 text-blue-700' 
                    : 'bg-gray-100 border-gray-300 text-gray-700'
                }`}
                onClick={() => setFilters({ sortOrder: filters.sortOrder === 'asc' ? 'desc' : 'asc' })}
                title={`Urutkan ${filters.sortOrder === 'asc' ? 'Z-A' : 'A-Z'}`}
              >
                {filters.sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
            
            <div className="flex gap-2">
              {(filters.search || filters.sortBy !== 'nama_kategori' || filters.sortOrder !== 'asc') && (
                <Button
                  variant="outline"
                  onClick={resetFilters}
                  size="sm"
                >
                  🔄 Reset Filter
                </Button>
              )}
              <Button
                variant="primary"
                onClick={() => navigate('/stok-barang/tambah-kategori')}
                size="sm"
              >
                ➕ Tambah Category
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Categories List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
            <span className="ml-3 text-gray-600">Memuat data kategori...</span>
          </div>
        ) : filteredCategories.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📂</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">Tidak Ada Kategori</h3>
            <p className="text-gray-600 mb-4">
              {filters.search 
                ? `Tidak ditemukan kategori yang sesuai dengan pencarian "${filters.search}"`
                : 'Belum ada kategori barang yang tersedia'
              }
            </p>
            {filters.search && (
              <Button
                variant="outline"
                onClick={() => setFilters({ search: '' })}
              >
                🔍 Hapus Pencarian
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCategories.map((category: Kategori) => (
              <div 
                key={category.id} 
                className={`border rounded-lg p-4 transition-all ${
                  expandedCategory === category.id 
                    ? 'border-primary-500 shadow-lg' 
                    : 'border-gray-200 hover:shadow-md'
                }`}
              >
                <div 
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => toggleExpanded(category.id)}
                >
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-800">{category.nama_kategori}</h3>
                    <p className="text-sm text-gray-600">Kode: {category.kode_kategori}</p>
                  </div>
                  <span className="text-gray-400">
                    {expandedCategory === category.id ? '▼' : '▶'}
                  </span>
                </div>
                
                {expandedCategory === category.id && (
                  <div className="mt-4 pt-4 border-t space-y-2">
                    {category.deskripsi && (
                      <div>
                        <label className="text-xs font-medium text-gray-600">Deskripsi:</label>
                        <p className="text-sm text-gray-800">{category.deskripsi}</p>
                      </div>
                    )}
                    <div>
                      <label className="text-xs font-medium text-gray-600">Tanggal Dibuat:</label>
                      <p className="text-sm text-gray-800">{formatDate(category.created_at)}</p>
                    </div>
                    {category.parent_id && (
                      <div>
                        <label className="text-xs font-medium text-gray-600">Parent Category:</label>
                        <p className="text-sm text-gray-800">ID: {category.parent_id}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CategoryListPage;

