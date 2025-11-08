/**
 * Mobil Add Page
 * Form untuk tambah mobil baru dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateMobilMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';

const MobilAddPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [createMobil, { isLoading }] = useCreateMobilMutation();

  const [formData, setFormData] = useState({
    nama: '',
    plat_nomor: '',
    status: 'active',
    is_backup: false,
    priority_score: 0,
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (name === 'priority_score') {
      setFormData(prev => ({ ...prev, [name]: parseInt(value) || 0 }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.nama || !formData.plat_nomor) {
      await sweetAlert.showError('Error', 'Nama dan plat nomor harus diisi');
      return;
    }

    try {
      await createMobil(formData).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Mobil berhasil ditambahkan');
      navigate('/mobil/dashboard');
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal menambah mobil');
    }
  };

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🚗 Tambah Mobil Baru</h1>
            <p className="text-gray-600">Tambahkan mobil baru ke dalam sistem perusahaan</p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/mobil/dashboard')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nama Mobil *
              </label>
              <Input
                type="text"
                name="nama"
                value={formData.nama}
                onChange={handleInputChange}
                placeholder="Contoh: Avanza, Innova, Fortuner"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Plat Nomor *
              </label>
              <Input
                type="text"
                name="plat_nomor"
                value={formData.plat_nomor}
                onChange={handleInputChange}
                placeholder="Contoh: B 1234 ABC"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleInputChange}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="active">Aktif</option>
                <option value="maintenance">Maintenance</option>
                <option value="inactive">Tidak Aktif</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority Score
              </label>
              <Input
                type="number"
                name="priority_score"
                value={formData.priority_score}
                onChange={handleInputChange}
                min="0"
                placeholder="0"
              />
            </div>

            <div className="md:col-span-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="is_backup"
                  checked={formData.is_backup}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  Mobil Backup
                </span>
              </label>
              <p className="text-xs text-gray-500 mt-1">
                Centang jika mobil ini digunakan sebagai backup
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/mobil/dashboard')}
              disabled={isLoading}
            >
              Batal
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isLoading}
            >
              Simpan Mobil
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MobilAddPage;

