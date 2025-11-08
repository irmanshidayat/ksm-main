/**
 * Vendor Requests Page
 * Halaman untuk melihat daftar request pembelian yang tersedia dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetVendorRequestsQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';

const VendorRequestsPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const { data: requests = [], isLoading, error, refetch } = useGetVendorRequestsQuery({
    limit,
    offset,
    category_filter: categoryFilter !== 'all' ? categoryFilter : undefined
  });

  // SweetAlert loading
  useEffect(() => {
    if (isLoading) {
      sweetAlert.showLoading('Memuat...', 'Mengambil data request pembelian');
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
          await sweetAlert.showError('Gagal Memuat', 'Terjadi kesalahan saat memuat request pembelian.');
        }
      }
    })();
  }, [error, sweetAlert, navigate]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-blue-100 text-blue-800';
    }
  };

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'Mendesak';
      case 'high': return 'Tinggi';
      case 'medium': return 'Sedang';
      case 'low': return 'Rendah';
      default: return priority;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'submitted': return 'Dikirim';
      case 'vendor_uploading': return 'Vendor Upload';
      case 'under_analysis': return 'Dianalisis';
      case 'approved': return 'Disetujui';
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
          <p className="text-red-600 mb-4">Gagal memuat request</p>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Request Pembelian</h1>
            <p className="text-gray-600">Lihat dan upload penawaran untuk request yang tersedia</p>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter Kategori</label>
            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setOffset(0);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Kategori</option>
              {/* Categories akan diisi dari API */}
            </select>
          </div>
        </div>
      </div>

      {/* Requests List */}
      {requests.length > 0 ? (
        <div className="space-y-4">
          {requests.map((request: any) => (
            <div
              key={request.id}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-800">#{request.reference_id}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(request.priority)}`}>
                      {getPriorityText(request.priority)}
                    </span>
                    {request.is_overdue && (
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        ⚠️ Terlambat
                      </span>
                    )}
                  </div>
                  <h4 className="text-xl font-bold text-gray-900 mb-2">{request.title}</h4>
                  {request.description && (
                    <p className="text-gray-600 mb-3 line-clamp-2">{request.description}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <span className="text-sm text-gray-600">Request Date:</span>
                  <p className="text-sm font-medium text-gray-800">{formatDate(request.request_date)}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Deadline Upload:</span>
                  <p className={`text-sm font-medium ${request.is_overdue ? 'text-red-600' : 'text-gray-800'}`}>
                    {formatDateTime(request.vendor_upload_deadline)}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Items:</span>
                  <p className="text-sm font-medium text-gray-800">{request.items_count} item</p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-2 pt-4 border-t border-gray-200">
                {request.can_upload ? (
                  <Button
                    variant="primary"
                    onClick={() => navigate(`/vendor/upload-penawaran/${request.id}`)}
                  >
                    📤 Upload Penawaran
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    disabled
                  >
                    {request.has_penawaran ? '✅ Penawaran Sudah Dikirim' : '⏸️ Tidak Dapat Upload'}
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={() => navigate(`/vendor/requests/${request.id}`)}
                >
                  👁️ Lihat Detail
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Tidak Ada Request</h3>
          <p className="text-gray-600">Tidak ada request pembelian yang tersedia saat ini</p>
        </div>
      )}
    </div>
  );
};

export default VendorRequestsPage;

