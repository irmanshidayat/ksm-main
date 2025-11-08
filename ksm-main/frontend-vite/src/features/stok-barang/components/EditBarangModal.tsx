/**
 * Edit Barang Modal Component
 * Modal untuk edit barang dengan Tailwind
 */

import React, { useState, useEffect } from 'react';
import { Modal, Button, Input, NumberInput } from '@/shared/components/ui';
import { useUpdateBarangMutation, useGetKategoriQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import type { Barang, Kategori } from '../types';
import Swal from 'sweetalert2';

interface EditBarangModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  item: Barang | null;
}

const EditBarangModal: React.FC<EditBarangModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  item
}) => {
  const sweetAlert = useSweetAlert();
  const { data: kategoriList = [] } = useGetKategoriQuery();
  const [updateBarang, { isLoading }] = useUpdateBarangMutation();

  const [formData, setFormData] = useState({
    kode_barang: '',
    nama_barang: '',
    deskripsi: '',
    kategori_id: '',
    satuan: 'PCS',
    harga_per_unit: '',
    stok_minimum: '',
    stok_maksimum: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen && item) {
      setFormData({
        kode_barang: item.kode_barang,
        nama_barang: item.nama_barang,
        deskripsi: item.deskripsi || '',
        kategori_id: item.kategori?.id?.toString() || '',
        satuan: item.satuan,
        harga_per_unit: item.harga_per_unit?.toString() || '',
        stok_minimum: item.stok?.stok_minimum?.toString() || '',
        stok_maksimum: item.stok?.stok_maksimum?.toString() || ''
      });
      setErrors({});
    }
  }, [isOpen, item]);

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: String(value) }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.kode_barang.trim()) {
      newErrors.kode_barang = 'Kode barang wajib diisi';
    }
    if (!formData.nama_barang.trim()) {
      newErrors.nama_barang = 'Nama barang wajib diisi';
    }
    if (!formData.kategori_id) {
      newErrors.kategori_id = 'Kategori wajib dipilih';
    }
    if (!formData.satuan.trim()) {
      newErrors.satuan = 'Satuan wajib diisi';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!item || !validateForm()) {
      return;
    }

    Swal.fire({
      title: 'Memproses...',
      text: 'Sedang memperbarui data barang...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });

    try {
      const dataToSend = {
        kode_barang: formData.kode_barang,
        nama_barang: formData.nama_barang,
        deskripsi: formData.deskripsi,
        kategori_id: parseInt(formData.kategori_id),
        satuan: formData.satuan,
        harga_per_unit: formData.harga_per_unit ? parseFloat(formData.harga_per_unit) : 0,
        stok: {
          stok_minimum: formData.stok_minimum ? parseInt(formData.stok_minimum) : 0,
          stok_maksimum: formData.stok_maksimum ? parseInt(formData.stok_maksimum) : undefined
        }
      };

      await updateBarang({ id: item.id, data: dataToSend }).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Data barang berhasil diperbarui');
      onSuccess();
      onClose();
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal memperbarui data barang');
    }
  };

  const satuanOptions = ['PCS', 'BOX', 'KG', 'GRAM', 'LITER', 'METER', 'ROLL', 'SET', 'UNIT', 'PAKET'];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="✏️ Edit Barang"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Kode Barang *
            </label>
            <Input
              value={formData.kode_barang}
              onChange={(e) => handleInputChange('kode_barang', e.target.value)}
              required
              className="w-full"
            />
            {errors.kode_barang && (
              <p className="text-sm text-red-600 mt-1">{errors.kode_barang}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nama Barang *
            </label>
            <Input
              value={formData.nama_barang}
              onChange={(e) => handleInputChange('nama_barang', e.target.value)}
              required
              className="w-full"
            />
            {errors.nama_barang && (
              <p className="text-sm text-red-600 mt-1">{errors.nama_barang}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Kategori *
            </label>
            <select
              value={formData.kategori_id}
              onChange={(e) => handleInputChange('kategori_id', e.target.value)}
              required
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Pilih Kategori</option>
              {kategoriList.map((kategori: Kategori) => (
                <option key={kategori.id} value={kategori.id}>
                  {kategori.kode_kategori} - {kategori.nama_kategori}
                </option>
              ))}
            </select>
            {errors.kategori_id && (
              <p className="text-sm text-red-600 mt-1">{errors.kategori_id}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Satuan *
            </label>
            <select
              value={formData.satuan}
              onChange={(e) => handleInputChange('satuan', e.target.value)}
              required
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {satuanOptions.map(satuan => (
                <option key={satuan} value={satuan}>{satuan}</option>
              ))}
            </select>
            {errors.satuan && (
              <p className="text-sm text-red-600 mt-1">{errors.satuan}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Harga Per Unit
            </label>
            <NumberInput
              value={formData.harga_per_unit || '0'}
              onChange={(value) => handleInputChange('harga_per_unit', value)}
              min="0"
              step="0.01"
              className="w-full"
              returnAsString={true}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Stok Minimum
            </label>
            <NumberInput
              value={formData.stok_minimum || '0'}
              onChange={(value) => handleInputChange('stok_minimum', value)}
              min="0"
              className="w-full"
              returnAsString={true}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Stok Maksimum
            </label>
            <NumberInput
              value={formData.stok_maksimum || '0'}
              onChange={(value) => handleInputChange('stok_maksimum', value)}
              min="0"
              className="w-full"
              returnAsString={true}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Deskripsi
          </label>
          <textarea
            value={formData.deskripsi}
            onChange={(e) => handleInputChange('deskripsi', e.target.value)}
            rows={3}
            className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
          />
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Batal
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isLoading}
          >
            Simpan Perubahan
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default EditBarangModal;

