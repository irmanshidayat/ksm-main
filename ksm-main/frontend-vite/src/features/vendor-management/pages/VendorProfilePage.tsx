/**
 * Vendor Profile Page
 * Halaman untuk melihat dan mengedit profile vendor dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetVendorProfileQuery, useUpdateVendorProfileMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';

const VendorProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const { data: vendorInfo, isLoading, error, refetch } = useGetVendorProfileQuery();
  const [updateProfile, { isLoading: saving }] = useUpdateVendorProfileMutation();

  // SweetAlert loading
  useEffect(() => {
    if (isLoading) {
      sweetAlert.showLoading('Memuat...', 'Mengambil data profile vendor');
    } else {
      sweetAlert.hideLoading();
    }
  }, [isLoading, sweetAlert]);

  // Handle error
  useEffect(() => {
    (async () => {
      if (error && 'status' in error) {
        if (error.status === 401) {
          localStorage.removeItem('KSM_access_token');
          localStorage.removeItem('KSM_refresh_token');
          localStorage.removeItem('KSM_user');
          navigate('/login');
        } else if (error.status === 404) {
          const goRegister = await sweetAlert.showConfirm(
            'Profil Vendor Belum Ada',
            'Silakan lakukan registrasi vendor terlebih dahulu. Buka halaman registrasi sekarang?'
          );
          if (goRegister) {
            navigate('/vendor/register');
          }
        } else if (error.status !== 404) {
          await sweetAlert.showError('Gagal Memuat', 'Terjadi kesalahan saat memuat profile vendor.');
        }
      }
    })();
  }, [error, sweetAlert, navigate]);

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    company_name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: ''
  });

  React.useEffect(() => {
    if (vendorInfo) {
      setFormData({
        company_name: vendorInfo.company_name,
        contact_person: vendorInfo.contact_person,
        email: vendorInfo.email,
        phone: vendorInfo.phone || '',
        address: vendorInfo.address || ''
      });
    }
  }, [vendorInfo]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = async () => {
    try {
      await updateProfile(formData).unwrap();
      setIsEditing(false);
      await sweetAlert.showSuccessAuto('Berhasil', 'Profile berhasil diperbarui');
      refetch();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal memperbarui profile');
    }
  };

  const handleCancel = () => {
    if (vendorInfo) {
      setFormData({
        company_name: vendorInfo.company_name,
        contact_person: vendorInfo.contact_person,
        email: vendorInfo.email,
        phone: vendorInfo.phone || '',
        address: vendorInfo.address || ''
      });
    }
    setIsEditing(false);
  };

  if (isLoading) return null;

  if (error && 'status' in error && error.status !== 404) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Gagal memuat profile</p>
          <Button variant="primary" onClick={() => refetch()}>
            Coba Lagi
          </Button>
        </div>
      </div>
    );
  }

  if (!vendorInfo) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">Data Tidak Ditemukan</h3>
          <p className="text-yellow-600">Tidak dapat memuat profile</p>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Profile Vendor</h1>
            <p className="text-gray-600">Kelola informasi profile perusahaan Anda</p>
          </div>
          {!isEditing && (
            <Button
              variant="primary"
              onClick={() => setIsEditing(true)}
            >
              ✏️ Edit Profile
            </Button>
          )}
        </div>
      </div>

      {/* Profile Form */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nama Perusahaan *
            </label>
            <Input
              name="company_name"
              value={formData.company_name}
              onChange={handleInputChange}
              disabled={!isEditing}
              required
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Contact Person *
            </label>
            <Input
              name="contact_person"
              value={formData.contact_person}
              onChange={handleInputChange}
              disabled={!isEditing}
              required
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email *
            </label>
            <Input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              disabled={!isEditing}
              required
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Telepon
            </label>
            <Input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              disabled={!isEditing}
              className="w-full"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Alamat
            </label>
            <textarea
              name="address"
              value={formData.address}
              onChange={handleInputChange}
              disabled={!isEditing}
              rows={3}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical disabled:bg-gray-100"
            />
          </div>
        </div>

        {/* Read-only Info */}
        <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Status</label>
            <p className="text-sm text-gray-800">{vendorInfo.status}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Kategori</label>
            <p className="text-sm text-gray-800">{vendorInfo.vendor_category}</p>
          </div>
        </div>

        {/* Action Buttons */}
        {isEditing && (
          <div className="flex justify-end gap-2 mt-6 pt-6 border-t border-gray-200">
            <Button
              variant="outline"
              onClick={handleCancel}
              disabled={saving}
            >
              Batal
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              isLoading={saving}
            >
              Simpan Perubahan
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default VendorProfilePage;

