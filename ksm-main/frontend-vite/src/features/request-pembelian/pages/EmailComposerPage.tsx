/**
 * Email Composer Page
 * Halaman untuk compose dan kirim email ke vendor dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useGetVendorByIdQuery } from '@/features/vendor-management';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import Swal from 'sweetalert2';

interface ItemData {
  id?: number;
  nama_barang: string;
  spesifikasi: string;
  quantity: number;
  satuan: string;
  harga_satuan?: number;
}

const EmailComposerPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const sweetAlert = useSweetAlert();

  // Get vendor ID from location state or URL params
  const vendorIdFromState = (location.state as any)?.vendorId;
  const urlParams = new URLSearchParams(location.search);
  const vendorIdFromUrl = urlParams.get('vendorId');
  const vendorId = vendorIdFromState || (vendorIdFromUrl ? parseInt(vendorIdFromUrl) : 0);

  const { data: vendor, isLoading: loadingVendor } = useGetVendorByIdQuery(vendorId, { skip: !vendorId });

  const [emailData, setEmailData] = useState({
    subject: '',
    to: '',
    cc: '',
    bcc: '',
    message: '',
  });

  const [items, setItems] = useState<ItemData[]>((location.state as any)?.items || []);
  const [sending, setSending] = useState(false);

  React.useEffect(() => {
    if (vendor) {
      setEmailData(prev => ({
        ...prev,
        to: vendor.email || '',
        subject: `Request Penawaran - ${vendor.company_name || 'Vendor'}`,
        message: generateDefaultMessage(vendor.company_name || 'Vendor', items),
      }));
    }
  }, [vendor, items]);

  const generateDefaultMessage = (vendorName: string, itemsList: ItemData[]) => {
    const itemsListText = itemsList.map((item, index) => 
      `${index + 1}. ${item.nama_barang} - Qty: ${item.quantity} ${item.satuan}${item.spesifikasi ? `\n   Spesifikasi: ${item.spesifikasi}` : ''}`
    ).join('\n');

    return `Kepada Yth. ${vendorName},

Dengan hormat,

Kami bermaksud untuk meminta penawaran harga untuk item-item berikut:

${itemsListText}

Mohon kirimkan penawaran harga terbaik untuk item-item di atas.

Terima kasih atas perhatiannya.

Hormat kami,
Tim Procurement`;
  };

  const handleSendEmail = async () => {
    if (!emailData.to || !emailData.subject || !emailData.message) {
      await sweetAlert.showError('Error', 'To, Subject, dan Message harus diisi');
      return;
    }

    try {
      setSending(true);
      Swal.fire({
        title: 'Mengirim Email...',
        text: 'Sedang mengirim email ke vendor...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const token = localStorage.getItem('KSM_access_token');
      const response = await fetch(`${import.meta.env.VITE_APP_API_URL || 'http://localhost:8000'}/api/email/send-vendor-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          to: emailData.to,
          cc: emailData.cc ? emailData.cc.split(',').map(e => e.trim()) : [],
          bcc: emailData.bcc ? emailData.bcc.split(',').map(e => e.trim()) : [],
          subject: emailData.subject,
          message: emailData.message,
          vendor_id: vendorId,
          items: items,
        }),
      });

      const data = await response.json();
      Swal.close();

      if (data.success) {
        await sweetAlert.showSuccessAuto('Berhasil', 'Email berhasil dikirim');
        navigate('/request-pembelian/daftar-barang-vendor');
      } else {
        await sweetAlert.showError('Gagal', data.message || 'Gagal mengirim email');
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Kesalahan', error?.message || 'Terjadi kesalahan saat mengirim email');
    } finally {
      setSending(false);
    }
  };

  if (loadingVendor) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!vendor && vendorId) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Vendor tidak ditemukan</p>
          <Button variant="primary" onClick={() => navigate('/request-pembelian/daftar-barang-vendor')}>
            Kembali
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Email Composer</h1>
            <p className="text-gray-600">
              {vendor ? `Kirim email ke: ${vendor.company_name}` : 'Compose email untuk vendor'}
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/request-pembelian/daftar-barang-vendor')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Email Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Email Fields */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Email Details</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">To *</label>
                <Input
                  type="email"
                  value={emailData.to}
                  onChange={(e) => setEmailData(prev => ({ ...prev, to: e.target.value }))}
                  required
                  placeholder="vendor@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">CC</label>
                <Input
                  type="text"
                  value={emailData.cc}
                  onChange={(e) => setEmailData(prev => ({ ...prev, cc: e.target.value }))}
                  placeholder="email1@example.com, email2@example.com"
                />
                <p className="text-xs text-gray-500 mt-1">Pisahkan dengan koma untuk multiple emails</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">BCC</label>
                <Input
                  type="text"
                  value={emailData.bcc}
                  onChange={(e) => setEmailData(prev => ({ ...prev, bcc: e.target.value }))}
                  placeholder="email1@example.com, email2@example.com"
                />
                <p className="text-xs text-gray-500 mt-1">Pisahkan dengan koma untuk multiple emails</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Subject *</label>
                <Input
                  type="text"
                  value={emailData.subject}
                  onChange={(e) => setEmailData(prev => ({ ...prev, subject: e.target.value }))}
                  required
                  placeholder="Subject email"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Message *</label>
                <textarea
                  value={emailData.message}
                  onChange={(e) => setEmailData(prev => ({ ...prev, message: e.target.value }))}
                  rows={12}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                  required
                  placeholder="Tulis pesan email..."
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-end gap-4">
              <Button
                variant="outline"
                onClick={() => navigate('/request-pembelian/daftar-barang-vendor')}
                disabled={sending}
              >
                Batal
              </Button>
              <Button
                variant="primary"
                onClick={handleSendEmail}
                isLoading={sending}
              >
                📧 Kirim Email
              </Button>
            </div>
          </div>
        </div>

        {/* Items Sidebar */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Items</h2>
            {items.length > 0 ? (
              <div className="space-y-3">
                {items.map((item, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <h3 className="font-medium text-gray-800 mb-1">{item.nama_barang}</h3>
                    <p className="text-sm text-gray-600">
                      Qty: {item.quantity} {item.satuan}
                    </p>
                    {item.spesifikasi && (
                      <p className="text-xs text-gray-500 mt-1">{item.spesifikasi}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-4">Tidak ada items</p>
            )}
          </div>

          {/* Vendor Info */}
          {vendor && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Vendor Info</h2>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Company:</span>
                  <p className="text-gray-800">{vendor.company_name}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Email:</span>
                  <p className="text-gray-800">{vendor.email}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Contact:</span>
                  <p className="text-gray-800">{vendor.contact_person}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmailComposerPage;

