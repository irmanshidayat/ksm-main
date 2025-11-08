/**
 * Barang Keluar Page
 * Halaman untuk mengurangi stok barang dari inventory
 */

import React, { useState, ChangeEvent, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBarangList } from '../hooks';
import { useCreateBarangKeluarMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { BarangKeluarForm, Barang } from '../types';
import Swal from 'sweetalert2';

const BarangKeluarPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const { barangList, refetch, loading: loadingData } = useBarangList();
  const [createBarangKeluar, { isLoading }] = useCreateBarangKeluarMutation();

  const [formData, setFormData] = useState<BarangKeluarForm>({
    barang_id: 0,
    jumlah_keluar: 0,
    tanggal_keluar: new Date().toISOString().split('T')[0],
    nomor_surat_jalan: '',
    keterangan: '',
    tujuan: ''
  });

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'barang_id' ? (value === '' ? 0 : parseInt(value)) :
              name === 'jumlah_keluar' ? (value === '' ? 0 : parseInt(value)) :
              value
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (formData.barang_id === 0) {
      await sweetAlert.showError('Validasi Error', 'Pilih barang terlebih dahulu');
      return;
    }

    if (formData.jumlah_keluar <= 0) {
      await sweetAlert.showError('Validasi Error', 'Jumlah keluar harus lebih dari 0');
      return;
    }

    const selectedBarang = barangList.find((b: Barang) => b.id === formData.barang_id);
    if (selectedBarang && formData.jumlah_keluar > selectedBarang.stok.jumlah_stok) {
      await sweetAlert.showError(
        'Stok Tidak Mencukupi',
        `Stok tersedia: ${selectedBarang.stok.jumlah_stok} ${selectedBarang.satuan}`
      );
      return;
    }

    if (!formData.tujuan.trim()) {
      await sweetAlert.showError('Validasi Error', 'Tujuan harus diisi');
      return;
    }

    Swal.fire({
      title: 'Memproses...',
      text: 'Sedang menambahkan barang keluar...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });

    try {
      await createBarangKeluar(formData).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Barang keluar berhasil ditambahkan! Stok telah diupdate otomatis.');
      
      // Reset form
      setFormData({
        barang_id: 0,
        jumlah_keluar: 0,
        tanggal_keluar: new Date().toISOString().split('T')[0],
        nomor_surat_jalan: '',
        keterangan: '',
        tujuan: ''
      });
      
      // Refresh barang list
      refetch();
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menambahkan barang keluar');
    }
  };

  const selectedBarang = barangList.find((b: Barang) => b.id === formData.barang_id);

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
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📤 Barang Keluar</h1>
        <p className="text-gray-600">Kurangi stok barang dari inventory dan catat barang keluar</p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
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
                value={formData.barang_id || ''}
                onChange={handleInputChange}
                required
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Pilih Barang</option>
                {Array.isArray(barangList) && barangList.map((barang: Barang) => (
                  <option key={barang.id} value={barang.id}>
                    {barang.kode_barang} - {barang.nama_barang} (Stok: {barang.stok.jumlah_stok} {barang.satuan})
                  </option>
                ))}
              </select>
            </div>

            {/* Jumlah Keluar */}
            <div>
              <label htmlFor="jumlah_keluar" className="block text-sm font-medium text-gray-700 mb-2">
                Jumlah Keluar *
              </label>
              <Input
                type="number"
                id="jumlah_keluar"
                name="jumlah_keluar"
                value={formData.jumlah_keluar || ''}
                onChange={handleInputChange}
                min="1"
                required
                className="w-full"
                placeholder="Masukkan jumlah barang keluar"
              />
            </div>

            {/* Tanggal Keluar */}
            <div>
              <label htmlFor="tanggal_keluar" className="block text-sm font-medium text-gray-700 mb-2">
                Tanggal Keluar *
              </label>
              <Input
                type="date"
                id="tanggal_keluar"
                name="tanggal_keluar"
                value={formData.tanggal_keluar}
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
                placeholder="Masukkan nomor surat jalan (opsional)"
              />
            </div>

            {/* Tujuan */}
            <div className="md:col-span-2">
              <label htmlFor="tujuan" className="block text-sm font-medium text-gray-700 mb-2">
                Tujuan *
              </label>
              <Input
                type="text"
                id="tujuan"
                name="tujuan"
                value={formData.tujuan}
                onChange={handleInputChange}
                required
                className="w-full"
                placeholder="Masukkan tujuan barang keluar"
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
              placeholder="Tambahkan keterangan tambahan (opsional)"
            />
          </div>

          {/* Info Barang */}
          {selectedBarang && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">📋 Informasi Barang</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <span className="text-sm text-gray-600">Kode Barang:</span>
                  <p className="font-medium text-gray-800">{selectedBarang.kode_barang}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Nama Barang:</span>
                  <p className="font-medium text-gray-800">{selectedBarang.nama_barang}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Kategori:</span>
                  <p className="font-medium text-gray-800">{selectedBarang.kategori?.nama_kategori || 'Tidak ada kategori'}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Stok Tersedia:</span>
                  <p className="font-medium text-gray-800">{selectedBarang.stok.jumlah_stok} {selectedBarang.satuan}</p>
                </div>
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
              Tambah Barang Keluar
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

      {/* Info Panel */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">ℹ️ Informasi Penting</h3>
        <ul className="space-y-1 text-sm text-gray-700">
          <li>✅ Stok akan berkurang otomatis setelah barang keluar ditambahkan</li>
          <li>📊 Data barang keluar akan tersimpan di database</li>
          <li>🔍 Barang keluar dapat dilihat di laporan stok</li>
          <li>⚠️ Pastikan stok mencukupi sebelum mengurangi</li>
        </ul>
      </div>
    </div>
  );
};

export default BarangKeluarPage;

