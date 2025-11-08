/**
 * Attendance History Page
 * History absensi dengan filter & pagination dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useGetAttendancesQuery } from '../store';
import { Button, Input, Table, Pagination } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { ATTENDANCE_STATUS_LABELS, ATTENDANCE_STATUS_COLORS } from '../types';

const AttendanceHistoryPage: React.FC = () => {
  const [filters, setFilters] = useState({
    start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    status: '',
    search: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  const { data: attendanceData, isLoading, error } = useGetAttendancesQuery({
    ...filters,
    page: currentPage,
    per_page: itemsPerPage,
  });

  const records = attendanceData?.items || [];
  const pagination = {
    page: attendanceData?.page || 1,
    per_page: attendanceData?.per_page || 10,
    total: attendanceData?.total || 0,
    pages: attendanceData?.pages || 1
  };

  const getStatusColor = (status: string) => {
    return ATTENDANCE_STATUS_COLORS[status as keyof typeof ATTENDANCE_STATUS_COLORS] || '#6B7280';
  };

  const getStatusLabel = (status: string) => {
    return ATTENDANCE_STATUS_LABELS[status as keyof typeof ATTENDANCE_STATUS_LABELS] || status;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('id-ID', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const columns = [
    {
      key: 'date',
      label: 'Tanggal',
      render: (_value: any, item: any) => formatDate(item.clock_in),
    },
    {
      key: 'user',
      label: 'User',
      render: (_value: any, item: any) => (
        <span className="font-medium">{item.user?.username || item.user_name || 'N/A'}</span>
      ),
    },
    {
      key: 'clock_in',
      label: 'Clock In',
      render: (_value: any, item: any) => formatTime(item.clock_in),
    },
    {
      key: 'clock_out',
      label: 'Clock Out',
      render: (_value: any, item: any) => item.clock_out ? formatTime(item.clock_out) : '-',
    },
    {
      key: 'duration',
      label: 'Durasi',
      render: (_value: any, item: any) => {
        if (item.work_duration_hours) {
          return `${item.work_duration_hours.toFixed(1)}h`;
        }
        return '-';
      },
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: any) => (
        <span
          className="px-2 py-1 rounded-full text-xs font-medium"
          style={{
            backgroundColor: `${getStatusColor(item.status)}20`,
            color: getStatusColor(item.status),
          }}
        >
          {getStatusLabel(item.status)}
        </span>
      ),
    },
  ];

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
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">
            Error memuat data: {error instanceof Error ? error.message : 'Terjadi kesalahan'}
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📋 History Absensi</h1>
            <p className="text-gray-600">Lihat riwayat absensi karyawan</p>
          </div>
          <Link to="/attendance/dashboard">
            <Button variant="outline">← Kembali</Button>
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <Input
              type="date"
              value={filters.start_date}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, start_date: e.target.value }));
                setCurrentPage(1);
              }}
            />
          </div>
          <div>
            <Input
              type="date"
              value={filters.end_date}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, end_date: e.target.value }));
                setCurrentPage(1);
              }}
            />
          </div>
          <div>
            <select
              value={filters.status}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, status: e.target.value }));
                setCurrentPage(1);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Semua Status</option>
              <option value="present">Hadir</option>
              <option value="late">Terlambat</option>
              <option value="absent">Tidak Hadir</option>
              <option value="half_day">Setengah Hari</option>
            </select>
          </div>
          <div>
            <Input
              type="text"
              placeholder="Cari..."
              value={filters.search}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, search: e.target.value }));
                setCurrentPage(1);
              }}
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={records}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada data absensi ditemukan"
        />
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, pagination.total)} dari {pagination.total} record
            </div>
            <Pagination
              currentPage={currentPage}
              totalPages={pagination.pages}
              onPageChange={(page) => {
                setCurrentPage(page);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendanceHistoryPage;

