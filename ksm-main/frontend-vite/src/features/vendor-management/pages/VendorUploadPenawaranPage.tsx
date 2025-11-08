/**
 * Vendor Upload Penawaran Page
 * Halaman untuk vendor upload penawaran dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useGetVendorRequestDetailQuery, useGetExistingPenawaranQuery, useUploadPenawaranMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, NumberInput } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import Swal from 'sweetalert2';

const VendorUploadPenawaranPage: React.FC = () => {
  const navigate = useNavigate();
  const { requestId } = useParams<{ requestId: string }>();
  const requestIdNum = requestId ? parseInt(requestId) : 0;
  const sweetAlert = useSweetAlert();

  const { data: request, isLoading: loadingRequest } = useGetVendorRequestDetailQuery(requestIdNum);
  const { data: existingPenawaran } = useGetExistingPenawaranQuery(requestIdNum);
  const [uploadPenawaran, { isLoading: submitting }] = useUploadPenawaranMutation();

  const [penawaranItems, setPenawaranItems] = useState<any[]>([]);
  const [penawaranData, setPenawaranData] = useState({
    total_quoted_price: 0,
    delivery_time_days: 0,
    payment_terms: '',
    quality_rating: 3,
    notes: ''
  });
  const [files, setFiles] = useState<File[]>([]);

  useEffect(() => {
    if (request?.items) {
      const initialItems = request.items.map((item: any) => ({
        request_item_id: item.id,
        quantity: item.quantity,
        harga_satuan: 0,
        harga_total: 0,
        spesifikasi: item.specifications || '',
        notes: item.notes || '',
        merk: ''
      }));
      setPenawaranItems(initialItems);
    }
  }, [request]);

  useEffect(() => {
    if (existingPenawaran) {
      setPenawaranData({
        total_quoted_price: existingPenawaran.total_quoted_price || 0,
        delivery_time_days: existingPenawaran.delivery_time_days || 0,
        payment_terms: existingPenawaran.payment_terms || '',
        quality_rating: existingPenawaran.quality_rating || 3,
        notes: existingPenawaran.notes || ''
      });
      if (existingPenawaran.items) {
        setPenawaranItems(existingPenawaran.items);
      }
    }
  }, [existingPenawaran]);

  const handleItemChange = (index: number, field: string, value: any) => {
    const updated = [...penawaranItems];
    // Convert value to number if it's a number field
    const numValue = (field === 'harga_satuan' || field === 'quantity') 
      ? (typeof value === 'number' ? value : (field === 'harga_satuan' ? parseFloat(String(value)) : parseInt(String(value), 10)))
      : value;
    updated[index] = { ...updated[index], [field]: numValue };
    
    if (field === 'harga_satuan' || field === 'quantity') {
      const hargaSatuan = field === 'harga_satuan' ? (typeof numValue === 'number' ? numValue : parseFloat(String(numValue)) || 0) : updated[index].harga_satuan;
      const quantity = field === 'quantity' ? (typeof numValue === 'number' ? numValue : parseInt(String(numValue), 10) || 0) : updated[index].quantity;
      updated[index].harga_total = hargaSatuan * quantity;
    }
    
    setPenawaranItems(updated);
    
    // Recalculate total
    const total = updated.reduce((sum, item) => sum + (item.harga_total || 0), 0);
    setPenawaranData(prev => ({ ...prev, total_quoted_price: total }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    Swal.fire({
      title: 'Mengirim...',
      text: 'Sedang mengirim penawaran...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });

    try {
      const formData = new FormData();
      formData.append('request_id', requestIdNum.toString());
      formData.append('items', JSON.stringify(penawaranItems));
      formData.append('total_quoted_price', penawaranData.total_quoted_price.toString());
      formData.append('delivery_time_days', penawaranData.delivery_time_days.toString());
      formData.append('payment_terms', penawaranData.payment_terms);
      formData.append('quality_rating', penawaranData.quality_rating.toString());
      formData.append('notes', penawaranData.notes);

      files.forEach((file, index) => {
        formData.append(`files[${index}]`, file);
      });

      await uploadPenawaran({ requestId: requestIdNum, data: formData }).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Penawaran berhasil dikirim');
      navigate('/vendor/requests');
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal mengirim penawaran');
    }
  };

  if (loadingRequest) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!request) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">Request Tidak Ditemukan</h3>
          <Button variant="primary" onClick={() => navigate('/vendor/requests')}>
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
            <p className="text-gray-600">#{request.reference_id} - {request.title}</p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate(`/vendor/requests/${requestId}`)}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Items */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Items Penawaran</h2>
          <div className="space-y-4">
            {penawaranItems.map((item, index) => {
              const requestItem = request.items?.find((ri: any) => ri.id === item.request_item_id);
              return (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-800 mb-3">
                    {requestItem?.nama_barang || `Item ${index + 1}`}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
                      <NumberInput
                        value={item.quantity}
                        onChange={(value) => handleItemChange(index, 'quantity', value)}
                        required
                        min="1"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Harga Satuan</label>
                      <NumberInput
                        value={item.harga_satuan}
                        onChange={(value) => handleItemChange(index, 'harga_satuan', value)}
                        required
                        min="0"
                        step="0.01"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Harga Total</label>
                      <NumberInput
                        value={item.harga_total}
                        disabled
                        className="bg-gray-100"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Spesifikasi</label>
                      <Input
                        value={item.spesifikasi}
                        onChange={(e) => handleItemChange(index, 'spesifikasi', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Merk</label>
                      <Input
                        value={item.merk || ''}
                        onChange={(e) => handleItemChange(index, 'merk', e.target.value)}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Penawaran Data */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Informasi Penawaran</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Total Harga</label>
              <NumberInput
                value={penawaranData.total_quoted_price}
                disabled
                className="bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Waktu Pengiriman (Hari)</label>
              <NumberInput
                value={penawaranData.delivery_time_days}
                onChange={(value) => setPenawaranData(prev => ({ ...prev, delivery_time_days: typeof value === 'number' ? value : parseInt(String(value), 10) || 0 }))}
                required
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Syarat Pembayaran</label>
              <Input
                value={penawaranData.payment_terms}
                onChange={(e) => setPenawaranData(prev => ({ ...prev, payment_terms: e.target.value }))}
                placeholder="Contoh: DP 30%, Pelunasan 70%"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Rating Kualitas (1-5)</label>
              <Input
                type="number"
                value={penawaranData.quality_rating}
                onChange={(e) => setPenawaranData(prev => ({ ...prev, quality_rating: parseInt(e.target.value) || 3 }))}
                min="1"
                max="5"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Catatan</label>
              <textarea
                value={penawaranData.notes}
                onChange={(e) => setPenawaranData(prev => ({ ...prev, notes: e.target.value }))}
                rows={3}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
              />
            </div>
          </div>
        </div>

        {/* File Upload */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Upload Dokumen</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">File Penawaran</label>
            <input
              type="file"
              multiple
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
            {files.length > 0 && (
              <p className="mt-2 text-sm text-gray-600">{files.length} file dipilih</p>
            )}
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate(`/vendor/requests/${requestId}`)}
            disabled={submitting}
          >
            Batal
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={submitting}
          >
            Kirim Penawaran
          </Button>
        </div>
      </form>
    </div>
  );
};

export default VendorUploadPenawaranPage;

