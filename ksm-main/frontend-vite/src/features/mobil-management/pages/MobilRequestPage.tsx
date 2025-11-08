/**
 * Mobil Request Page
 * Form untuk request mobil dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useGetMobilsQuery, useCreateReservationMutation, useCheckMobilAvailabilityQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';

const MobilRequestPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sweetAlert = useSweetAlert();
  const [createReservation, { isLoading }] = useCreateReservationMutation();

  const { data: mobilsData } = useGetMobilsQuery({ page: 1, per_page: 100 });
  const mobils = mobilsData?.items || [];

  const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Baca query params dari URL
  const tanggalMulaiFromUrl = searchParams.get('tanggal_mulai');
  const tanggalSelesaiFromUrl = searchParams.get('tanggal_selesai');
  const mobilIdFromUrl = searchParams.get('mobil_id');

  const [formData, setFormData] = useState({
    mobil_id: mobilIdFromUrl || '',
    tanggal_mulai: tanggalMulaiFromUrl || '',
    tanggal_selesai: tanggalSelesaiFromUrl || '',
    jam_mulai: '08:00',
    jam_selesai: '17:00',
    keperluan: '',
    is_recurring: false,
    recurring_pattern: 'weekly',
    recurring_end_date: '',
  });

  useEffect(() => {
    // Set default dates jika tidak ada dari URL
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    // Jika ada tanggal dari URL, gunakan itu
    if (tanggalMulaiFromUrl && tanggalSelesaiFromUrl) {
      setFormData(prev => ({
        ...prev,
        tanggal_mulai: tanggalMulaiFromUrl,
        tanggal_selesai: tanggalSelesaiFromUrl,
        mobil_id: mobilIdFromUrl || prev.mobil_id,
      }));
    } else {
      // Jika tidak ada dari URL, set default
      setFormData(prev => {
        // Hanya set default jika belum ada nilai
        if (!prev.tanggal_mulai) {
          return {
            ...prev,
            tanggal_mulai: formatDate(today),
            tanggal_selesai: formatDate(tomorrow),
          };
        }
        return prev;
      });
    }
  }, [tanggalMulaiFromUrl, tanggalSelesaiFromUrl, mobilIdFromUrl]);

  const { data: availabilityData } = useCheckMobilAvailabilityQuery(
    {
      mobil_id: parseInt(formData.mobil_id) || 0,
      start_date: formData.tanggal_mulai,
      end_date: formData.tanggal_selesai,
    },
    { skip: !formData.mobil_id || !formData.tanggal_mulai || !formData.tanggal_selesai }
  );

  const isAvailable = availabilityData?.available ?? true;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.mobil_id || !formData.tanggal_mulai || !formData.tanggal_selesai) {
      await sweetAlert.showError('Error', 'Mohon lengkapi semua field yang wajib diisi');
      return;
    }

    if (!isAvailable) {
      await sweetAlert.showError('Error', 'Mobil tidak tersedia pada tanggal yang dipilih');
      return;
    }

    try {
      const reservationData = {
        mobil_id: parseInt(formData.mobil_id),
        tanggal_mulai: formData.tanggal_mulai,
        tanggal_selesai: formData.tanggal_selesai,
        jam_mulai: formData.jam_mulai,
        jam_selesai: formData.jam_selesai,
        keperluan: formData.keperluan,
        is_recurring: formData.is_recurring,
        recurring_pattern: formData.is_recurring ? formData.recurring_pattern : undefined,
        recurring_end_date: formData.is_recurring ? formData.recurring_end_date : undefined,
      };

      await createReservation(reservationData).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Request mobil berhasil dibuat');
      
      // Navigate ke calendar dengan query params untuk auto-open modal
      navigate(`/mobil/calendar?open_modal=true&mobil_id=${formData.mobil_id}&date=${formData.tanggal_mulai}`);
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal membuat request mobil');
    }
  };

  const selectedMobil = mobils.find(m => m.id === parseInt(formData.mobil_id));

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📝 Request Mobil</h1>
            <p className="text-gray-600">Buat request untuk menggunakan mobil perusahaan</p>
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
                Pilih Mobil *
              </label>
              <select
                name="mobil_id"
                value={formData.mobil_id}
                onChange={handleInputChange}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                <option value="">-- Pilih Mobil --</option>
                {mobils
                  .filter(m => m.status === 'active')
                  .map(mobil => (
                    <option key={mobil.id} value={mobil.id}>
                      {mobil.nama || mobil.nama_mobil} - {mobil.plat_nomor}
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status Ketersediaan
              </label>
              {formData.mobil_id && formData.tanggal_mulai && formData.tanggal_selesai ? (
                <div className={`p-3 rounded-lg ${
                  isAvailable ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                }`}>
                  {isAvailable ? '✅ Tersedia' : '❌ Tidak Tersedia'}
                </div>
              ) : (
                <div className="p-3 rounded-lg bg-gray-50 text-gray-600">
                  Pilih mobil dan tanggal terlebih dahulu
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tanggal Mulai *
              </label>
              <Input
                type="date"
                name="tanggal_mulai"
                value={formData.tanggal_mulai}
                onChange={handleInputChange}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tanggal Selesai *
              </label>
              <Input
                type="date"
                name="tanggal_selesai"
                value={formData.tanggal_selesai}
                onChange={handleInputChange}
                min={formData.tanggal_mulai}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Jam Mulai
              </label>
              <Input
                type="time"
                name="jam_mulai"
                value={formData.jam_mulai}
                onChange={handleInputChange}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Jam Selesai
              </label>
              <Input
                type="time"
                name="jam_selesai"
                value={formData.jam_selesai}
                onChange={handleInputChange}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Keperluan *
              </label>
              <textarea
                name="keperluan"
                value={formData.keperluan}
                onChange={handleInputChange}
                rows={3}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                placeholder="Jelaskan keperluan penggunaan mobil..."
                required
              />
            </div>

            <div className="md:col-span-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="is_recurring"
                  checked={formData.is_recurring}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  Recurring Request
                </span>
              </label>
            </div>

            {formData.is_recurring && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Pattern
                  </label>
                  <select
                    name="recurring_pattern"
                    value={formData.recurring_pattern}
                    onChange={handleInputChange}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="daily">Harian</option>
                    <option value="weekly">Mingguan</option>
                    <option value="monthly">Bulanan</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tanggal Akhir Recurring
                  </label>
                  <Input
                    type="date"
                    name="recurring_end_date"
                    value={formData.recurring_end_date}
                    onChange={handleInputChange}
                    min={formData.tanggal_selesai}
                  />
                </div>
              </>
            )}
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
              disabled={!isAvailable && formData.mobil_id && formData.tanggal_mulai && formData.tanggal_selesai}
            >
              Buat Request
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MobilRequestPage;

