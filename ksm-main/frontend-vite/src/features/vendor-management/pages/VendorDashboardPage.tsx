/**
 * Vendor Dashboard Page
 * Dashboard untuk vendor dengan Tailwind CSS
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetVendorDashboardQuery } from '../store';
import { useAppSelector } from '@/app/store/hooks';
import { Button } from '@/shared/components/ui';
import { useSweetAlert } from '@/shared/hooks';

const VendorDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const { isAuthenticated, loading: authLoading } = useAppSelector((state) => state.auth);
  
  // Skip query jika belum authenticated atau masih loading
  const { data: dashboardData, isLoading, error, refetch } = useGetVendorDashboardQuery(undefined, {
    skip: !isAuthenticated || authLoading,
  });

  // Handle 401 error - redirect to login
  useEffect(() => {
    if (error && 'status' in error && error.status === 401) {
      localStorage.removeItem('KSM_access_token');
      localStorage.removeItem('KSM_refresh_token');
      localStorage.removeItem('KSM_user');
      navigate('/login');
    }
  }, [error, navigate]);

  // SweetAlert loading
  useEffect(() => {
    if (isLoading) {
      sweetAlert.showLoading('Memuat...', 'Mengambil data dashboard vendor');
    } else {
      sweetAlert.hideLoading();
    }
  }, [isLoading, sweetAlert]);

  // Handle 404 vendor belum terdaftar -> arahkan ke registrasi vendor
  useEffect(() => {
    (async () => {
      if (error && 'status' in error && error.status === 404) {
        const goRegister = await sweetAlert.showConfirm(
          'Profil Vendor Belum Ada',
          'Silakan lakukan registrasi vendor terlebih dahulu. Buka halaman registrasi sekarang?'
        );
        if (goRegister) {
          navigate('/vendor/register');
        }
      } else if (error && 'status' in error && error.status !== 401) {
        // Error lain selain 401/404
        await sweetAlert.showError('Gagal Memuat', 'Terjadi kesalahan saat memuat dashboard vendor.');
      }
    })();
  }, [error, sweetAlert, navigate]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'submitted': return 'bg-yellow-100 text-yellow-800';
      case 'under_review': return 'bg-blue-100 text-blue-800';
      case 'selected': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'submitted': return 'Dikirim';
      case 'under_review': return 'Ditinjau';
      case 'selected': return 'Dipilih';
      case 'rejected': return 'Ditolak';
      default: return status;
    }
  };

  if (isLoading) return null;

  if (error) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Gagal memuat dashboard</p>
          <Button variant="primary" onClick={() => refetch()}>
            Coba Lagi
          </Button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">❌ Data Tidak Ditemukan</h3>
          <p className="text-yellow-600">Tidak dapat memuat dashboard</p>
        </div>
      </div>
    );
  }

  const { vendor, statistics, recent_penawaran = [] } = dashboardData;

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex-1">
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Dashboard Vendor</h1>
            <p className="text-gray-600 mb-2">Selamat datang, {vendor.company_name}</p>
            <div className="flex flex-wrap gap-4 text-sm text-gray-500">
              {vendor.email && (
                <span className="flex items-center gap-1">
                  <span>📧</span>
                  <span>{vendor.email}</span>
                </span>
              )}
              {vendor.phone && (
                <span className="flex items-center gap-1">
                  <span>📞</span>
                  <span>{vendor.phone}</span>
                </span>
              )}
              {vendor.vendor_type && (
                <span className="flex items-center gap-1">
                  <span>🏢</span>
                  <span className="capitalize">{vendor.vendor_type === 'internal' ? 'Internal' : 'Partner'}</span>
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate('/vendor/profile')}
            >
              👤 Profile
            </Button>
          </div>
        </div>
      </div>

      {/* Vendor Info Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Informasi Vendor</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Nama Perusahaan</p>
            <p className="font-medium text-gray-800">{vendor.company_name}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Contact Person</p>
            <p className="font-medium text-gray-800">{vendor.contact_person}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Kategori</p>
            <p className="font-medium text-gray-800 capitalize">
              {vendor.custom_category || vendor.vendor_category}
            </p>
          </div>
          {vendor.address && (
            <div className="md:col-span-2">
              <p className="text-sm text-gray-600 mb-1">Alamat</p>
              <p className="font-medium text-gray-800">{vendor.address}</p>
            </div>
          )}
          {vendor.business_license && (
            <div>
              <p className="text-sm text-gray-600 mb-1">Izin Usaha</p>
              <p className="font-medium text-gray-800">{vendor.business_license}</p>
            </div>
          )}
          {vendor.tax_id && (
            <div>
              <p className="text-sm text-gray-600 mb-1">NPWP</p>
              <p className="font-medium text-gray-800">{vendor.tax_id}</p>
            </div>
          )}
          {vendor.bank_account && (
            <div>
              <p className="text-sm text-gray-600 mb-1">Rekening Bank</p>
              <p className="font-medium text-gray-800">{vendor.bank_account}</p>
            </div>
          )}
          {vendor.business_model && (
            <div>
              <p className="text-sm text-gray-600 mb-1">Model Bisnis</p>
              <p className="font-medium text-gray-800 capitalize">
                {vendor.business_model === 'supplier' ? 'Pemasok' : 
                 vendor.business_model === 'reseller' ? 'Penjual Ulang' : 'Keduanya'}
              </p>
            </div>
          )}
          {vendor.registration_date && (
            <div>
              <p className="text-sm text-gray-600 mb-1">Tanggal Registrasi</p>
              <p className="font-medium text-gray-800">{formatDate(vendor.registration_date)}</p>
            </div>
          )}
          {vendor.approved_date && (
            <div>
              <p className="text-sm text-gray-600 mb-1">Tanggal Disetujui</p>
              <p className="font-medium text-gray-800">{formatDate(vendor.approved_date)}</p>
            </div>
          )}
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📊</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.total_penawaran}</h3>
              <p className="text-sm text-gray-600">Total Penawaran</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-4">
            <div className="text-4xl">⏳</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.pending_penawaran}</h3>
              <p className="text-sm text-gray-600">Menunggu Review</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-4">
            <div className="text-4xl">🔍</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.under_review_penawaran || 0}</h3>
              <p className="text-sm text-gray-600">Sedang Ditinjau</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-4">
            <div className="text-4xl">✅</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.approved_penawaran}</h3>
              <p className="text-sm text-gray-600">Disetujui</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-4">
            <div className="text-4xl">❌</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.rejected_penawaran || 0}</h3>
              <p className="text-sm text-gray-600">Ditolak</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📋</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.active_requests}</h3>
              <p className="text-sm text-gray-600">Request Aktif</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📈</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{statistics.success_rate}%</h3>
              <p className="text-sm text-gray-600">Tingkat Sukses</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📦</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{vendor.penawarans_count || 0}</h3>
              <p className="text-sm text-gray-600">Total Penawaran (DB)</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Menu Utama</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/vendor/requests')}
            className="p-6 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all text-left"
          >
            <div className="text-3xl mb-2">📋</div>
            <h3 className="font-semibold text-gray-800 mb-1">Request Pembelian</h3>
            <p className="text-sm text-gray-600 mb-2">Lihat dan upload penawaran</p>
            <div className="inline-block px-2 py-1 bg-primary-100 text-primary-700 text-xs rounded">
              {statistics.active_requests} aktif
            </div>
          </button>

          <button
            onClick={() => navigate('/vendor/history')}
            className="p-6 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all text-left"
          >
            <div className="text-3xl mb-2">📚</div>
            <h3 className="font-semibold text-gray-800 mb-1">Riwayat Penawaran</h3>
            <p className="text-sm text-gray-600">Lihat semua penawaran</p>
          </button>

          <button
            onClick={() => navigate('/vendor/templates')}
            className="p-6 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all text-left"
          >
            <div className="text-3xl mb-2">📄</div>
            <h3 className="font-semibold text-gray-800 mb-1">Download Template</h3>
            <p className="text-sm text-gray-600">Template dokumen</p>
          </button>
        </div>
      </div>

      {/* Recent Penawaran */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800">Penawaran Terbaru</h2>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/vendor/history')}
          >
            Lihat Semua
          </Button>
        </div>

        {recent_penawaran.length > 0 ? (
          <div className="space-y-4">
            {recent_penawaran.map((penawaran) => (
              <div
                key={penawaran.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-3">
                  <h4 className="font-semibold text-gray-800">#{penawaran.reference_id}</h4>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(penawaran.status)}`}>
                    {getStatusText(penawaran.status)}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                  <div>
                    <span className="text-sm text-gray-600">Tanggal Submit:</span>
                    <p className="text-sm font-medium text-gray-800">{formatDate(penawaran.submission_date)}</p>
                  </div>
                  {penawaran.total_quoted_price && (
                    <div>
                      <span className="text-sm text-gray-600">Harga:</span>
                      <p className="text-sm font-medium text-gray-800">{formatCurrency(penawaran.total_quoted_price)}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-sm text-gray-600">File:</span>
                    <p className="text-sm font-medium text-gray-800">{penawaran.files_count} file</p>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/vendor/requests/${penawaran.request_id}`)}
                >
                  Lihat Detail
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📝</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Belum Ada Penawaran</h3>
            <p className="text-gray-600 mb-4">Mulai dengan melihat request pembelian yang tersedia</p>
            <Button
              variant="primary"
              onClick={() => navigate('/vendor/requests')}
            >
              Lihat Request Pembelian
            </Button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white rounded-lg shadow-md p-4 text-center text-sm text-gray-600">
        <p>&copy; {new Date().getFullYear()} KSM Grup - Vendor Portal</p>
        <p className="mt-1">Status: {vendor.status} | Kategori: {vendor.vendor_category}</p>
      </div>
    </div>
  );
};

export default VendorDashboardPage;

