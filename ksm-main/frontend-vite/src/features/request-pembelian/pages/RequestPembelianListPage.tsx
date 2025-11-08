/**
 * Request Pembelian List Page
 * Halaman daftar request pembelian dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useGetRequestPembelianListQuery, useDeleteRequestPembelianMutation, useApproveRequestPembelianMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table, Pagination } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { CheckIcon, EyeIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';
import { formatCurrency } from '@/core/utils/format';

const RequestPembelianListPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: '',
    dateFrom: '',
    dateTo: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [showFilters, setShowFilters] = useState(false);

  const { data: requestsData, isLoading, error, refetch } = useGetRequestPembelianListQuery({
    ...filters,
    page: currentPage,
    per_page: itemsPerPage,
  });

  const [deleteRequest] = useDeleteRequestPembelianMutation();
  const [approveRequest] = useApproveRequestPembelianMutation();

  const requests = requestsData?.items || [];
  const pagination = requestsData?.pagination || { page: 1, per_page: 10, total: 0, pages: 1 };

  // Helper untuk reset page saat filter berubah
  const handleFilterChange = (updater: (prev: typeof filters) => typeof filters) => {
    setFilters(updater);
    setCurrentPage(1);
  };

  // Format date dengan format yang sesuai (menggunakan utility dengan custom format)
  const formatDateDisplay = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'submitted': return 'bg-blue-100 text-blue-800';
      case 'vendor_uploading': return 'bg-yellow-100 text-yellow-800';
      case 'under_analysis': return 'bg-purple-100 text-purple-800';
      case 'vendor_selected': return 'bg-green-100 text-green-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleDelete = async (requestId: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Hapus Request',
      'Apakah Anda yakin ingin menghapus request ini?'
    );

    if (confirmed) {
      try {
        sweetAlert.showLoading('Menghapus...', 'Sedang menghapus request...');
        await deleteRequest(requestId).unwrap();
        sweetAlert.hideLoading();
        await sweetAlert.showSuccessAuto('Berhasil', 'Request berhasil dihapus');
        refetch();
      } catch (error: any) {
        sweetAlert.hideLoading();
        await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menghapus request');
      }
    }
  };

  const handleApprove = async (requestId: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Setujui Request',
      'Apakah Anda yakin ingin menyetujui request ini?'
    );

    if (confirmed) {
      try {
        sweetAlert.showLoading('Menyetujui...', 'Sedang menyetujui request...');
        await approveRequest({ id: requestId }).unwrap();
        sweetAlert.hideLoading();
        await sweetAlert.showSuccessAuto('Berhasil', 'Request berhasil disetujui');
        refetch();
      } catch (error: any) {
        sweetAlert.hideLoading();
        await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menyetujui request');
      }
    }
  };

  const columns = [
    {
      key: 'reference_id',
      label: 'Reference ID',
      render: (_value: any, item: any) => (
        <span className="font-mono text-sm font-semibold">{item.reference_id}</span>
      ),
    },
    {
      key: 'title',
      label: 'Title',
      render: (_value: any, item: any) => (
        <span className="font-medium text-gray-800">{item.title}</span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: any) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
          {item.status}
        </span>
      ),
    },
    {
      key: 'priority',
      label: 'Priority',
      render: (_value: any, item: any) => (
        <span className="text-sm text-gray-600 capitalize">{item.priority}</span>
      ),
    },
    {
      key: 'total_budget',
      label: 'Budget',
      render: (_value: any, item: any) => (
        <span className="font-medium">{formatCurrency(item.total_budget || 0)}</span>
      ),
    },
    {
      key: 'created_at',
      label: 'Date',
      render: (_value: any, item: any) => formatDateDisplay(item.created_at),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_value: any, item: any) => (
        <div className="flex gap-2 items-center">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(`/request-pembelian/detail/${item.id}`)}
            title="Detail"
            className="p-1.5"
          >
            <EyeIcon className="w-4 h-4" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(`/request-pembelian/edit-request/${item.id}`)}
            title="Edit"
            className="p-1.5"
          >
            <PencilIcon className="w-4 h-4" />
          </Button>

          <Button
            variant="danger"
            size="sm"
            onClick={() => handleDelete(item.id)}
            title="Delete"
            className="p-1.5"
          >
            <TrashIcon className="w-4 h-4" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleApprove(item.id)}
            title="Setujui"
            className="p-1.5"
          >
            <CheckIcon className="w-4 h-4" />
          </Button>
        </div>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Gagal memuat data request</p>
          <Button variant="primary" onClick={() => refetch()}>
            Coba Lagi
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Daftar Request Pembelian</h1>
            <p className="text-gray-600">Kelola semua request pembelian</p>
          </div>
          <Link to="/request-pembelian/buat-request">
            <Button variant="primary">
              ➕ Buat Request Baru
            </Button>
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">Filter</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            {showFilters ? 'Sembunyikan' : 'Tampilkan'} Filter
          </Button>
        </div>
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <Input
                type="text"
                placeholder="Cari request..."
                value={filters.search}
                onChange={(e) => {
                  handleFilterChange(prev => ({ ...prev, search: e.target.value }));
                }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={filters.status}
                onChange={(e) => {
                  handleFilterChange(prev => ({ ...prev, status: e.target.value }));
                }}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Semua Status</option>
                <option value="draft">Draft</option>
                <option value="submitted">Submitted</option>
                <option value="vendor_uploading">Vendor Uploading</option>
                <option value="under_analysis">Under Analysis</option>
                <option value="vendor_selected">Vendor Selected</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
              <select
                value={filters.priority}
                onChange={(e) => {
                  handleFilterChange(prev => ({ ...prev, priority: e.target.value }));
                }}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Semua Prioritas</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Dari Tanggal</label>
              <Input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => {
                  handleFilterChange(prev => ({ ...prev, dateFrom: e.target.value }));
                }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sampai Tanggal</label>
              <Input
                type="date"
                value={filters.dateTo}
                onChange={(e) => {
                  handleFilterChange(prev => ({ ...prev, dateTo: e.target.value }));
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={requests}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada request pembelian"
        />
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, pagination.total)} dari {pagination.total} request
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
    </div>
  );
};

export default RequestPembelianListPage;

