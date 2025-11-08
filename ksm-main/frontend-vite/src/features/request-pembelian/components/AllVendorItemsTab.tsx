/**
 * All Vendor Items Tab Component
 * Tab untuk menampilkan semua barang vendor penawaran dari semua request
 */

import React, { useState } from 'react';
import { useGetAllVendorCatalogItemsQuery, useUpdateVendorCatalogItemMutation, useDeleteVendorCatalogItemMutation, useSendVendorEmailMutation } from '../store';
import { useGetVendorsQuery } from '@/features/vendor-management';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table, Pagination } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { PencilIcon, TrashIcon, EnvelopeIcon } from '@heroicons/react/24/outline';
import Swal from 'sweetalert2';
import VendorCatalogImportModal from './VendorCatalogImportModal';
import VendorCatalogItemUpdateModal from './VendorCatalogItemUpdateModal';
import VendorCatalogSendEmailModal from './VendorCatalogSendEmailModal';

const AllVendorItemsTab: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [filters, setFilters] = useState({
    search: '',
    vendor_id: '',
    status: '',
    kategori: '',
    merek: '',
    date_from: '',
    date_to: '',
    min_harga: '',
    max_harga: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [showFilters, setShowFilters] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [selectedItemForUpdate, setSelectedItemForUpdate] = useState<any | null>(null);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [selectedItemForEmail, setSelectedItemForEmail] = useState<any | null>(null);
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);

  // Mutations
  const [updateItem] = useUpdateVendorCatalogItemMutation();
  const [deleteItem] = useDeleteVendorCatalogItemMutation();
  const [sendEmail] = useSendVendorEmailMutation();

  // Get vendors for filter dropdown
  const { data: vendorsData } = useGetVendorsQuery({ page: 1, per_page: 100 });
  const vendors = vendorsData?.items || [];

  // Get all vendor catalog items
  const { data: itemsData, isLoading, error, refetch } = useGetAllVendorCatalogItemsQuery({
    page: currentPage,
    per_page: itemsPerPage,
    ...(filters.search && { search: filters.search }),
    ...(filters.vendor_id && { vendor_id: parseInt(filters.vendor_id) }),
    ...(filters.status && { status: filters.status }),
    ...(filters.kategori && { kategori: filters.kategori }),
    ...(filters.merek && { merek: filters.merek }),
    ...(filters.date_from && { date_from: filters.date_from }),
    ...(filters.date_to && { date_to: filters.date_to }),
    ...(filters.min_harga && { min_harga: parseFloat(filters.min_harga) }),
    ...(filters.max_harga && { max_harga: parseFloat(filters.max_harga) }),
  });

  const items = itemsData?.data || [];
  const pagination = itemsData?.pagination || { page: 1, per_page: 20, total: 0, pages: 1, has_next: false, has_prev: false };

  const formatCurrency = (amount?: number) => {
    if (!amount) return '-';
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleExport = async () => {
    try {
      Swal.fire({
        title: 'Mengekspor...',
        text: 'Sedang memproses data untuk ekspor...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const token = localStorage.getItem('KSM_access_token');
      const apiUrl = import.meta.env.VITE_APP_API_URL || 'http://localhost:8000';
      
      // Build query params
      const params = new URLSearchParams();
      params.append('format', 'excel');
      if (filters.search) params.append('search', filters.search);
      if (filters.vendor_id) params.append('vendor_id', filters.vendor_id);
      if (filters.status) params.append('status', filters.status);
      if (filters.kategori) params.append('kategori', filters.kategori);
      if (filters.merek) params.append('merek', filters.merek);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      if (filters.min_harga) params.append('min_harga', filters.min_harga);
      if (filters.max_harga) params.append('max_harga', filters.max_harga);

      const response = await fetch(`${apiUrl}/api/vendor-catalog/export?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `daftar-barang-vendor-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
        
        Swal.close();
        await sweetAlert.showSuccessAuto('Berhasil', 'Data berhasil diekspor ke Excel');
      } else {
        throw new Error('Gagal mengekspor data');
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.message || 'Gagal mengekspor data');
    }
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      vendor_id: '',
      status: '',
      kategori: '',
      merek: '',
      date_from: '',
      date_to: '',
      min_harga: '',
      max_harga: '',
    });
    setCurrentPage(1);
  };

  const handleUpdate = (item: any) => {
    setSelectedItemForUpdate(item);
    setIsUpdateModalOpen(true);
  };

  const handleDelete = async (item: any) => {
    const result = await Swal.fire({
      title: 'Hapus Barang Vendor?',
      text: `Apakah Anda yakin ingin menghapus "${item.nama_barang || item.request_item?.nama_barang || 'item ini'}"?`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#dc2626',
      cancelButtonColor: '#6b7280',
      confirmButtonText: 'Ya, Hapus',
      cancelButtonText: 'Batal',
    });

    if (result.isConfirmed) {
      try {
        Swal.fire({
          title: 'Menghapus...',
          text: 'Sedang menghapus data...',
          allowOutsideClick: false,
          allowEscapeKey: false,
          showConfirmButton: false,
          didOpen: () => {
            Swal.showLoading();
          },
        });

        const response = await deleteItem(item.id).unwrap();
        
        Swal.close();
        if (response.success) {
          await sweetAlert.showSuccessAuto('Berhasil', 'Barang vendor berhasil dihapus');
          refetch();
        } else {
          await sweetAlert.showError('Gagal', response.message || 'Gagal menghapus barang vendor');
        }
      } catch (error: any) {
        Swal.close();
        await sweetAlert.showError('Gagal', error?.data?.message || error?.message || 'Gagal menghapus barang vendor');
      }
    }
  };

  const handleSendEmail = (item: any) => {
    setSelectedItemForEmail(item);
    setIsEmailModalOpen(true);
  };

  const columns = [
    {
      key: 'nama_barang',
      label: 'Nama Barang',
      render: (_value: any, item: any) => (
        <span className="font-medium text-gray-800">{item.nama_barang || item.request_item?.nama_barang || '-'}</span>
      ),
    },
    {
      key: 'vendor',
      label: 'Vendor',
      render: (_value: any, item: any) => (
        <div>
          <p className="font-medium text-gray-800">{item.vendor?.company_name || '-'}</p>
          <p className="text-xs text-gray-500">{item.vendor?.email || ''}</p>
        </div>
      ),
    },
    {
      key: 'request',
      label: 'Request ID',
      render: (_value: any, item: any) => (
        <span className="font-mono text-sm">{item.request?.reference_id || '-'}</span>
      ),
    },
    {
      key: 'kategori',
      label: 'Kategori',
      render: (_value: any, item: any) => (
        <span className="text-sm text-gray-600">{item.kategori || '-'}</span>
      ),
    },
    {
      key: 'vendor_merk',
      label: 'Merek',
      render: (_value: any, item: any) => (
        <span className="text-sm text-gray-600">{item.vendor_merk || '-'}</span>
      ),
    },
    {
      key: 'vendor_quantity',
      label: 'Quantity',
      render: (_value: any, item: any) => (
        <span className="text-sm text-gray-600">
          {item.vendor_quantity || 0} {item.satuan || 'pcs'}
        </span>
      ),
    },
    {
      key: 'vendor_unit_price',
      label: 'Harga Satuan',
      render: (_value: any, item: any) => (
        <span className="font-medium text-gray-800">{formatCurrency(item.vendor_unit_price)}</span>
      ),
    },
    {
      key: 'vendor_total_price',
      label: 'Harga Total',
      render: (_value: any, item: any) => (
        <span className="font-semibold text-primary-600">{formatCurrency(item.vendor_total_price)}</span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: any) => {
        const status = item.penawaran?.status || '-';
        const statusColors: Record<string, string> = {
          'submitted': 'bg-blue-100 text-blue-800',
          'under_review': 'bg-purple-100 text-purple-800',
          'approved': 'bg-green-100 text-green-800',
          'rejected': 'bg-red-100 text-red-800',
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
            {status}
          </span>
        );
      },
    },
    {
      key: 'created_at',
      label: 'Tanggal',
      render: (_value: any, item: any) => formatDate(item.created_at),
    },
    {
      key: 'actions',
      label: 'Action',
      render: (_value: any, item: any) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleUpdate(item)}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="Update"
          >
            <PencilIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => handleDelete(item)}
            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Delete"
          >
            <TrashIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => handleSendEmail(item)}
            className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
            title="Send Email"
          >
            <EnvelopeIcon className="w-5 h-5" />
          </button>
        </div>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
        <p className="text-red-600 mb-4">Gagal memuat data barang vendor</p>
        <Button variant="primary" onClick={() => refetch()}>
          Coba Lagi
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters & Export */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-gray-800">Filter & Pencarian</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              {showFilters ? 'Sembunyikan' : 'Tampilkan'} Filter
            </Button>
            {(filters.search || filters.vendor_id || filters.status || filters.kategori || filters.merek || filters.date_from || filters.date_to || filters.min_harga || filters.max_harga) && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleResetFilters}
              >
                Reset Filter
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setIsImportModalOpen(true)}
              className="flex items-center gap-2"
            >
              <span>📤</span>
              Import
            </Button>
            <Button
              variant="primary"
              onClick={handleExport}
              className="flex items-center gap-2"
            >
              <span>📥</span>
              Export Excel
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="mb-4">
          <Input
            type="text"
            placeholder="Cari barang, vendor, request ID..."
            value={filters.search}
            onChange={(e) => {
              setFilters(prev => ({ ...prev, search: e.target.value }));
              setCurrentPage(1);
            }}
            className="w-full"
          />
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Vendor</label>
              <select
                value={filters.vendor_id}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, vendor_id: e.target.value }));
                  setCurrentPage(1);
                }}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Semua Vendor</option>
                {vendors.map((vendor: any) => (
                  <option key={vendor.id} value={vendor.id.toString()}>
                    {vendor.company_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={filters.status}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, status: e.target.value }));
                  setCurrentPage(1);
                }}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Semua Status</option>
                <option value="submitted">Submitted</option>
                <option value="under_review">Under Review</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Kategori</label>
              <Input
                type="text"
                placeholder="Kategori..."
                value={filters.kategori}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, kategori: e.target.value }));
                  setCurrentPage(1);
                }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Merek</label>
              <Input
                type="text"
                placeholder="Merek..."
                value={filters.merek}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, merek: e.target.value }));
                  setCurrentPage(1);
                }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Dari Tanggal</label>
              <Input
                type="date"
                value={filters.date_from}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, date_from: e.target.value }));
                  setCurrentPage(1);
                }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sampai Tanggal</label>
              <Input
                type="date"
                value={filters.date_to}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, date_to: e.target.value }));
                  setCurrentPage(1);
                }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Harga Min</label>
              <Input
                type="number"
                placeholder="Harga minimum..."
                value={filters.min_harga}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, min_harga: e.target.value }));
                  setCurrentPage(1);
                }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Harga Max</label>
              <Input
                type="number"
                placeholder="Harga maksimum..."
                value={filters.max_harga}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, max_harga: e.target.value }));
                  setCurrentPage(1);
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={items}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada barang vendor ditemukan"
        />
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, pagination.total)} dari {pagination.total} barang
            </div>
            <Pagination
              currentPage={currentPage}
              totalPages={pagination.pages}
              onPageChange={(page) => {
                setCurrentPage(page);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
          </div>
        </div>
      )}

      {/* Import Modal */}
      <VendorCatalogImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImportSuccess={() => {
          refetch();
        }}
      />

      {/* Update Modal */}
      <VendorCatalogItemUpdateModal
        isOpen={isUpdateModalOpen}
        onClose={() => {
          setIsUpdateModalOpen(false);
          setSelectedItemForUpdate(null);
        }}
        item={selectedItemForUpdate}
        onUpdateSuccess={() => {
          refetch();
          setIsUpdateModalOpen(false);
          setSelectedItemForUpdate(null);
        }}
      />

      {/* Send Email Modal */}
      <VendorCatalogSendEmailModal
        isOpen={isEmailModalOpen}
        onClose={() => {
          setIsEmailModalOpen(false);
          setSelectedItemForEmail(null);
        }}
        item={selectedItemForEmail}
        onSendSuccess={() => {
          setIsEmailModalOpen(false);
          setSelectedItemForEmail(null);
        }}
      />
    </div>
  );
};

export default AllVendorItemsTab;

