/**
 * Vendor Penawaran Upload Page
 * Halaman untuk upload penawaran vendor dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetRequestPembelianByIdQuery } from '../store';
import { useGetVendorByIdQuery } from '@/features/vendor-management';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, NumberInput } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import Swal from 'sweetalert2';

const VendorPenawaranUploadPage: React.FC = () => {
  const { vendorId, requestId } = useParams<{ vendorId: string; requestId: string }>();
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const vendorIdNum = vendorId ? parseInt(vendorId) : 0;
  const requestIdNum = requestId ? parseInt(requestId) : 0;

  const { data: vendor, isLoading: loadingVendor } = useGetVendorByIdQuery(vendorIdNum, { skip: !vendorIdNum });
  const { data: request, isLoading: loadingRequest } = useGetRequestPembelianByIdQuery(requestIdNum, { skip: !requestIdNum });

  const [penawaranData, setPenawaranData] = useState({
    total_quoted_price: 0,
    delivery_time_days: 0,
    payment_terms: '',
    quality_rating: 3,
    notes: '',
  });

  const [items, setItems] = useState<Array<{
    nama_barang: string;
    quantity: number;
    harga_satuan: number;
    spesifikasi: string;
  }>>([]);

  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  const addItem = () => {
    setItems(prev => [...prev, {
      nama_barang: '',
      quantity: 1,
      harga_satuan: 0,
      spesifikasi: '',
    }]);
  };

  const updateItem = (index: number, field: string, value: any) => {
    setItems(prev => prev.map((item, i) => 
      i === index ? { ...item, [field]: value } : item
    ));
  };

  const removeItem = (index: number) => {
    setItems(prev => prev.filter((_, i) => i !== index));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (items.length === 0) {
      await sweetAlert.showError('Error', 'Minimal harus ada 1 item');
      return;
    }

    try {
      setUploading(true);
      Swal.fire({
        title: 'Mengupload...',
        text: 'Sedang mengupload penawaran...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const formData = new FormData();
      formData.append('request_id', requestIdNum.toString());
      formData.append('total_quoted_price', penawaranData.total_quoted_price.toString());
      formData.append('delivery_time_days', penawaranData.delivery_time_days.toString());
      formData.append('payment_terms', penawaranData.payment_terms);
      formData.append('quality_rating', penawaranData.quality_rating.toString());
      formData.append('notes', penawaranData.notes);
      formData.append('items', JSON.stringify(items));

      files.forEach((file, index) => {
        formData.append(`files[${index}]`, file);
      });

      const token = localStorage.getItem('KSM_access_token');
      const response = await fetch(`${import.meta.env.VITE_APP_API_URL || 'http://localhost:8000'}/api/vendor/${vendorIdNum}/penawaran/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();

      Swal.close();

      if (data.success) {
        await sweetAlert.showSuccessAuto('Berhasil', 'Penawaran berhasil diupload');
        navigate(`/request-pembelian/detail/${requestIdNum}`);
      } else {
        await sweetAlert.showError('Gagal', data.message || 'Gagal mengupload penawaran');
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Kesalahan', error?.message || 'Terjadi kesalahan saat mengupload');
    } finally {
      setUploading(false);
    }
  };

  if (loadingVendor || loadingRequest) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!vendor || !request) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Vendor atau Request tidak ditemukan</p>
          <Button variant="primary" onClick={() => navigate('/request-pembelian/upload-penawaran')}>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Upload Penawaran</h1>
            <p className="text-gray-600">
              Vendor: {vendor.company_name} | Request: {request.title}
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/request-pembelian/upload-penawaran')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Penawaran Info */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Informasi Penawaran</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Total Quoted Price</label>
              <NumberInput
                value={penawaranData.total_quoted_price}
                onChange={(value) => setPenawaranData(prev => ({ ...prev, total_quoted_price: typeof value === 'number' ? value : parseFloat(String(value)) || 0 }))}
                min="0"
                step="0.01"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Delivery Time (days)</label>
              <NumberInput
                value={penawaranData.delivery_time_days}
                onChange={(value) => setPenawaranData(prev => ({ ...prev, delivery_time_days: typeof value === 'number' ? value : parseInt(String(value), 10) || 0 }))}
                min="0"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Payment Terms</label>
              <Input
                type="text"
                value={penawaranData.payment_terms}
                onChange={(e) => setPenawaranData(prev => ({ ...prev, payment_terms: e.target.value }))}
                placeholder="e.g., Net 30, COD, etc."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Quality Rating</label>
              <select
                value={penawaranData.quality_rating}
                onChange={(e) => setPenawaranData(prev => ({ ...prev, quality_rating: parseInt(e.target.value) }))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value={1}>1 - Poor</option>
                <option value={2}>2 - Fair</option>
                <option value={3}>3 - Good</option>
                <option value={4}>4 - Very Good</option>
                <option value={5}>5 - Excellent</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
              <textarea
                value={penawaranData.notes}
                onChange={(e) => setPenawaranData(prev => ({ ...prev, notes: e.target.value }))}
                rows={3}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                placeholder="Tambahkan catatan..."
              />
            </div>
          </div>
        </div>

        {/* Items */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Items</h2>
            <Button
              type="button"
              variant="outline"
              onClick={addItem}
            >
              ➕ Tambah Item
            </Button>
          </div>

          {items.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>Belum ada item. Klik "Tambah Item" untuk menambahkan.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {items.map((item, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="font-medium text-gray-800">Item #{index + 1}</h3>
                    <Button
                      type="button"
                      variant="danger"
                      size="sm"
                      onClick={() => removeItem(index)}
                    >
                      🗑️ Hapus
                    </Button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Nama Barang</label>
                      <Input
                        type="text"
                        value={item.nama_barang}
                        onChange={(e) => updateItem(index, 'nama_barang', e.target.value)}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
                      <NumberInput
                        value={item.quantity}
                        onChange={(value) => updateItem(index, 'quantity', typeof value === 'number' ? value : parseInt(String(value), 10) || 1)}
                        min="1"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Harga Satuan</label>
                      <NumberInput
                        value={item.harga_satuan}
                        onChange={(value) => updateItem(index, 'harga_satuan', typeof value === 'number' ? value : parseFloat(String(value)) || 0)}
                        min="0"
                        step="0.01"
                        required
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Spesifikasi</label>
                      <textarea
                        value={item.spesifikasi}
                        onChange={(e) => updateItem(index, 'spesifikasi', e.target.value)}
                        rows={2}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Files */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Upload Files</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Pilih Files</label>
            <Input
              type="file"
              multiple
              onChange={handleFileChange}
              className="w-full"
            />
            {files.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">Files yang dipilih:</p>
                <ul className="list-disc list-inside text-sm text-gray-700">
                  {files.map((file, index) => (
                    <li key={index}>{file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-end gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/request-pembelian/upload-penawaran')}
              disabled={uploading}
            >
              Batal
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={uploading}
            >
              Upload Penawaran
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default VendorPenawaranUploadPage;

