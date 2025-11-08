/**
 * Mobil Dashboard Page
 * Dashboard untuk melihat daftar mobil dan recent requests dengan Tailwind CSS
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useGetMobilsQuery, useGetMyReservationsQuery, useDeleteMobilMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';

const MobilDashboardPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const { data: mobilsData, isLoading: loadingMobils, refetch: refetchMobils } = useGetMobilsQuery({ page: 1, per_page: 100 });
  const { data: requestsData, isLoading: loadingRequests } = useGetMyReservationsQuery({ page: 1, per_page: 5 });
  const [deleteMobil] = useDeleteMobilMutation();

  const mobils = mobilsData?.items || [];
  const recentRequests = requestsData?.items || [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'maintenance': return 'bg-yellow-100 text-yellow-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return 'Aktif';
      case 'maintenance': return 'Maintenance';
      case 'inactive': return 'Tidak Aktif';
      default: return 'Unknown';
    }
  };

  const handleDelete = async (mobilId: number, mobilName: string) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus Mobil',
      `Apakah Anda yakin ingin menghapus mobil ${mobilName}?`,
      'warning'
    );

    if (confirmed) {
      try {
        await deleteMobil(mobilId).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Mobil berhasil dihapus');
        refetchMobils();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus mobil');
      }
    }
  };

  if (loadingMobils || loadingRequests) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🚗 Dashboard Mobil</h1>
            <p className="text-gray-600">Kelola dan pantau penggunaan mobil perusahaan</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/mobil/add">
              <Button variant="primary">🚗 Tambah Mobil</Button>
            </Link>
            <Link to="/mobil/request">
              <Button variant="primary">+ Request Baru</Button>
            </Link>
            <Link to="/mobil/calendar">
              <Button variant="outline">📅 Lihat Kalender</Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">🚗</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{mobils.length}</h3>
              <p className="text-sm text-gray-600">Total Mobil</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">✅</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">
                {mobils.filter(m => m.status === 'active').length}
              </h3>
              <p className="text-sm text-gray-600">Mobil Aktif</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">🔧</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">
                {mobils.filter(m => m.status === 'maintenance').length}
              </h3>
              <p className="text-sm text-gray-600">Dalam Maintenance</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📋</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{recentRequests.length}</h3>
              <p className="text-sm text-gray-600">Request Terbaru</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mobil List */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">📋 Daftar Mobil</h2>
            <Link to="/mobil/calendar" className="text-primary-600 hover:text-primary-700 text-sm">
              Lihat Semua →
            </Link>
          </div>
          <div className="space-y-4">
            {mobils.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>Belum ada mobil terdaftar</p>
                <Link to="/mobil/add" className="mt-4 inline-block">
                  <Button variant="primary">Tambah Mobil</Button>
                </Link>
              </div>
            ) : (
              mobils.map(mobil => (
                <div key={mobil.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-800">
                        {mobil.nama || mobil.nama_mobil}
                        {mobil.is_backup && (
                          <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                            🔄 Backup
                          </span>
                        )}
                      </h3>
                      <p className="text-sm text-gray-600">Plat: {mobil.plat_nomor}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(mobil.status)}`}>
                      {getStatusText(mobil.status)}
                    </span>
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Link to={`/mobil/request?mobil_id=${mobil.id}`}>
                      <Button variant="primary" size="sm">Request</Button>
                    </Link>
                    <Link to={`/mobil/calendar?mobil_id=${mobil.id}`}>
                      <Button variant="outline" size="sm">Lihat Jadwal</Button>
                    </Link>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(mobil.id, mobil.nama || mobil.nama_mobil || 'Mobil')}
                    >
                      🗑️ Hapus
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Requests */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">📝 Request Terbaru</h2>
            <Link to="/mobil/history" className="text-primary-600 hover:text-primary-700 text-sm">
              Lihat Semua →
            </Link>
          </div>
          <div className="space-y-4">
            {recentRequests.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>Belum ada request mobil</p>
                <Link to="/mobil/request" className="mt-4 inline-block">
                  <Button variant="primary">Buat Request Pertama</Button>
                </Link>
              </div>
            ) : (
              recentRequests.map(request => (
                <div key={request.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-gray-800">Request #{request.id}</h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                      {getStatusText(request.status)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>
                      <strong>Tanggal:</strong>{' '}
                      {new Date(request.tanggal_mulai || request.start_date).toLocaleDateString('id-ID')} -{' '}
                      {new Date(request.tanggal_selesai || request.end_date).toLocaleDateString('id-ID')}
                    </p>
                    <p>
                      <strong>Keperluan:</strong> {request.keperluan || request.purpose || 'Tidak diisi'}
                    </p>
                    <p>
                      <strong>Pemohon:</strong> {request.user?.username || 'User tidak ditemukan'}
                    </p>
                    {request.is_recurring && (
                      <p>
                        <strong>Recurring:</strong>{' '}
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                          🔄 Ya
                        </span>
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Link to={`/mobil/history?request_id=${request.id}`}>
                      <Button variant="outline" size="sm">Detail</Button>
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobilDashboardPage;

