/**
 * Vendor Detail Page (Admin)
 * Halaman detail vendor untuk admin dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetVendorByIdQuery, useDeleteVendorMutation, useUpdateVendorMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import Swal from 'sweetalert2';

const VendorDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const vendorId = id ? parseInt(id) : 0;

  const { data: vendor, isLoading, error, refetch } = useGetVendorByIdQuery(vendorId);
  const [deleteVendor] = useDeleteVendorMutation();
  const [updateVendor] = useUpdateVendorMutation();
  const [activeTab, setActiveTab] = useState<'info' | 'documents'>('info');

  const handleDelete = async () => {
    const confirmed = await sweetAlert.showConfirm(
      'Hapus Vendor',
      `Apakah Anda yakin ingin menghapus ${vendor?.company_name}?`
    );

    if (confirmed) {
      try {
        Swal.fire({
          title: 'Menghapus...',
          text: 'Sedang menghapus vendor...',
          allowOutsideClick: false,
          allowEscapeKey: false,
          showConfirmButton: false,
          didOpen: () => {
            Swal.showLoading();
          },
        });

        await deleteVendor(vendorId).unwrap();
        Swal.close();
        await sweetAlert.showSuccessAuto('Berhasil', 'Vendor berhasil dihapus');
        navigate('/vendor/daftar');
      } catch (error: any) {
        Swal.close();
        await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menghapus vendor');
      }
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      Swal.fire({
        title: 'Memperbarui...',
        text: 'Sedang memperbarui status vendor...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      await updateVendor({ id: vendorId, data: { status: newStatus } }).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Status vendor berhasil diubah');
      refetch();
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal mengubah status');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Gagal memuat detail vendor</p>
          <div className="flex gap-2 justify-center">
            <Button variant="outline" onClick={() => navigate('/vendor/daftar')}>
              Kembali
            </Button>
            <Button variant="primary" onClick={() => refetch()}>
              Coba Lagi
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!vendor) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">Vendor Tidak Ditemukan</h3>
          <Button variant="primary" onClick={() => navigate('/vendor/daftar')}>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">{vendor.company_name}</h1>
            <p className="text-gray-600">Detail informasi vendor</p>
          </div>
          <div className="flex gap-2">
            <select
              value={vendor.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="pending">Pending</option>
            </select>
            <Button
              variant="danger"
              onClick={handleDelete}
            >
              🗑️ Hapus
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/vendor/daftar')}
            >
              ← Kembali
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('info')}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === 'info'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Informasi
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === 'documents'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Dokumen
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'info' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">Informasi Vendor</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Nama Perusahaan</label>
              <p className="text-sm text-gray-800">{vendor.company_name}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Contact Person</label>
              <p className="text-sm text-gray-800">{vendor.contact_person}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Email</label>
              <p className="text-sm text-gray-800">{vendor.email}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Telepon</label>
              <p className="text-sm text-gray-800">{vendor.phone || '-'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Alamat</label>
              <p className="text-sm text-gray-800">{vendor.address || '-'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Kategori</label>
              <p className="text-sm text-gray-800">{vendor.vendor_category}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Status</label>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                vendor.status === 'active' ? 'bg-green-100 text-green-800' :
                vendor.status === 'inactive' ? 'bg-gray-100 text-gray-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {vendor.status}
              </span>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Tanggal Dibuat</label>
              <p className="text-sm text-gray-800">
                {new Date(vendor.created_at).toLocaleDateString('id-ID')}
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'documents' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">Dokumen Vendor</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {vendor.documents && Object.entries(vendor.documents).map(([key, value]: [string, any]) => (
              <div key={key} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-800 capitalize">
                      {key.replace(/_/g, ' ').replace(/_file/g, '')}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {value ? 'Tersedia' : 'Tidak tersedia'}
                    </p>
                  </div>
                  {value && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // Handle download
                        window.open(value, '_blank');
                      }}
                    >
                      📥 Download
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default VendorDetailPage;

