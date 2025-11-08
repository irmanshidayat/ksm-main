/**
 * Request Pembelian Detail Page
 * Halaman detail request pembelian dengan Tailwind CSS
 */

import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useGetRequestPembelianByIdQuery, useDeleteRequestPembelianMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import Swal from 'sweetalert2';

const RequestPembelianDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const requestId = id ? parseInt(id) : 0;

  const { data: request, isLoading, error, refetch } = useGetRequestPembelianByIdQuery(requestId);
  const [deleteRequest] = useDeleteRequestPembelianMutation();

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
      hour: '2-digit',
      minute: '2-digit',
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

  const handleDelete = async () => {
    if (!request) return;

    const confirmed = await sweetAlert.showConfirm(
      'Hapus Request',
      'Apakah Anda yakin ingin menghapus request ini?'
    );

    if (confirmed) {
      try {
        Swal.fire({
          title: 'Menghapus...',
          text: 'Sedang menghapus request...',
          allowOutsideClick: false,
          allowEscapeKey: false,
          showConfirmButton: false,
          didOpen: () => {
            Swal.showLoading();
          },
        });

        await deleteRequest(requestId).unwrap();
        Swal.close();
        await sweetAlert.showSuccessAuto('Berhasil', 'Request berhasil dihapus');
        navigate('/request-pembelian/daftar-request');
      } catch (error: any) {
        Swal.close();
        await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menghapus request');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !request) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">{error ? 'Gagal memuat detail request' : 'Request tidak ditemukan'}</p>
          <div className="flex gap-2 justify-center">
            <Button variant="outline" onClick={() => navigate('/request-pembelian/daftar-request')}>
              Kembali
            </Button>
            <Button variant="primary" onClick={() => refetch()}>
              Coba Lagi
            </Button>
          </div>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">
              {request.title}
            </h1>
            <p className="text-gray-600">Reference: {request.reference_id}</p>
          </div>
          <div className="flex gap-2">
            {request.status === 'draft' && (
              <>
                <Link to={`/request-pembelian/edit-request/${request.id}`}>
                  <Button variant="outline">
                    ✏️ Edit
                  </Button>
                </Link>
                <Button
                  variant="danger"
                  onClick={handleDelete}
                >
                  🗑️ Delete
                </Button>
              </>
            )}
            <Link to="/request-pembelian/daftar-request">
              <Button variant="outline">
                ← Kembali
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📊</div>
            <div>
              <h3 className="text-sm text-gray-600 mb-1">Status</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                {request.status}
              </span>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">⚡</div>
            <div>
              <h3 className="text-sm text-gray-600 mb-1">Priority</h3>
              <p className="text-sm font-medium text-gray-800 capitalize">{request.priority}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">💰</div>
            <div>
              <h3 className="text-sm text-gray-600 mb-1">Total Budget</h3>
              <p className="text-sm font-medium text-gray-800">{formatCurrency(request.total_budget || 0)}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📦</div>
            <div>
              <h3 className="text-sm text-gray-600 mb-1">Items</h3>
              <p className="text-sm font-medium text-gray-800">{request.items_count || 0} items</p>
            </div>
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Informasi Request</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Description</label>
              <p className="text-sm text-gray-800">{request.description || '-'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Request Date</label>
              <p className="text-sm text-gray-800">{formatDate(request.request_date)}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Required Date</label>
              <p className="text-sm text-gray-800">{request.required_date ? formatDate(request.required_date) : '-'}</p>
            </div>
            {request.notes && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Notes</label>
                <p className="text-sm text-gray-800">{request.notes}</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Timeline</h2>
          <div className="space-y-3">
            {request.vendor_upload_deadline && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Vendor Upload Deadline</label>
                <p className="text-sm text-gray-800">{formatDate(request.vendor_upload_deadline)}</p>
              </div>
            )}
            {request.analysis_deadline && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Analysis Deadline</label>
                <p className="text-sm text-gray-800">{formatDate(request.analysis_deadline)}</p>
              </div>
            )}
            {request.approval_deadline && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Approval Deadline</label>
                <p className="text-sm text-gray-800">{formatDate(request.approval_deadline)}</p>
              </div>
            )}
            {request.is_overdue && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm font-medium text-red-800">⚠️ Request Overdue</p>
              </div>
            )}
            {request.days_remaining !== undefined && request.days_remaining > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Days Remaining</label>
                <p className="text-sm font-medium text-gray-800">{request.days_remaining} days</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Vendor Penawarans */}
      {request.vendor_penawarans_count > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Vendor Penawarans</h2>
            <Link to={`/request-pembelian/analisis-vendor/${request.id}`}>
              <Button variant="outline" size="sm">
                Lihat Analisis
              </Button>
            </Link>
          </div>
          <p className="text-sm text-gray-600">{request.vendor_penawarans_count} penawaran diterima</p>
        </div>
      )}
    </div>
  );
};

export default RequestPembelianDetailPage;

