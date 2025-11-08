/**
 * Vendor List Page (Admin)
 * Halaman untuk admin melihat dan mengelola daftar vendor dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetVendorsQuery, useDeleteVendorMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { Table, Pagination } from '@/shared/components/ui';
import type { Vendor } from '../types';

const VendorListPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading, error, refetch } = useGetVendorsQuery({
    page: currentPage,
    per_page: perPage,
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const [deleteVendor] = useDeleteVendorMutation();

  // SweetAlert loading
  useEffect(() => {
    if (isLoading) {
      sweetAlert.showLoading('Memuat...', 'Mengambil data vendor');
    } else {
      sweetAlert.hideLoading();
    }
  }, [isLoading, sweetAlert]);

  // Handle error
  useEffect(() => {
    (async () => {
      if (error && 'status' in error) {
        if (error.status === 401) {
          localStorage.removeItem('KSM_access_token');
          localStorage.removeItem('KSM_refresh_token');
          localStorage.removeItem('KSM_user');
          navigate('/login');
        } else if (error.status !== 404) {
          await sweetAlert.showError('Gagal Memuat', 'Terjadi kesalahan saat memuat data vendor.');
        }
      }
    })();
  }, [error, sweetAlert, navigate]);

  const handleDelete = async (vendor: Vendor) => {
    const confirmed = await sweetAlert.showConfirm(
      'Hapus Vendor',
      `Apakah Anda yakin ingin menghapus ${vendor.company_name}?`
    );

    if (confirmed) {
      try {
        sweetAlert.showLoading('Menghapus...', 'Sedang menghapus vendor');
        await deleteVendor(vendor.id).unwrap();
        sweetAlert.hideLoading();
        await sweetAlert.showSuccessAuto('Berhasil', 'Vendor berhasil dihapus');
        refetch();
      } catch (error: any) {
        sweetAlert.hideLoading();
        await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menghapus vendor');
      }
    }
  };

  const columns = [
    {
      key: 'company_name',
      label: 'Nama Perusahaan',
      sortable: true,
    },
    {
      key: 'contact_person',
      label: 'Contact Person',
    },
    {
      key: 'email',
      label: 'Email',
    },
    {
      key: 'vendor_category',
      label: 'Kategori',
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: Vendor) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          item.status === 'active' ? 'bg-green-100 text-green-800' :
          item.status === 'inactive' ? 'bg-gray-100 text-gray-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          {item.status}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: Vendor) => (
        <div className="flex gap-2">
          <button
            onClick={() => navigate(`/vendor/detail/${item.id}`)}
            className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            👁️
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

  if (isLoading) return null;

  if (error && 'status' in error && error.status !== 404) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Gagal memuat data vendor</p>
          <Button variant="primary" onClick={() => refetch()}>
            Coba Lagi
          </Button>
        </div>
      </div>
    );
  }

  const vendors = data?.items || [];
  const pagination = {
    page: data?.page || 1,
    per_page: data?.per_page || 10,
    total: data?.total || 0,
    pages: data?.pages || 0,
  };

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Daftar Vendor</h1>
            <p className="text-gray-600">Kelola data vendor dan informasi terkait</p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Cari vendor..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full"
            />
          </div>
          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Semua Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="pending">Pending</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={vendors}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada vendor"
        />
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * perPage) + 1} - {Math.min(currentPage * perPage, pagination.total)} dari {pagination.total} vendor
            </div>
            <Pagination
              currentPage={currentPage}
              totalPages={pagination.pages}
              onPageChange={(page) => {
                setCurrentPage(page);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Per halaman:</label>
              <select
                value={perPage}
                onChange={(e) => {
                  setPerPage(parseInt(e.target.value));
                  setCurrentPage(1);
                }}
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
    </div>
  );
};

export default VendorListPage;

