/**
 * Tambah Kategori Page
 * Halaman untuk menambahkan kategori baru
 */

import React, { useState, ChangeEvent, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateKategoriMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import type { TambahKategoriForm } from '../types';
import Swal from 'sweetalert2';

const TambahKategoriPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [createKategori, { isLoading }] = useCreateKategoriMutation();

  const [formData, setFormData] = useState<TambahKategoriForm>({
    kode_kategori: '',
    nama_kategori: '',
    deskripsi: ''
  });

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!formData.kode_kategori.trim()) {
      await sweetAlert.showError('Validasi Error', 'Kode kategori harus diisi');
      return;
    }

    if (!formData.nama_kategori.trim()) {
      await sweetAlert.showError('Validasi Error', 'Nama kategori harus diisi');
      return;
    }

    if (formData.kode_kategori.length < 2) {
      await sweetAlert.showError('Validasi Error', 'Kode kategori minimal 2 karakter');
      return;
    }

    if (formData.nama_kategori.length < 3) {
      await sweetAlert.showError('Validasi Error', 'Nama kategori minimal 3 karakter');
      return;
    }

    Swal.fire({
      title: 'Memproses...',
      text: 'Sedang menambahkan kategori baru...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });

    try {
      await createKategori(formData).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Kategori baru berhasil ditambahkan! Kategori telah tersedia untuk digunakan.');
      
      // Reset form
      setFormData({
        kode_kategori: '',
        nama_kategori: '',
        deskripsi: ''
      });
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || error?.data?.detail || 'Gagal menambahkan kategori baru');
    }
  };

  return (
    <div className="p-4 md:p-6 lg:p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🏷️ Tambah Kategori</h1>
        <p className="text-gray-600">Tambahkan kategori baru untuk mengelompokkan barang</p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Kode Kategori */}
            <div>
              <label htmlFor="kode_kategori" className="block text-sm font-medium text-gray-700 mb-2">
                Kode Kategori *
              </label>
              <Input
                type="text"
                id="kode_kategori"
                name="kode_kategori"
                value={formData.kode_kategori}
                onChange={handleInputChange}
                required
                className="w-full"
                placeholder="Contoh: ELK, MKN, PKS"
                maxLength={10}
              />
              <small className="text-xs text-gray-500 mt-1 block">
                Maksimal 10 karakter, gunakan singkatan yang mudah diingat
              </small>
            </div>

            {/* Nama Kategori */}
            <div>
              <label htmlFor="nama_kategori" className="block text-sm font-medium text-gray-700 mb-2">
                Nama Kategori *
              </label>
              <Input
                type="text"
                id="nama_kategori"
                name="nama_kategori"
                value={formData.nama_kategori}
                onChange={handleInputChange}
                required
                className="w-full"
                placeholder="Contoh: Elektronik, Makanan, Pakaian"
                maxLength={50}
              />
              <small className="text-xs text-gray-500 mt-1 block">
                Nama lengkap kategori yang mudah dipahami
              </small>
            </div>
          </div>

          {/* Deskripsi */}
          <div>
            <label htmlFor="deskripsi" className="block text-sm font-medium text-gray-700 mb-2">
              Deskripsi
            </label>
            <textarea
              id="deskripsi"
              name="deskripsi"
              value={formData.deskripsi}
              onChange={handleInputChange}
              rows={4}
              maxLength={200}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-vertical"
              placeholder="Tambahkan deskripsi detail tentang kategori ini (opsional)"
            />
            <small className="text-xs text-gray-500 mt-1 block">Maksimal 200 karakter</small>
          </div>

          {/* Preview Kategori */}
          {(formData.kode_kategori || formData.nama_kategori || formData.deskripsi) && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">👁️ Preview Kategori</h3>
              <div className="space-y-2">
                <div className="flex items-center">
                  <span className="text-sm font-medium text-gray-600 w-24">Kode:</span>
                  <span className="text-gray-800">{formData.kode_kategori || 'KODE'}</span>
                </div>
                <div className="flex items-center">
                  <span className="text-sm font-medium text-gray-600 w-24">Nama:</span>
                  <span className="text-gray-800">{formData.nama_kategori || 'NAMA KATEGORI'}</span>
                </div>
                <div className="flex items-start">
                  <span className="text-sm font-medium text-gray-600 w-24">Deskripsi:</span>
                  <span className="text-gray-800">{formData.deskripsi || 'Deskripsi kategori akan muncul di sini...'}</span>
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
              Tambah Kategori
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setFormData({
                  kode_kategori: '',
                  nama_kategori: '',
                  deskripsi: ''
                });
              }}
              className="flex-1"
            >
              Reset Form
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
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">ℹ️ Informasi Penting</h3>
        <ul className="space-y-1 text-sm text-gray-700">
          <li>✅ Kode kategori harus unik dan tidak boleh duplikat</li>
          <li>📊 Kategori akan digunakan untuk mengelompokkan barang</li>
          <li>🔍 Kategori dapat dikelola melalui menu pengaturan</li>
          <li>⚠️ Pastikan kode dan nama kategori mudah diingat</li>
        </ul>
      </div>

      {/* Tips Panel */}
      <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">💡 Tips Membuat Kategori</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">🎯 Gunakan Singkatan</h4>
            <p className="text-sm text-gray-600">Contoh: ELK untuk Elektronik, MKN untuk Makanan</p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">📝 Nama yang Jelas</h4>
            <p className="text-sm text-gray-600">Gunakan nama yang mudah dipahami semua pengguna</p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">🔤 Konsisten</h4>
            <p className="text-sm text-gray-600">Gunakan format yang konsisten untuk semua kategori</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TambahKategoriPage;

