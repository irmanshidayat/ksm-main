/**
 * Tambah Barang Page
 * Halaman untuk menambahkan barang baru ke inventory
 */

import React, { useState, useEffect, ChangeEvent, FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useGetKategoriQuery, useGetMerkListQuery, useCreateBarangMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { TambahBarangForm, Kategori } from '../types';
import Swal from 'sweetalert2';

const TambahBarangPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sweetAlert = useSweetAlert();
  const { data: kategoriList = [], isLoading: loadingKategori } = useGetKategoriQuery();
  const { data: merkList = [] } = useGetMerkListQuery();
  const [createBarang, { isLoading }] = useCreateBarangMutation();

  const [formData, setFormData] = useState<TambahBarangForm>({
    kode_barang: '',
    nama_barang: '',
    kategori_id: 0,
    satuan: '',
    stok_minimal: 0,
    harga_per_unit: 0,
    deskripsi: '',
    merk: ''
  });

  useEffect(() => {
    // Check for nama_barang parameter from URL
    const namaBarangParam = searchParams.get('nama_barang');
    if (namaBarangParam) {
      setFormData(prev => ({
        ...prev,
        nama_barang: decodeURIComponent(namaBarangParam)
      }));
    }
  }, [searchParams]);

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'kategori_id' ? (value === '' ? 0 : parseInt(value)) :
              name === 'stok_minimal' || name === 'harga_per_unit' ? (value === '' ? 0 : parseFloat(value)) :
              value
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!formData.kode_barang.trim()) {
      await sweetAlert.showError('Validasi Error', 'Kode barang harus diisi');
      return;
    }

    if (!formData.nama_barang.trim()) {
      await sweetAlert.showError('Validasi Error', 'Nama barang harus diisi');
      return;
    }

    if (formData.kategori_id === 0) {
      await sweetAlert.showError('Validasi Error', 'Pilih kategori terlebih dahulu');
      return;
    }

    if (!formData.satuan.trim()) {
      await sweetAlert.showError('Validasi Error', 'Satuan harus diisi');
      return;
    }

    if (formData.stok_minimal < 0) {
      await sweetAlert.showError('Validasi Error', 'Stok minimal tidak boleh negatif');
      return;
    }

    if (formData.harga_per_unit < 0) {
      await sweetAlert.showError('Validasi Error', 'Harga per unit tidak boleh negatif');
      return;
    }

    Swal.fire({
      title: 'Memproses...',
      text: 'Sedang menambahkan barang baru...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });

    try {
      const dataToSend = {
        ...formData,
        stok_minimum: formData.stok_minimal,
        jumlah_stok_awal: 0
      };
      
      await createBarang(dataToSend).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Barang baru berhasil ditambahkan! Barang telah tersedia di inventory.');
      
      // Reset form
      setFormData({
        kode_barang: '',
        nama_barang: '',
        kategori_id: 0,
        satuan: '',
        stok_minimal: 0,
        harga_per_unit: 0,
        deskripsi: '',
        merk: ''
      });
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || error?.data?.detail || 'Gagal menambahkan barang baru');
    }
  };

  const selectedKategori = kategoriList.find(k => k.id === formData.kategori_id);

  const satuanOptions = [
    'PCS', 'BOX', 'KG', 'GRAM', 'LITER', 'METER', 'ROLL', 'SET', 'UNIT', 'PAKET'
  ];

  if (loadingKategori) {
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
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📦 Tambah Barang Baru</h1>
        <p className="text-gray-600">Tambahkan barang baru ke dalam sistem inventory</p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Kode Barang */}
            <div>
              <label htmlFor="kode_barang" className="block text-sm font-medium text-gray-700 mb-2">
                Kode Barang *
              </label>
              <Input
                type="text"
                id="kode_barang"
                name="kode_barang"
                value={formData.kode_barang}
                onChange={handleInputChange}
                required
                className="w-full"
                placeholder="Masukkan kode barang (unik)"
              />
            </div>

            {/* Nama Barang */}
            <div>
              <label htmlFor="nama_barang" className="block text-sm font-medium text-gray-700 mb-2">
                Nama Barang *
              </label>
              <Input
                type="text"
                id="nama_barang"
                name="nama_barang"
                value={formData.nama_barang}
                onChange={handleInputChange}
                required
                className="w-full"
                placeholder="Masukkan nama barang"
              />
            </div>

            {/* Kategori */}
            <div>
              <label htmlFor="kategori_id" className="block text-sm font-medium text-gray-700 mb-2">
                Kategori *
              </label>
              <select
                id="kategori_id"
                name="kategori_id"
                value={formData.kategori_id || ''}
                onChange={handleInputChange}
                required
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Pilih Kategori</option>
                {Array.isArray(kategoriList) && kategoriList.length > 0 ? (
                  kategoriList.map(kategori => (
                    <option key={kategori.id} value={kategori.id}>
                      {kategori.kode_kategori} - {kategori.nama_kategori}
                    </option>
                  ))
                ) : (
                  <option value="" disabled>Loading kategori...</option>
                )}
              </select>
            </div>

            {/* Satuan */}
            <div>
              <label htmlFor="satuan" className="block text-sm font-medium text-gray-700 mb-2">
                Satuan *
              </label>
              <select
                id="satuan"
                name="satuan"
                value={formData.satuan}
                onChange={handleInputChange}
                required
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Pilih Satuan</option>
                {satuanOptions.map(satuan => (
                  <option key={satuan} value={satuan}>{satuan}</option>
                ))}
              </select>
            </div>

            {/* Stok Minimal */}
            <div>
              <label htmlFor="stok_minimal" className="block text-sm font-medium text-gray-700 mb-2">
                Stok Minimal
              </label>
              <Input
                type="number"
                id="stok_minimal"
                name="stok_minimal"
                value={formData.stok_minimal || ''}
                onChange={handleInputChange}
                min="0"
                className="w-full"
                placeholder="Masukkan stok minimal (opsional)"
              />
            </div>

            {/* Harga Per Unit */}
            <div>
              <label htmlFor="harga_per_unit" className="block text-sm font-medium text-gray-700 mb-2">
                Harga Per Unit
              </label>
              <Input
                type="number"
                id="harga_per_unit"
                name="harga_per_unit"
                value={formData.harga_per_unit || ''}
                onChange={handleInputChange}
                min="0"
                step="0.01"
                className="w-full"
                placeholder="Masukkan harga per unit (opsional)"
              />
            </div>

            {/* Merk */}
            <div className="md:col-span-2">
              <label htmlFor="merk" className="block text-sm font-medium text-gray-700 mb-2">
                Merk
              </label>
              <Input
                type="text"
                id="merk"
                name="merk"
                value={formData.merk || ''}
                onChange={handleInputChange}
                className="w-full"
                placeholder="Masukkan merk/brand (opsional)"
                list="merk-options"
              />
              <datalist id="merk-options">
                {merkList.map((merk, index) => (
                  <option key={index} value={merk} />
                ))}
              </datalist>
            </div>
          </div>

          {/* Deskripsi */}
          <div>
            <label htmlFor="deskripsi" className="block text-sm font-medium text-gray-700 mb-2">
              Spesifikasi Teknis
            </label>
            <textarea
              id="deskripsi"
              name="deskripsi"
              value={formData.deskripsi}
              onChange={handleInputChange}
              rows={3}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-vertical"
              placeholder="Tambahkan spesifikasi teknis (opsional)"
            />
          </div>

          {/* Info Kategori */}
          {selectedKategori && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">🏷️ Informasi Kategori</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-600">Kode Kategori:</span>
                  <p className="font-medium text-gray-800">{selectedKategori.kode_kategori}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Nama Kategori:</span>
                  <p className="font-medium text-gray-800">{selectedKategori.nama_kategori}</p>
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
              Tambah Barang Baru
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setFormData({
                  kode_barang: '',
                  nama_barang: '',
                  kategori_id: 0,
                  satuan: '',
                  stok_minimal: 0,
                  harga_per_unit: 0,
                  deskripsi: '',
                  merk: ''
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
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">ℹ️ Informasi Penting</h3>
        <ul className="space-y-1 text-sm text-gray-700">
          <li>✅ Kode barang harus unik dan tidak boleh duplikat</li>
          <li>📊 Barang baru akan otomatis memiliki stok 0</li>
          <li>🔍 Barang dapat dikelola melalui menu stok barang</li>
          <li>⚠️ Pastikan data yang dimasukkan sudah benar</li>
        </ul>
      </div>
    </div>
  );
};

export default TambahBarangPage;

