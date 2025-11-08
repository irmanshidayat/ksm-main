/**
 * Vendor Pesanan Page
 * Halaman untuk melihat pesanan vendor dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetVendorOrdersQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { Table, Pagination } from '@/shared/components/ui';

const VendorPesananPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(12);
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');

  const { data, isLoading, error, refetch } = useGetVendorOrdersQuery({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    search: search || undefined,
    page: currentPage,
    per_page: perPage,
    sort_by: 'created_at',
    sort_dir: 'desc',
  });

  // SweetAlert loading
  useEffect(() => {
    if (isLoading) {
      sweetAlert.showLoading('Memuat...', 'Mengambil data pesanan');
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
        } else if (error.status === 403) {
          // 403 Forbidden - User tidak memiliki role vendor
          const errorData = 'data' in error ? error.data : null;
          const message = errorData?.message || errorData?.error || 'Anda tidak memiliki izin untuk mengakses halaman ini.';
          await sweetAlert.showError(
            'Akses Ditolak',
            `${message}\n\nHalaman ini hanya dapat diakses oleh vendor. Pastikan akun Anda memiliki role vendor.`
          );
        } else if (error.status !== 404) {
          await sweetAlert.showError('Gagal Memuat', 'Terjadi kesalahan saat memuat data pesanan.');
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
      day: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending_confirmation': return 'bg-yellow-100 text-yellow-800';
      case 'confirmed': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-purple-100 text-purple-800';
      case 'shipped': return 'bg-indigo-100 text-indigo-800';
      case 'delivered': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending_confirmation': return 'Menunggu Konfirmasi';
      case 'confirmed': return 'Dikonfirmasi';
      case 'in_progress': return 'Sedang Diproses';
      case 'shipped': return 'Dikirim';
      case 'delivered': return 'Terkirim';
      case 'cancelled': return 'Dibatalkan';
      default: return status;
    }
  };

  if (isLoading) return null;

  if (error && 'status' in error) {
    if (error.status === 403) {
      // 403 Forbidden - Tampilkan pesan khusus
      const errorData = 'data' in error ? error.data : null;
      const message = errorData?.message || errorData?.error || 'Anda tidak memiliki izin untuk mengakses halaman ini.';
      return (
        <div className="p-4 md:p-6 lg:p-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <div className="text-6xl mb-4">🔒</div>
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">Akses Ditolak</h3>
            <p className="text-yellow-700 mb-4">{message}</p>
            <p className="text-sm text-yellow-600 mb-4">
              Halaman ini hanya dapat diakses oleh vendor. Pastikan akun Anda memiliki role vendor.
            </p>
            <div className="flex gap-2 justify-center">
              <Button variant="outline" onClick={() => navigate('/vendor/dashboard')}>
                Kembali ke Dashboard
              </Button>
              <Button variant="primary" onClick={() => refetch()}>
                Coba Lagi
              </Button>
            </div>
          </div>
        </div>
      );
    } else if (error.status !== 404) {
      return (
        <div className="p-4 md:p-6 lg:p-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
            <p className="text-red-600 mb-4">Gagal memuat data pesanan</p>
            <Button variant="primary" onClick={() => refetch()}>
              Coba Lagi
            </Button>
          </div>
        </div>
      );
    }
  }

  const orders = data?.orders || [];
  const pagination = data?.pagination || { page: 1, per_page: 12, total: 0, pages: 0 };
  const statistics = data?.statistics || { total_orders: 0, total_value: 0 };

  const columns = [
    {
      key: 'order_reference',
      label: 'Reference',
      render: (_value: any, item: any) => (
        <span className="font-mono text-sm font-semibold">{item.order_reference || item.id}</span>
      ),
    },
    {
      key: 'request_reference',
      label: 'Request',
      render: (_value: any, item: any) => (
        <span className="font-mono text-xs text-gray-600">{item.request_reference || '-'}</span>
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
      key: 'total_amount',
      label: 'Total',
      render: (_value: any, item: any) => (
        <span className="font-medium">{formatCurrency(item.total_amount || 0)}</span>
      ),
    },
    {
      key: 'created_at',
      label: 'Tanggal',
      render: (_value: any, item: any) => formatDate(item.created_at),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: any) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/vendor/pesanan/${item.id}`)}
        >
          Detail
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Pesanan Saya</h1>
            <p className="text-gray-600">Kelola dan monitor pesanan dari perusahaan</p>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📦</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.total_orders || 0}</h3>
              <p className="text-sm text-gray-600">Total Pesanan</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">💰</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{formatCurrency(statistics.total_value || 0)}</h3>
              <p className="text-sm text-gray-600">Total Nilai</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Cari pesanan..."
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
              <option value="all">Semua Status</option>
              <option value="pending_confirmation">Menunggu Konfirmasi</option>
              <option value="confirmed">Dikonfirmasi</option>
              <option value="in_progress">Sedang Diproses</option>
              <option value="shipped">Dikirim</option>
              <option value="delivered">Terkirim</option>
              <option value="cancelled">Dibatalkan</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={orders}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada pesanan"
        />
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * perPage) + 1} - {Math.min(currentPage * perPage, pagination.total)} dari {pagination.total} pesanan
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
                <option value={12}>12</option>
                <option value={24}>24</option>
                <option value={48}>48</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VendorPesananPage;

