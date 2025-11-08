/**
 * Dashboard Stok Barang Page
 * Halaman dashboard untuk monitoring stok barang
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetDashboardQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import Swal from 'sweetalert2';

const DashboardStokPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const { data: dashboardData, isLoading, error, refetch } = useGetDashboardQuery();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR'
    }).format(amount);
  };

  const safeArrayLength = (array: any[] | undefined | null): number => {
    return Array.isArray(array) ? array.length : 0;
  };

  const safeArraySlice = (array: any[] | undefined | null, start: number, end: number): any[] => {
    return Array.isArray(array) ? array.slice(start, end) : [];
  };

  const handleRefresh = async () => {
    Swal.fire({
      title: 'Memperbarui Data',
      text: 'Sedang memperbarui data dashboard...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });
    try {
      await refetch();
      Swal.close();
      await sweetAlert.showSuccessAuto('Data Berhasil Diperbarui', 'Data dashboard stok barang berhasil diperbarui');
    } catch (err) {
      Swal.close();
      await sweetAlert.showError('Gagal Memperbarui Data', 'Terjadi kesalahan saat memperbarui data dashboard');
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
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md w-full text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">{error.toString()}</p>
          <Button onClick={async () => {
            Swal.fire({
              title: 'Memuat Ulang',
              text: 'Sedang memuat ulang data dashboard...',
              allowOutsideClick: false,
              allowEscapeKey: false,
              showConfirmButton: false,
              didOpen: () => {
                Swal.showLoading();
              },
            });
            try {
              await refetch();
              Swal.close();
              await sweetAlert.showSuccessAuto('Data Berhasil Dimuat', 'Data dashboard stok barang berhasil dimuat ulang');
            } catch (err) {
              Swal.close();
              await sweetAlert.showError('Gagal Memuat Data', 'Terjadi kesalahan saat memuat data dashboard');
            }
          }}>
            Coba Lagi
          </Button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Tidak ada data tersedia</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">📊 Dashboard Stok Barang</h1>
        <p className="text-gray-600">Monitoring real-time stok barang dan aktivitas inventory</p>
      </div>

      {/* Statistik Utama */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        <div 
          className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500 cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => navigate('/stok-barang/daftar-barang')}
        >
          <div className="flex items-center space-x-4">
            <div className="text-4xl">📦</div>
            <div>
              <h3 className="text-sm font-medium text-gray-600">Total Barang</h3>
              <p className="text-2xl font-bold text-gray-800">{dashboardData.total_barang || 0}</p>
              <span className="text-xs text-gray-500">item</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
          <div className="flex items-center space-x-4">
            <div className="text-4xl">🏷️</div>
            <div>
              <h3 className="text-sm font-medium text-gray-600">Total Kategori</h3>
              <p className="text-2xl font-bold text-gray-800">{dashboardData.total_kategori || 0}</p>
              <span className="text-xs text-gray-500">kategori</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-400">
          <div className="flex items-center space-x-4">
            <div className="text-4xl">📥</div>
            <div>
              <h3 className="text-sm font-medium text-gray-600">Barang Masuk</h3>
              <p className="text-2xl font-bold text-gray-800">{dashboardData.barang_masuk_hari_ini || 0}</p>
              <span className="text-xs text-gray-500">hari ini</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-yellow-500">
          <div className="flex items-center space-x-4">
            <div className="text-4xl">📤</div>
            <div>
              <h3 className="text-sm font-medium text-gray-600">Barang Keluar</h3>
              <p className="text-2xl font-bold text-gray-800">{dashboardData.barang_keluar_hari_ini || 0}</p>
              <span className="text-xs text-gray-500">hari ini</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
          <div className="flex items-center space-x-4">
            <div className="text-4xl">💰</div>
            <div>
              <h3 className="text-sm font-medium text-gray-600">Total Nilai Stok</h3>
              <p className="text-lg font-bold text-gray-800">{formatCurrency(dashboardData.total_nilai_stok || 0)}</p>
              <span className="text-xs text-gray-500">nilai inventory</span>
            </div>
          </div>
        </div>
      </div>

      {/* Alert Stok */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Stok Menipis */}
        <div className="bg-white rounded-lg shadow-md border-l-4 border-yellow-500">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">⚠️ Stok Menipis</h3>
              <span className="bg-yellow-100 text-yellow-800 text-sm font-semibold px-3 py-1 rounded-full">
                {safeArrayLength(dashboardData.stok_menipis)}
              </span>
            </div>
            <div className="space-y-2">
              {safeArrayLength(dashboardData.stok_menipis) > 0 ? (
                <ul className="space-y-2">
                  {safeArraySlice(dashboardData.stok_menipis, 0, 5).map((item, index) => (
                    <li key={index} className="flex items-center justify-between p-2 bg-yellow-50 rounded">
                      <span className="text-sm font-medium text-gray-800">
                        {item?.barang?.nama_barang || 'Nama tidak tersedia'}
                      </span>
                      <span className="text-sm text-gray-600">
                        {item?.jumlah_stok || 0} {item?.barang?.satuan || 'unit'}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">Tidak ada stok yang menipis</p>
              )}
            </div>
          </div>
        </div>

        {/* Stok Habis */}
        <div className="bg-white rounded-lg shadow-md border-l-4 border-red-500">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">🚨 Stok Habis</h3>
              <span className="bg-red-100 text-red-800 text-sm font-semibold px-3 py-1 rounded-full">
                {safeArrayLength(dashboardData.stok_habis)}
              </span>
            </div>
            <div className="space-y-2">
              {safeArrayLength(dashboardData.stok_habis) > 0 ? (
                <ul className="space-y-2">
                  {safeArraySlice(dashboardData.stok_habis, 0, 5).map((item, index) => (
                    <li key={index} className="flex items-center justify-between p-2 bg-red-50 rounded">
                      <span className="text-sm font-medium text-gray-800">
                        {item?.barang?.nama_barang || 'Nama tidak tersedia'}
                      </span>
                      <span className="text-sm text-gray-600">0 {item?.barang?.satuan || 'unit'}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">Tidak ada stok yang habis</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">🚀 Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Button
            variant="primary"
            className="w-full"
            onClick={() => navigate('/stok-barang/barang-masuk')}
          >
            <span className="mr-2">📥</span>
            Tambah Barang Masuk
          </Button>
          <Button
            variant="primary"
            className="w-full"
            onClick={() => navigate('/stok-barang/barang-keluar')}
          >
            <span className="mr-2">📤</span>
            Tambah Barang Keluar
          </Button>
          <Button
            variant="primary"
            className="w-full"
            onClick={() => navigate('/stok-barang/tambah-barang')}
          >
            <span className="mr-2">📦</span>
            Tambah Barang Baru
          </Button>
          <Button
            variant="primary"
            className="w-full"
            onClick={() => navigate('/stok-barang/tambah-kategori')}
          >
            <span className="mr-2">🏷️</span>
            Tambah Kategori
          </Button>
        </div>
      </div>

      {/* Refresh Button */}
      <div className="flex flex-col sm:flex-row items-center justify-between bg-white rounded-lg shadow-md p-4">
        <Button onClick={handleRefresh} variant="outline">
          🔄 Refresh Data
        </Button>
        <p className="text-sm text-gray-500 mt-2 sm:mt-0">
          Terakhir diperbarui: {new Date().toLocaleString('id-ID')}
        </p>
      </div>
    </div>
  );
};

export default DashboardStokPage;

