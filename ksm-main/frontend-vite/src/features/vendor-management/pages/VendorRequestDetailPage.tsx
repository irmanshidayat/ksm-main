/**
 * Vendor Request Detail Page
 * Halaman detail request pembelian untuk vendor dengan Tailwind CSS
 */

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useGetVendorRequestDetailQuery } from '../store';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';

const VendorRequestDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { requestId } = useParams<{ requestId: string }>();
  const requestIdNum = requestId ? parseInt(requestId) : 0;

  const { data: request, isLoading, error, refetch } = useGetVendorRequestDetailQuery(requestIdNum);

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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0
    }).format(amount);
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
          <p className="text-red-600 mb-4">Gagal memuat detail request</p>
          <div className="flex gap-2 justify-center">
            <Button variant="outline" onClick={() => navigate('/vendor/requests')}>
              Kembali ke Daftar Request
            </Button>
            <Button variant="primary" onClick={() => refetch()}>
              Coba Lagi
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!request) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">Request Tidak Ditemukan</h3>
          <p className="text-yellow-600 mb-4">Request yang Anda cari tidak ditemukan atau tidak dapat diakses.</p>
          <Button variant="primary" onClick={() => navigate('/vendor/requests')}>
            Kembali ke Daftar Request
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
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl md:text-3xl font-bold text-gray-800">#{request.reference_id}</h1>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(request.priority)}`}>
                {getPriorityText(request.priority)}
              </span>
              {request.is_overdue && (
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                  ⚠️ Terlambat
                </span>
              )}
            </div>
            <h2 className="text-xl font-semibold text-gray-700">{request.title}</h2>
          </div>
          <div className="flex gap-2">
            {request.can_upload && (
              <Button
                variant="primary"
                onClick={() => navigate(`/vendor/upload-penawaran/${requestId}`)}
              >
                📤 Upload Penawaran
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => navigate('/vendor/requests')}
            >
              ← Kembali
            </Button>
          </div>
        </div>
      </div>

      {/* Request Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Informasi Request</h3>
          <div className="space-y-3">
            <div>
              <span className="text-sm text-gray-600">Request Date:</span>
              <p className="text-sm font-medium text-gray-800">{formatDate(request.request_date)}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Required Date:</span>
              <p className="text-sm font-medium text-gray-800">
                {request.required_date ? formatDate(request.required_date) : '-'}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Deadline Upload:</span>
              <p className={`text-sm font-medium ${request.is_overdue ? 'text-red-600' : 'text-gray-800'}`}>
                {request.vendor_upload_deadline ? formatDateTime(request.vendor_upload_deadline) : '-'}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Status:</span>
              <p className="text-sm font-medium text-gray-800">{getStatusText(request.status)}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Statistik</h3>
          <div className="space-y-3">
            <div>
              <span className="text-sm text-gray-600">Jumlah Items:</span>
              <p className="text-sm font-medium text-gray-800">{request.items_count || request.items?.length || 0} item</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Penawaran Terkirim:</span>
              <p className="text-sm font-medium text-gray-800">{request.vendor_penawarans_count || 0}</p>
            </div>
            {request.days_remaining !== null && (
              <div>
                <span className="text-sm text-gray-600">Hari Tersisa:</span>
                <p className={`text-sm font-medium ${request.days_remaining < 3 ? 'text-red-600' : 'text-gray-800'}`}>
                  {request.days_remaining} hari
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Description */}
      {request.description && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Deskripsi</h3>
          <p className="text-gray-700 whitespace-pre-wrap">{request.description}</p>
        </div>
      )}

      {/* Items List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Daftar Items</h3>
        {request.items && request.items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">No</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nama Barang</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kategori</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Satuan</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Spesifikasi</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {request.items.map((item: any, index: number) => (
                  <tr key={item.id}>
                    <td className="px-4 py-3 text-sm text-gray-900">{index + 1}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.nama_barang || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{item.kategori || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{item.quantity}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{item.satuan || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{item.specifications || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-600 text-center py-8">Tidak ada items</p>
        )}
      </div>
    </div>
  );
};

export default VendorRequestDetailPage;

