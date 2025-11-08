/**
 * Vendor History Page
 * Halaman riwayat penawaran vendor dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetVendorHistoryQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { Table, Pagination } from '@/shared/components/ui';

const VendorHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [statusFilter, setStatusFilter] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const { data, isLoading, error, refetch } = useGetVendorHistoryQuery({
    page: currentPage,
    limit: itemsPerPage,
    status: statusFilter !== 'all' ? statusFilter : undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  });

  // SweetAlert loading
  useEffect(() => {
    if (isLoading) {
      sweetAlert.showLoading('Memuat...', 'Mengambil riwayat penawaran');
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
          await sweetAlert.showError('Gagal Memuat', 'Terjadi kesalahan saat memuat riwayat penawaran.');
        }
      }
    })();
  }, [error, sweetAlert, navigate]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'submitted': return 'bg-yellow-100 text-yellow-800';
      case 'under_review': return 'bg-blue-100 text-blue-800';
      case 'selected': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'submitted': return 'Dikirim';
      case 'under_review': return 'Ditinjau';
      case 'selected': return 'Dipilih';
      case 'rejected': return 'Ditolak';
      default: return status;
    }
  };

  if (isLoading) return null;

  if (error && 'status' in error && error.status !== 404) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Gagal memuat riwayat penawaran</p>
          <Button variant="primary" onClick={() => refetch()}>
            Coba Lagi
          </Button>
        </div>
      </div>
    );
  }

  const history = data?.data || [];
  const pagination = data?.pagination || { page: 1, per_page: 10, total: 0, pages: 0 };
  const statistics = data?.statistics || { total_count: 0, success_rate: 0 };

  const columns = [
    {
      key: 'reference_id',
      label: 'Reference ID',
      render: (_value: any, item: any) => (
        <span className="font-mono text-sm">{item.reference_id}</span>
      ),
    },
    {
      key: 'request_title',
      label: 'Request',
      render: (_value: any, item: any) => (
        <div>
          <p className="font-medium text-gray-800">{item.request_title || '-'}</p>
          <p className="text-xs text-gray-500">{item.request_reference_id}</p>
        </div>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: any) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
          {getStatusText(item.status)}
        </span>
      ),
    },
    {
      key: 'total_quoted_price',
      label: 'Total Harga',
      render: (_value: any, item: any) => (
        <span className="font-medium">
          {item.total_quoted_price ? formatCurrency(item.total_quoted_price) : '-'}
        </span>
      ),
    },
    {
      key: 'submission_date',
      label: 'Tanggal Submit',
      render: (_value: any, item: any) => formatDate(item.submission_date),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: any) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/vendor/requests/${item.request_id}`)}
        >
          Lihat Detail
        </Button>
      ),
    },
  ];

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Riwayat Penawaran</h1>
            <p className="text-gray-600">Lihat semua penawaran yang telah Anda kirim</p>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📊</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.total_count}</h3>
              <p className="text-sm text-gray-600">Total Penawaran</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📈</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.success_rate}%</h3>
              <p className="text-sm text-gray-600">Tingkat Sukses</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Status</option>
              <option value="submitted">Dikirim</option>
              <option value="under_review">Ditinjau</option>
              <option value="selected">Dipilih</option>
              <option value="rejected">Ditolak</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Dari Tanggal</label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sampai Tanggal</label>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full"
            />
          </div>
          <div className="flex items-end">
            <Button
              variant="outline"
              onClick={() => {
                setStatusFilter('all');
                setStartDate('');
                setEndDate('');
                setCurrentPage(1);
              }}
              className="w-full"
            >
              Reset Filter
            </Button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={history}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada riwayat penawaran"
        />
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, pagination.total)} dari {pagination.total} penawaran
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

export default VendorHistoryPage;

