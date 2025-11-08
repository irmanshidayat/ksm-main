/**
 * Attendance Dashboard Page
 * Dashboard untuk melihat statistik dan status absensi dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useGetAttendanceDashboardQuery, useGetTodayStatusQuery, useGetAttendancesQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { ATTENDANCE_STATUS_LABELS, ATTENDANCE_STATUS_COLORS } from '../types';

const AttendanceDashboardPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  const { data: dashboardData, isLoading: loadingDashboard, error: errorDashboard } = useGetAttendanceDashboardQuery({
    date_from: dateRange.start,
    date_to: dateRange.end,
  });
  const { data: todayStatus, isLoading: loadingToday, error: errorToday } = useGetTodayStatusQuery();
  const { data: recentAttendance, isLoading: loadingRecent, error: errorRecent } = useGetAttendancesQuery({
    start_date: dateRange.start,
    end_date: dateRange.end,
    per_page: 10,
  });

  const stats = dashboardData?.stats;
  const recentRecords = recentAttendance?.items || [];

  const getStatusColor = (status: string) => {
    return ATTENDANCE_STATUS_COLORS[status as keyof typeof ATTENDANCE_STATUS_COLORS] || '#6B7280';
  };

  const getStatusLabel = (status: string) => {
    return ATTENDANCE_STATUS_LABELS[status as keyof typeof ATTENDANCE_STATUS_LABELS] || status;
  };

  if (loadingDashboard || loadingToday || loadingRecent) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (errorDashboard || errorToday || errorRecent) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">
            Error memuat data: {(errorDashboard || errorToday || errorRecent) instanceof Error 
              ? (errorDashboard || errorToday || errorRecent)?.message 
              : 'Terjadi kesalahan'}
          </p>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📊 Dashboard Absensi</h1>
            <p className="text-gray-600">Pantau statistik dan status absensi karyawan</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/attendance/clock-in">
              <Button variant="primary">⏰ Clock In/Out</Button>
            </Link>
            <Link to="/attendance/history">
              <Button variant="outline">📋 History</Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Today Status */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Status Hari Ini</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Clock In</div>
              <div className="text-2xl font-bold text-gray-800">
                {todayStatus?.has_clocked_in ? '✅' : '❌'}
              </div>
              {todayStatus?.clock_in_time && (
                <div className="text-xs text-gray-500 mt-1">
                  {new Date(todayStatus.clock_in_time).toLocaleTimeString('id-ID')}
                </div>
              )}
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Clock Out</div>
              <div className="text-2xl font-bold text-gray-800">
                {todayStatus?.has_clocked_out ? '✅' : '❌'}
              </div>
              {todayStatus?.clock_out_time && (
                <div className="text-xs text-gray-500 mt-1">
                  {new Date(todayStatus.clock_out_time).toLocaleTimeString('id-ID')}
                </div>
              )}
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Status</div>
              <div
                className="text-lg font-semibold"
                style={{ color: getStatusColor(todayStatus?.status || 'absent') }}
              >
                {getStatusLabel(todayStatus?.status || 'absent')}
              </div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Durasi Kerja</div>
              <div className="text-2xl font-bold text-gray-800">
                {todayStatus?.work_duration_hours?.toFixed(1) || 0}h
              </div>
            </div>
          </div>
        </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">✅</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{stats?.attendance?.present_days || 0}</h3>
              <p className="text-sm text-gray-600">Hadir</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">⏰</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{stats?.attendance?.late_days || 0}</h3>
              <p className="text-sm text-gray-600">Terlambat</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">❌</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{stats?.attendance?.absent_days || 0}</h3>
              <p className="text-sm text-gray-600">Tidak Hadir</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📊</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">
                {stats?.attendance?.attendance_rate?.toFixed(1) || 0}%
              </h3>
              <p className="text-sm text-gray-600">Attendance Rate</p>
            </div>
          </div>
        </div>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tanggal Mulai</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tanggal Akhir</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Recent Attendance */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800">📋 Absensi Terbaru</h2>
          <Link to="/attendance/history" className="text-primary-600 hover:text-primary-700 text-sm">
            Lihat Semua →
          </Link>
        </div>
        <div className="space-y-4">
          {recentRecords.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>Belum ada data absensi</p>
            </div>
          ) : (
            recentRecords.map(record => (
              <div key={record.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-800">
                      {record.user?.username || record.user_name || 'User'}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {new Date(record.clock_in).toLocaleDateString('id-ID', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Clock In: {new Date(record.clock_in).toLocaleTimeString('id-ID')}
                      {record.clock_out && ` | Clock Out: ${new Date(record.clock_out).toLocaleTimeString('id-ID')}`}
                    </p>
                  </div>
                  <span
                    className="px-3 py-1 rounded-full text-xs font-medium"
                    style={{
                      backgroundColor: `${getStatusColor(record.status)}20`,
                      color: getStatusColor(record.status),
                    }}
                  >
                    {getStatusLabel(record.status)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AttendanceDashboardPage;

