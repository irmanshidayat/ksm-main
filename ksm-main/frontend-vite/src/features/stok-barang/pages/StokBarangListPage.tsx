/**
 * Stok Barang List Page
 * Halaman utama untuk melihat dan mengelola daftar barang
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBarangList } from '../hooks';
import { useUpdateBarangMutation, useDeleteBarangMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { Table, Pagination } from '@/shared/components/ui';
import { SearchAndFilter, EditBarangModal, DeleteConfirmModal, ExportModal } from '../components';
import type { Barang, FilterParams } from '../types';
import Swal from 'sweetalert2';

const StokBarangListPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const {
    barangList,
    supplierList,
    kategoriList,
    loading,
    error,
    pagination,
    refetch,
    debouncedRefetch,
    exportData
  } = useBarangList();
  
  const [updateBarang] = useUpdateBarangMutation();
  const [deleteBarang] = useDeleteBarangMutation();

  const [filters, setFilters] = useState<FilterParams>({});
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<Barang | null>(null);

  const handleFilterChange = (newFilters: FilterParams) => {
    setFilters(newFilters);
    setCurrentPage(1);
    refetch(newFilters, { page: 1, per_page: perPage });
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    refetch(filters, { page, per_page: perPage });
  };

  const handlePerPageChange = (newPerPage: number) => {
    setPerPage(newPerPage);
    setCurrentPage(1);
    refetch(filters, { page: 1, per_page: newPerPage });
  };

  const handleEdit = (item: Barang) => {
    setSelectedItem(item);
    setShowEditModal(true);
  };

  const handleDelete = (item: Barang) => {
    setSelectedItem(item);
    setShowDeleteModal(true);
  };

  const handleModalSuccess = () => {
    refetch(filters, { page: currentPage, per_page: perPage });
    setShowEditModal(false);
    setShowDeleteModal(false);
    setSelectedItem(null);
  };

  const handleView = (item: Barang) => {
    const details = `
      <div style="text-align: left; line-height: 1.6;">
        <p><strong>Kode:</strong> ${item.kode_barang}</p>
        <p><strong>Nama:</strong> ${item.nama_barang}</p>
        <p><strong>Kategori:</strong> ${item.kategori?.nama_kategori || '-'}</p>
        <p><strong>Satuan:</strong> ${item.satuan}</p>
        <p><strong>Harga:</strong> ${new Intl.NumberFormat('id-ID', {
          style: 'currency',
          currency: 'IDR',
          minimumFractionDigits: 0
        }).format(item.harga_per_unit || 0)}</p>
        <p><strong>Stok:</strong> ${item.stok?.jumlah_stok || 0}</p>
        <p><strong>Stok Min:</strong> ${item.stok?.stok_minimum || 0}</p>
        <p><strong>Stok Max:</strong> ${item.stok?.stok_maksimum || '-'}</p>
        <p><strong>Deskripsi:</strong> ${item.deskripsi || '-'}</p>
      </div>
    `;
    
    sweetAlert.showInfo('Detail Barang', details, {
      confirmButtonText: 'Tutup'
    });
  };

  const handleExport = async (exportFilters?: FilterParams, exportAll?: boolean) => {
    try {
      const result = await exportData(exportFilters);
      return result;
    } catch (error) {
      return false;
    }
  };

  const hasActiveFilters = Object.values(filters).some(value => 
    value !== undefined && value !== null && value !== ''
  );

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const columns = [
    {
      key: 'kode_barang',
      label: 'Kode',
      sortable: true,
    },
    {
      key: 'nama_barang',
      label: 'Nama Barang',
      sortable: true,
    },
    {
      key: 'kategori',
      label: 'Kategori',
      render: (_value: any, item: Barang) => item.kategori?.nama_kategori || '-',
    },
    {
      key: 'stok',
      label: 'Stok',
      render: (_value: any, item: Barang) => `${item.stok?.jumlah_stok || 0} ${item.satuan}`,
    },
    {
      key: 'harga_per_unit',
      label: 'Harga',
      render: (_value: any, item: Barang) => formatCurrency(item.harga_per_unit || 0),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: Barang) => (
        <div className="flex gap-2">
          <button
            onClick={() => handleView(item)}
            className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            👁️
          </button>
          <button
            onClick={() => handleEdit(item)}
            className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
          >
            ✏️
          </button>
          <button
            onClick={() => handleDelete(item)}
            className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            🗑️
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📋 Daftar Barang</h1>
            <p className="text-gray-600">Kelola data barang, stok, dan informasi terkait</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setShowExportModal(true)}
              disabled={loading}
            >
              📊 Export Excel
            </Button>
            <Button
              variant="primary"
              onClick={() => navigate('/stok-barang/tambah-barang')}
              disabled={loading}
            >
              ➕ Tambah Barang
            </Button>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <SearchAndFilter
        onFilterChange={handleFilterChange}
        onReset={() => {
          setFilters({});
          refetch({}, { page: 1, per_page: perPage });
        }}
        kategoriList={kategoriList}
        supplierList={supplierList}
        loading={loading}
        enableRealtimeSearch={true}
      />

      {/* Data Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12 bg-white rounded-lg shadow-md">
          <LoadingSpinner />
          <span className="ml-3 text-gray-600">Memuat data...</span>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <span className="text-4xl mb-4 block">⚠️</span>
          <h3 className="text-lg font-semibold text-red-800 mb-2">Terjadi Kesalahan</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <Button
            onClick={() => refetch(filters, { page: currentPage, per_page: perPage })}
          >
            🔄 Coba Lagi
          </Button>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow-md overflow-hidden mb-4">
            <Table
              data={barangList}
              columns={columns}
              loading={loading}
            />
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-sm text-gray-600">
                  Menampilkan {((currentPage - 1) * perPage) + 1} - {Math.min(currentPage * perPage, pagination.total)} dari {pagination.total} barang
                </div>
                <Pagination
                  currentPage={currentPage}
                  totalPages={pagination.pages}
                  onPageChange={handlePageChange}
                />
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-600">Per halaman:</label>
                  <select
                    value={perPage}
                    onChange={(e) => handlePerPageChange(parseInt(e.target.value))}
                    className="px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Modals */}
      <EditBarangModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedItem(null);
        }}
        onSuccess={handleModalSuccess}
        item={selectedItem}
      />

      <DeleteConfirmModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setSelectedItem(null);
        }}
        onSuccess={handleModalSuccess}
        item={selectedItem}
      />

      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        onExport={handleExport}
        currentFilters={filters}
        hasActiveFilters={hasActiveFilters}
      />
    </div>
  );
};

export default StokBarangListPage;

