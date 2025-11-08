/**
 * Vendor Pesanan Detail Page
 * Halaman detail pesanan vendor dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useGetVendorOrderDetailQuery, useGetVendorOrderStatusHistoryQuery, useConfirmVendorOrderMutation, useUpdateVendorOrderStatusMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Modal } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import Swal from 'sweetalert2';

const VendorPesananDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { orderId } = useParams<{ orderId: string }>();
  const orderIdNum = orderId ? parseInt(orderId) : 0;
  const sweetAlert = useSweetAlert();

  const { data: orderDetail, isLoading, error, refetch } = useGetVendorOrderDetailQuery(orderIdNum);
  const { data: timeline = [] } = useGetVendorOrderStatusHistoryQuery(orderIdNum);
  const [confirmOrder, { isLoading: confirming }] = useConfirmVendorOrderMutation();
  const [updateStatus, { isLoading: updating }] = useUpdateVendorOrderStatusMutation();

  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [confirmNotes, setConfirmNotes] = useState('');
  const [statusForm, setStatusForm] = useState({
    status: 'confirmed',
    tracking_number: '',
    estimated_delivery_date: '',
    notes: ''
  });

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

  const handleConfirm = async () => {
    try {
      Swal.fire({
        title: 'Mengkonfirmasi...',
        text: 'Sedang mengkonfirmasi pesanan...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      await confirmOrder({ orderId: orderIdNum, data: { vendor_notes: confirmNotes } }).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Pesanan berhasil dikonfirmasi');
      setShowConfirmModal(false);
      setConfirmNotes('');
      refetch();
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal mengkonfirmasi pesanan');
    }
  };

  const handleUpdateStatus = async () => {
    try {
      Swal.fire({
        title: 'Memperbarui...',
        text: 'Sedang memperbarui status pesanan...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      await updateStatus({ orderId: orderIdNum, data: statusForm }).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Status pesanan berhasil diperbarui');
      setShowStatusModal(false);
      setStatusForm({
        status: 'confirmed',
        tracking_number: '',
        estimated_delivery_date: '',
        notes: ''
      });
      refetch();
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal memperbarui status');
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
          <p className="text-red-600 mb-4">Gagal memuat detail pesanan</p>
          <div className="flex gap-2 justify-center">
            <Button variant="outline" onClick={() => navigate('/vendor/pesanan')}>
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

  if (!orderDetail?.order) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">Pesanan Tidak Ditemukan</h3>
          <Button variant="primary" onClick={() => navigate('/vendor/pesanan')}>
            Kembali
          </Button>
        </div>
      </div>
    );
  }

  const order = orderDetail.order;

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">
              Pesanan #{order.order_reference || order.id}
            </h1>
            <p className="text-gray-600">Request: {order.request_reference || '-'}</p>
          </div>
          <div className="flex gap-2">
            {order.status === 'pending_confirmation' && (
              <Button
                variant="primary"
                onClick={() => setShowConfirmModal(true)}
                disabled={confirming}
              >
                ✅ Konfirmasi Pesanan
              </Button>
            )}
            {order.status !== 'pending_confirmation' && order.status !== 'cancelled' && (
              <Button
                variant="outline"
                onClick={() => setShowStatusModal(true)}
                disabled={updating}
              >
                📝 Update Status
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => navigate('/vendor/pesanan')}
            >
              ← Kembali
            </Button>
          </div>
        </div>
      </div>

      {/* Order Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Informasi Pesanan</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                {getStatusText(order.status)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total:</span>
              <span className="text-sm font-medium text-gray-800">{formatCurrency(order.total_amount || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Tanggal Pesanan:</span>
              <span className="text-sm text-gray-800">{formatDate(order.created_at)}</span>
            </div>
            {order.tracking_number && (
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">No. Resi:</span>
                <span className="text-sm font-medium text-gray-800">{order.tracking_number}</span>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Informasi Pengiriman</h3>
          <div className="space-y-3">
            {order.estimated_delivery_date && (
              <div>
                <span className="text-sm text-gray-600">Estimasi Pengiriman:</span>
                <p className="text-sm font-medium text-gray-800">{formatDate(order.estimated_delivery_date)}</p>
              </div>
            )}
            {order.delivery_address && (
              <div>
                <span className="text-sm text-gray-600">Alamat:</span>
                <p className="text-sm text-gray-800">{order.delivery_address}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Order Items */}
      {order.specifications && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Detail Items</h3>
          <div className="text-gray-700 whitespace-pre-wrap">{order.specifications}</div>
        </div>
      )}

      {/* Timeline */}
      {timeline.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Timeline</h3>
          <div className="space-y-4">
            {timeline.map((event: any, index: number) => (
              <div key={index} className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-primary-600 rounded-full mt-2"></div>
                  {index < timeline.length - 1 && (
                    <div className="w-0.5 h-full bg-gray-300 ml-1"></div>
                  )}
                </div>
                <div className="flex-1 pb-4">
                  <p className="text-sm font-medium text-gray-800">{event.status || event.event}</p>
                  <p className="text-xs text-gray-600">{formatDate(event.created_at || event.timestamp)}</p>
                  {event.notes && (
                    <p className="text-sm text-gray-600 mt-1">{event.notes}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confirm Modal */}
      <Modal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        title="Konfirmasi Pesanan"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-gray-700">Apakah Anda yakin ingin mengkonfirmasi pesanan ini?</p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Catatan (Opsional)</label>
            <textarea
              value={confirmNotes}
              onChange={(e) => setConfirmNotes(e.target.value)}
              rows={3}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
              placeholder="Tambahkan catatan untuk pesanan ini..."
            />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => setShowConfirmModal(false)}
              disabled={confirming}
            >
              Batal
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirm}
              isLoading={confirming}
            >
              Konfirmasi
            </Button>
          </div>
        </div>
      </Modal>

      {/* Status Update Modal */}
      <Modal
        isOpen={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        title="Update Status Pesanan"
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={statusForm.status}
              onChange={(e) => setStatusForm(prev => ({ ...prev, status: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="confirmed">Dikonfirmasi</option>
              <option value="in_progress">Sedang Diproses</option>
              <option value="shipped">Dikirim</option>
              <option value="delivered">Terkirim</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">No. Resi (Opsional)</label>
            <Input
              value={statusForm.tracking_number}
              onChange={(e) => setStatusForm(prev => ({ ...prev, tracking_number: e.target.value }))}
              placeholder="Masukkan nomor resi"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Estimasi Pengiriman (Opsional)</label>
            <Input
              type="date"
              value={statusForm.estimated_delivery_date}
              onChange={(e) => setStatusForm(prev => ({ ...prev, estimated_delivery_date: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Catatan (Opsional)</label>
            <textarea
              value={statusForm.notes}
              onChange={(e) => setStatusForm(prev => ({ ...prev, notes: e.target.value }))}
              rows={3}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
              placeholder="Tambahkan catatan..."
            />
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => setShowStatusModal(false)}
              disabled={updating}
            >
              Batal
            </Button>
            <Button
              variant="primary"
              onClick={handleUpdateStatus}
              isLoading={updating}
            >
              Update Status
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default VendorPesananDetailPage;

