/**
 * Vendor Notifications Page
 * Halaman notifikasi vendor dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetVendorNotificationsQuery, useGetVendorNotificationStatsQuery, useMarkNotificationAsReadMutation, useMarkAllNotificationsAsReadMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';

const VendorNotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const { data: notificationsData, isLoading, error, refetch } = useGetVendorNotificationsQuery({
    limit: 100,
    unread_only: filter === 'unread'
  });
  const { data: stats } = useGetVendorNotificationStatsQuery();
  const [markAsRead] = useMarkNotificationAsReadMutation();
  const [markAllAsRead, { isLoading: markingAll }] = useMarkAllNotificationsAsReadMutation();

  // SweetAlert loading
  useEffect(() => {
    if (isLoading) {
      sweetAlert.showLoading('Memuat...', 'Mengambil data notifikasi');
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
        } else if (error.status !== 404) {
          await sweetAlert.showError('Gagal Memuat', 'Terjadi kesalahan saat memuat notifikasi.');
        }
      }
    })();
  }, [error, sweetAlert, navigate]);

  const notifications = notificationsData?.notifications || [];

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'deadline_warning': return '⚠️';
      case 'status_update': return '📢';
      case 'new_request': return '📋';
      case 'order_approved': return '✅';
      case 'order_status_update': return '🔄';
      case 'order_reminder': return '⏰';
      default: return '🔔';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'deadline_warning': return 'bg-red-50 border-red-200';
      case 'status_update': return 'bg-blue-50 border-blue-200';
      case 'new_request': return 'bg-green-50 border-green-200';
      case 'order_approved': return 'bg-green-50 border-green-200';
      case 'order_status_update': return 'bg-blue-50 border-blue-200';
      case 'order_reminder': return 'bg-yellow-50 border-yellow-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const handleMarkAsRead = async (notificationId: number) => {
    try {
      await markAsRead(notificationId).unwrap();
      refetch();
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead().unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Semua notifikasi ditandai sebagai sudah dibaca');
      refetch();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menandai semua notifikasi');
    }
  };

  const handleNotificationClick = (notification: any) => {
    if (!notification.is_read) {
      handleMarkAsRead(notification.id);
    }

    if (notification.related_request_id) {
      navigate(`/vendor/requests/${notification.related_request_id}`);
    } else if (notification.related_penawaran_id) {
      // Navigate to penawaran detail if needed
    }
  };

  if (isLoading) return null;

  if (error && 'status' in error && error.status !== 404) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Gagal memuat notifikasi</p>
          <Button variant="primary" onClick={() => refetch()}>
            Coba Lagi
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Notifikasi</h1>
            <p className="text-gray-600">Lihat semua notifikasi dan update terbaru</p>
          </div>
          {stats && stats.unread_notifications > 0 && (
            <Button
              variant="outline"
              onClick={handleMarkAllAsRead}
              isLoading={markingAll}
            >
              ✅ Tandai Semua Dibaca
            </Button>
          )}
        </div>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-4">
              <div className="text-4xl">🔔</div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800">{stats.total_notifications || 0}</h3>
                <p className="text-sm text-gray-600">Total Notifikasi</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-4">
              <div className="text-4xl">📬</div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800">{stats.unread_notifications || 0}</h3>
                <p className="text-sm text-gray-600">Belum Dibaca</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-4">
              <div className="text-4xl">⚠️</div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800">{stats.deadline_warnings || 0}</h3>
                <p className="text-sm text-gray-600">Peringatan Deadline</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-4">
              <div className="text-4xl">📋</div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800">{stats.new_requests || 0}</h3>
                <p className="text-sm text-gray-600">Request Baru</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Semua ({stats?.total_notifications || 0})
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === 'unread'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Belum Dibaca ({stats?.unread_notifications || 0})
          </button>
        </div>
      </div>

      {/* Notifications List */}
      {notifications.length > 0 ? (
        <div className="space-y-4">
          {notifications.map((notification: any) => (
            <div
              key={notification.id}
              onClick={() => handleNotificationClick(notification)}
              className={`bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-all border-l-4 ${
                notification.is_read ? 'border-gray-300' : 'border-primary-600'
              } ${getTypeColor(notification.type)}`}
            >
              <div className="flex items-start gap-4">
                <div className="text-3xl">{getTypeIcon(notification.type)}</div>
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <h3 className={`font-semibold ${notification.is_read ? 'text-gray-700' : 'text-gray-900'}`}>
                      {notification.title}
                    </h3>
                    {!notification.is_read && (
                      <span className="px-2 py-1 bg-primary-600 text-white text-xs rounded-full">
                        Baru
                      </span>
                    )}
                  </div>
                  <p className={`text-sm mb-3 ${notification.is_read ? 'text-gray-600' : 'text-gray-800'}`}>
                    {notification.message}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">{formatDate(notification.created_at)}</span>
                    {!notification.is_read && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleMarkAsRead(notification.id);
                        }}
                      >
                        Tandai Dibaca
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <div className="text-6xl mb-4">🔔</div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Tidak Ada Notifikasi</h3>
          <p className="text-gray-600">
            {filter === 'unread' ? 'Tidak ada notifikasi yang belum dibaca' : 'Belum ada notifikasi'}
          </p>
        </div>
      )}
    </div>
  );
};

export default VendorNotificationsPage;

