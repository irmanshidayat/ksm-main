/**
 * Barang Masuk Page
 * Halaman untuk menambahkan barang masuk ke gudang
 */

import React, { useState, ChangeEvent, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBarangList } from '../hooks';
import { useCreateBarangMasukMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { Textarea } from '@/shared/components/ui/Form';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { BarangMasukForm } from '../types';
import Swal from 'sweetalert2';

const BarangMasukPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const { barangList, supplierList, loading: loadingData } = useBarangList();
  const [createBarangMasuk, { isLoading }] = useCreateBarangMasukMutation();

  const [formData, setFormData] = useState<BarangMasukForm>({
    barang_id: 0,
    supplier_id: null,
    jumlah_masuk: 0,
    harga_per_unit: null,
    tanggal_masuk: new Date().toISOString().split('T')[0],
    nomor_surat_jalan: '',
    keterangan: ''
  });

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'jumlah_masuk' || name === 'harga_per_unit' ? parseFloat(value) || 0 : 
              name === 'barang_id' || name === 'supplier_id' ? (value === '' ? (name === 'supplier_id' ? null : 0) : parseInt(value)) :
              value
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (formData.barang_id === 0) {
      await sweetAlert.showError('Validasi Error', 'Pilih barang terlebih dahulu');
      return;
    }

    if (formData.jumlah_masuk <= 0) {
      await sweetAlert.showError('Validasi Error', 'Jumlah masuk harus lebih dari 0');
      return;
    }

    Swal.fire({
      title: 'Memproses...',
      text: 'Sedang menambahkan barang masuk...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });

    try {
      const result = await createBarangMasuk(formData).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Barang masuk berhasil ditambahkan!');
      
      // Reset form
      setFormData({
        barang_id: 0,
        supplier_id: null,
        jumlah_masuk: 0,
        harga_per_unit: null,
        tanggal_masuk: new Date().toISOString().split('T')[0],
        nomor_surat_jalan: '',
        keterangan: ''
      });
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menambahkan barang masuk');
    }
  };

  const calculateTotal = () => {
    return formData.jumlah_masuk * (formData.harga_per_unit || 0);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR'
    }).format(amount);
  };

  if (loadingData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📥 Barang Masuk</h1>
        <p className="text-gray-600">Tambahkan barang baru yang masuk ke gudang</p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Barang */}
            <div>
              <label htmlFor="barang_id" className="block text-sm font-medium text-gray-700 mb-2">
                Barang *
              </label>
              <select
                id="barang_id"
                name="barang_id"
                value={formData.barang_id}
                onChange={handleInputChange}
                required
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Pilih Barang</option>
                {Array.isArray(barangList) && barangList.map((barang) => (
                  <option key={barang.id} value={barang.id}>
                    {barang.kode_barang} - {barang.nama_barang}
                  </option>
                ))}
              </select>
            </div>

            {/* Supplier */}
            <div>
              <label htmlFor="supplier_id" className="block text-sm font-medium text-gray-700 mb-2">
                Supplier
              </label>
              <select
                id="supplier_id"
                name="supplier_id"
                value={formData.supplier_id || ''}
                onChange={handleInputChange}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Pilih Supplier</option>
                {Array.isArray(supplierList) && supplierList.map((supplier) => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.nama_supplier}
                  </option>
                ))}
              </select>
            </div>

            {/* Jumlah Masuk */}
            <div>
              <label htmlFor="jumlah_masuk" className="block text-sm font-medium text-gray-700 mb-2">
                Jumlah Masuk *
              </label>
              <Input
                type="number"
                id="jumlah_masuk"
                name="jumlah_masuk"
                value={formData.jumlah_masuk}
                onChange={handleInputChange}
                min="1"
                required
                className="w-full"
              />
            </div>

            {/* Harga Satuan */}
            <div>
              <label htmlFor="harga_per_unit" className="block text-sm font-medium text-gray-700 mb-2">
                Harga Satuan (Rp)
              </label>
              <Input
                type="number"
                id="harga_per_unit"
                name="harga_per_unit"
                value={formData.harga_per_unit || ''}
                onChange={handleInputChange}
                min="0"
                step="1000"
                className="w-full"
              />
            </div>

            {/* Tanggal Masuk */}
            <div>
              <label htmlFor="tanggal_masuk" className="block text-sm font-medium text-gray-700 mb-2">
                Tanggal Masuk *
              </label>
              <Input
                type="date"
                id="tanggal_masuk"
                name="tanggal_masuk"
                value={formData.tanggal_masuk}
                onChange={handleInputChange}
                required
                className="w-full"
              />
            </div>

            {/* Nomor Surat Jalan */}
            <div>
              <label htmlFor="nomor_surat_jalan" className="block text-sm font-medium text-gray-700 mb-2">
                Nomor Surat Jalan
              </label>
              <Input
                type="text"
                id="nomor_surat_jalan"
                name="nomor_surat_jalan"
                value={formData.nomor_surat_jalan}
                onChange={handleInputChange}
                className="w-full"
                placeholder="Masukkan nomor surat jalan"
              />
            </div>
          </div>

          {/* Keterangan */}
          <div>
            <label htmlFor="keterangan" className="block text-sm font-medium text-gray-700 mb-2">
              Keterangan
            </label>
            <textarea
              id="keterangan"
              name="keterangan"
              value={formData.keterangan}
              onChange={handleInputChange}
              rows={3}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-vertical"
              placeholder="Masukkan keterangan tambahan (opsional)"
            />
          </div>

          {/* Total */}
          {formData.harga_per_unit && formData.harga_per_unit > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">Total Nilai:</span>
                <span className="text-lg font-bold text-blue-600">
                  {formatCurrency(calculateTotal())}
                </span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t">
            <Button
              type="submit"
              variant="primary"
              isLoading={isLoading}
              className="flex-1"
            >
              Simpan Barang Masuk
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/stok-barang')}
              className="flex-1"
            >
              Batal
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BarangMasukPage;

