/**
 * Notifications Page
 * Halaman untuk melihat dan mengelola notifikasi dengan Tailwind CSS
 */

import React, { useState } from 'react';
import {
  useGetNotificationsQuery,
  useGetNotificationStatsQuery,
  useMarkAsReadMutation,
  useMarkAllAsReadMutation,
  useDeleteNotificationMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { Notification } from '../types';

const NotificationsPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');

  const { data: notifications, isLoading, refetch } = useGetNotificationsQuery({
    filter,
    priority: priorityFilter !== 'all' ? priorityFilter : undefined,
  });
  const { data: stats } = useGetNotificationStatsQuery();
  const [markAsRead] = useMarkAsReadMutation();
  const [markAllAsRead] = useMarkAllAsReadMutation();
  const [deleteNotification] = useDeleteNotificationMutation();

  const handleMarkAsRead = async (id: number) => {
    try {
      await markAsRead(id).unwrap();
      refetch();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal menandai notifikasi sebagai dibaca');
    }
  };

  const handleMarkAllAsRead = async () => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi',
      'Apakah Anda yakin ingin menandai semua notifikasi sebagai dibaca?',
      'info'
    );

    if (confirmed) {
      try {
        await markAllAsRead().unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Semua notifikasi ditandai sebagai dibaca');
        refetch();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menandai semua notifikasi');
      }
    }
  };

  const handleDelete = async (id: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus',
      'Apakah Anda yakin ingin menghapus notifikasi ini?',
      'warning'
    );

    if (confirmed) {
      try {
        await deleteNotification(id).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Notifikasi berhasil dihapus');
        refetch();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus notifikasi');
      }
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'urgent': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'high': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'normal': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'low': return 'bg-gray-100 text-gray-800 border-gray-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return 'Baru saja';
    if (minutes < 60) return `${minutes} menit yang lalu`;
    if (hours < 24) return `${hours} jam yang lalu`;
    if (days < 7) return `${days} hari yang lalu`;
    return date.toLocaleDateString('id-ID', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  if (isLoading) {
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🔔 Notifikasi</h1>
            <p className="text-gray-600">Lihat dan kelola notifikasi Anda</p>
          </div>
          {stats && stats.unread > 0 && (
            <Button
              variant="primary"
              onClick={handleMarkAllAsRead}
            >
              ✓ Tandai Semua Dibaca
            </Button>
          )}
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Total</div>
            <div className="text-2xl font-bold text-gray-800">{stats.total}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Belum Dibaca</div>
            <div className="text-2xl font-bold text-blue-600">{stats.unread}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Sudah Dibaca</div>
            <div className="text-2xl font-bold text-green-600">{stats.read}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Urgent</div>
            <div className="text-2xl font-bold text-orange-600">{stats.by_priority?.urgent || 0}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Critical</div>
            <div className="text-2xl font-bold text-red-600">{stats.by_priority?.critical || 0}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter Status</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as 'all' | 'unread' | 'read')}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua</option>
              <option value="unread">Belum Dibaca</option>
              <option value="read">Sudah Dibaca</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter Priority</label>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Priority</option>
              <option value="critical">Critical</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="normal">Normal</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-4">
        {notifications && notifications.length > 0 ? (
          notifications.map(notification => (
            <div
              key={notification.id}
              className={`bg-white rounded-lg shadow-md p-6 border-l-4 ${
                notification.is_read ? 'border-gray-300' : 'border-primary-500'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className={`font-semibold ${notification.is_read ? 'text-gray-600' : 'text-gray-800'}`}>
                      {notification.title}
                    </h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(notification.priority)}`}>
                      {notification.priority}
                    </span>
                    {notification.action_required && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
                        ⚠️ Action Required
                      </span>
                    )}
                  </div>
                  <p className={`text-sm mb-2 ${notification.is_read ? 'text-gray-500' : 'text-gray-700'}`}>
                    {notification.message}
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatTime(notification.created_at)}
                  </p>
                </div>
                <div className="flex gap-2 ml-4">
                  {!notification.is_read && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleMarkAsRead(notification.id)}
                    >
                      ✓ Baca
                    </Button>
                  )}
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDelete(notification.id)}
                  >
                    🗑️
                  </Button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">🔔</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Tidak Ada Notifikasi</h3>
            <p className="text-gray-600">Anda tidak memiliki notifikasi saat ini</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsPage;

