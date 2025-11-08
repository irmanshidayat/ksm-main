/**
 * Vendor Self Registration Page
 * Halaman public untuk vendor mendaftar sendiri dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVendorSelfRegisterMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { Textarea } from '@/shared/components/ui/Form';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { VendorSelfRegistrationRequest } from '../types';

const VendorSelfRegistrationPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<Partial<VendorSelfRegistrationRequest>>({
    company_name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    business_license: '',
    tax_id: '',
    bank_account: '',
    vendor_category: 'general',
    vendor_type: 'internal',
    business_model: 'supplier',
    custom_category: '',
    ktp_director_name: '',
    ktp_director_number: '',
    password: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [showCustomCategory, setShowCustomCategory] = useState(false);

  const [register, { isLoading: registering }] = useVendorSelfRegisterMutation();

  const validateStep1 = (): boolean => {
    const errors: { [key: string]: string } = {};
    
    if (!formData.company_name?.trim()) {
      errors.company_name = 'Nama perusahaan harus diisi';
    }
    
    if (!formData.contact_person?.trim()) {
      errors.contact_person = 'Nama kontak harus diisi';
    }
    
    if (!formData.email?.trim()) {
      errors.email = 'Email harus diisi';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Format email tidak valid';
    }
    
    if (!formData.phone?.trim()) {
      errors.phone = 'Nomor telepon harus diisi';
    }
    
    if (formData.vendor_category === 'custom' && !formData.custom_category?.trim()) {
      errors.custom_category = 'Kategori custom harus diisi';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateStep2 = (): boolean => {
    const errors: { [key: string]: string } = {};
    
    if (!formData.password) {
      errors.password = 'Password harus diisi';
    } else if (formData.password.length < 6) {
      errors.password = 'Password minimal 6 karakter';
    }
    
    if (!confirmPassword) {
      errors.confirm_password = 'Konfirmasi password harus diisi';
    } else if (formData.password !== confirmPassword) {
      errors.confirm_password = 'Password tidak sama';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (currentStep === 1 && validateStep1()) {
      setCurrentStep(2);
    }
  };

  const handlePrevious = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep2()) return;

    try {
      const result = await register(formData as VendorSelfRegistrationRequest).unwrap();
      
      if (result.success) {
        await sweetAlert.showSuccessAuto('Berhasil', 'Registrasi vendor berhasil! Anda akan diarahkan ke halaman login.');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        await sweetAlert.showError('Gagal', result.message || 'Gagal mendaftarkan vendor');
      }
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.data?.message || error?.message || 'Terjadi kesalahan saat mendaftarkan vendor');
    }
  };

  const handleInputChange = (field: keyof VendorSelfRegistrationRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (field === 'vendor_category') {
      setShowCustomCategory(value === 'custom');
      if (value !== 'custom') {
        setFormData(prev => ({ ...prev, custom_category: '' }));
      }
    }
    // Clear error for this field
    if (formErrors[field as string]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field as string];
        return newErrors;
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">📝 Registrasi Vendor</h1>
          <p className="text-gray-600">Daftarkan perusahaan Anda sebagai vendor</p>
        </div>

        {/* Step Indicator */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className={`flex items-center ${currentStep >= 1 ? 'text-primary-600' : 'text-gray-400'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                currentStep >= 1 ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}>
                {currentStep > 1 ? '✓' : '1'}
              </div>
              <span className="ml-2 font-medium">Informasi Perusahaan</span>
            </div>
            <div className="flex-1 h-1 mx-4 bg-gray-200">
              <div className={`h-full transition-all ${currentStep >= 2 ? 'bg-primary-600' : 'bg-gray-200'}`} style={{ width: currentStep >= 2 ? '100%' : '0%' }} />
            </div>
            <div className={`flex items-center ${currentStep >= 2 ? 'text-primary-600' : 'text-gray-400'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                currentStep >= 2 ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}>
                2
              </div>
              <span className="ml-2 font-medium">Akun Login</span>
            </div>
          </div>
        </div>

        {/* Form Content */}
        <div className="bg-white rounded-lg shadow-md p-6">
          {currentStep === 1 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">📋 Informasi Perusahaan</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Nama Perusahaan *"
                  value={formData.company_name || ''}
                  onChange={(e) => handleInputChange('company_name', e.target.value)}
                  error={formErrors.company_name}
                  required
                />
                <Input
                  label="Nama Kontak *"
                  value={formData.contact_person || ''}
                  onChange={(e) => handleInputChange('contact_person', e.target.value)}
                  error={formErrors.contact_person}
                  required
                />
                <Input
                  type="email"
                  label="Email *"
                  value={formData.email || ''}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  error={formErrors.email}
                  required
                />
                <Input
                  type="tel"
                  label="Nomor Telepon *"
                  value={formData.phone || ''}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  error={formErrors.phone}
                  required
                />
                <div className="md:col-span-2">
                  <Textarea
                    label="Alamat"
                    value={formData.address || ''}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Kategori Vendor</label>
                  <select
                    value={formData.vendor_category || 'general'}
                    onChange={(e) => handleInputChange('vendor_category', e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="general">General</option>
                    <option value="specialized">Specialized</option>
                    <option value="preferred">Preferred</option>
                    <option value="supplier">Supplier</option>
                    <option value="contractor">Contractor</option>
                    <option value="agent_tunggal">Agent Tunggal</option>
                    <option value="distributor">Distributor</option>
                    <option value="jasa">Jasa</option>
                    <option value="produk">Produk</option>
                    <option value="custom">Lainnya (Custom)</option>
                  </select>
                </div>
                {showCustomCategory && (
                  <Input
                    label="Kategori Custom *"
                    value={formData.custom_category || ''}
                    onChange={(e) => handleInputChange('custom_category', e.target.value)}
                    error={formErrors.custom_category}
                    required
                  />
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Jenis Vendor</label>
                  <select
                    value={formData.vendor_type || 'internal'}
                    onChange={(e) => handleInputChange('vendor_type', e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="internal">Vendor Internal</option>
                    <option value="partner">Vendor Mitra</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Model Bisnis</label>
                  <select
                    value={formData.business_model || 'supplier'}
                    onChange={(e) => handleInputChange('business_model', e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="supplier">Supplier</option>
                    <option value="reseller">Reseller</option>
                    <option value="both">Supplier & Reseller</option>
                  </select>
                </div>
                <Input
                  label="Nomor NIB"
                  value={formData.business_license || ''}
                  onChange={(e) => handleInputChange('business_license', e.target.value)}
                />
                <Input
                  label="NPWP"
                  value={formData.tax_id || ''}
                  onChange={(e) => handleInputChange('tax_id', e.target.value)}
                />
                <Input
                  label="Nomor Rekening"
                  value={formData.bank_account || ''}
                  onChange={(e) => handleInputChange('bank_account', e.target.value)}
                />
                <Input
                  label="Nama Direktur/Penanggung Jawab"
                  value={formData.ktp_director_name || ''}
                  onChange={(e) => handleInputChange('ktp_director_name', e.target.value)}
                />
                <Input
                  label="Nomor KTP Direktur"
                  value={formData.ktp_director_number || ''}
                  onChange={(e) => handleInputChange('ktp_director_number', e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="primary" onClick={handleNext}>
                  Selanjutnya →
                </Button>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">🔐 Informasi Akun Login</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  type="password"
                  label="Password *"
                  value={formData.password || ''}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  error={formErrors.password}
                  required
                />
                <Input
                  type="password"
                  label="Konfirmasi Password *"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    if (formErrors.confirm_password) {
                      setFormErrors(prev => {
                        const newErrors = { ...prev };
                        delete newErrors.confirm_password;
                        return newErrors;
                      });
                    }
                  }}
                  error={formErrors.confirm_password}
                  required
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-900 mb-2">Persyaratan Password:</h4>
                <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
                  <li>Minimal 6 karakter</li>
                  <li>Gunakan kombinasi huruf dan angka untuk keamanan yang lebih baik</li>
                </ul>
              </div>

              <div className="flex justify-between gap-2 pt-4">
                <Button variant="outline" onClick={handlePrevious}>
                  ← Sebelumnya
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSubmit}
                  disabled={registering}
                >
                  {registering ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Mendaftarkan...
                    </>
                  ) : (
                    'Daftar'
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Sudah punya akun? <a href="/login" className="text-primary-600 hover:underline">Login di sini</a></p>
        </div>
      </div>
    </div>
  );
};

export default VendorSelfRegistrationPage;

