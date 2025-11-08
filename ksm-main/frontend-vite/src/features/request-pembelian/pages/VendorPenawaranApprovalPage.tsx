/**
 * Vendor Penawaran Approval Page
 * Halaman untuk approval penawaran vendor dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetRequestPembelianListQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table, Pagination } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';

const VendorPenawaranApprovalPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [filters, setFilters] = useState({
    status: '',
    search: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  const { data: requestsData, isLoading, error, refetch } = useGetRequestPembelianListQuery({
    ...filters,
    page: currentPage,
    per_page: itemsPerPage,
  });

  const requests = requestsData?.items || [];
  const pagination = requestsData?.pagination || { page: 1, per_page: 10, total: 0, pages: 1 };

  const formatCurrency = (amount: number) => {
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'submitted': return 'bg-blue-100 text-blue-800';
      case 'under_review': return 'bg-purple-100 text-purple-800';
      case 'vendor_selected': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
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
      key: 'vendor_penawarans_count',
      label: 'Penawarans',
      render: (_value: any, item: any) => (
        <span className="text-sm text-gray-600">{item.vendor_penawarans_count || 0}</span>
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
      render: (_value: any, item: any) => formatDate(item.created_at),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_value: any, item: any) => (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(`/request-pembelian/analisis-vendor/${item.id}`)}
          >
            Analisis
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate(`/request-pembelian/detail/${item.id}`)}
          >
            Detail
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
          <p className="text-red-600 mb-4">Gagal memuat data penawaran</p>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Vendor Penawaran Approval</h1>
            <p className="text-gray-600">Kelola dan approve penawaran vendor</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Cari request..."
              value={filters.search}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, search: e.target.value }));
                setCurrentPage(1);
              }}
              className="w-full"
            />
          </div>
          <div>
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
              <option value="vendor_selected">Vendor Selected</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={requests}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada penawaran untuk di-approve"
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

export default VendorPenawaranApprovalPage;

