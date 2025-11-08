/**
 * Attendance Report Page
 * Laporan absensi dengan filter & export dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetAttendanceReportQuery, useGetAttendancesQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { ATTENDANCE_STATUS_LABELS, ATTENDANCE_STATUS_COLORS } from '../types';

const AttendanceReportPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });
  const [exportFormat, setExportFormat] = useState<'excel' | 'pdf'>('excel');

  const { data: reportData, isLoading: loadingReport, error: errorReport } = useGetAttendanceReportQuery({
    date_from: dateRange.start,
    date_to: dateRange.end,
    format: 'json',
  });
  const { data: attendanceData, isLoading: loadingAttendance, error: errorAttendance } = useGetAttendancesQuery({
    start_date: dateRange.start,
    end_date: dateRange.end,
    per_page: 100,
  });

  const records = attendanceData?.items || [];

  const handleExport = async () => {
    try {
      const token = localStorage.getItem('KSM_access_token');
      const url = `${import.meta.env.VITE_APP_API_URL || 'http://localhost:8000'}/api/attendance/report?date_from=${dateRange.start}&date_to=${dateRange.end}&format=${exportFormat}`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `laporan-absensi-${dateRange.start}-${dateRange.end}.${exportFormat === 'excel' ? 'xlsx' : 'pdf'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
        await sweetAlert.showSuccessAuto('Berhasil', 'Laporan berhasil diunduh');
      } else {
        await sweetAlert.showError('Gagal', 'Gagal mengunduh laporan');
      }
    } catch (error: any) {
      await sweetAlert.showError('Kesalahan', error?.message || 'Terjadi kesalahan saat mengunduh laporan');
    }
  };

  const getStatusColor = (status: string) => {
    return ATTENDANCE_STATUS_COLORS[status as keyof typeof ATTENDANCE_STATUS_COLORS] || '#6B7280';
  };

  const getStatusLabel = (status: string) => {
    return ATTENDANCE_STATUS_LABELS[status as keyof typeof ATTENDANCE_STATUS_LABELS] || status;
  };

  if (loadingReport || loadingAttendance) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (errorReport || errorAttendance) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">
            Error memuat data: {(errorReport || errorAttendance) instanceof Error 
              ? (errorReport || errorAttendance)?.message 
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📊 Laporan Absensi</h1>
            <p className="text-gray-600">Lihat dan export laporan absensi</p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/attendance/dashboard')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      {/* Filters & Export */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tanggal Mulai</label>
            <Input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tanggal Akhir</label>
            <Input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Format Export</label>
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as 'excel' | 'pdf')}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="excel">Excel (.xlsx)</option>
              <option value="pdf">PDF</option>
            </select>
          </div>
          <div className="flex items-end">
            <Button
              variant="primary"
              onClick={handleExport}
              className="w-full"
            >
              📥 Export Laporan
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {reportData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-sm text-gray-600 mb-1">Total Record</div>
            <div className="text-2xl font-bold text-gray-800">{records.length}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-sm text-gray-600 mb-1">Hadir</div>
            <div className="text-2xl font-bold text-green-600">
              {records.filter(r => r.status === 'present').length}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-sm text-gray-600 mb-1">Terlambat</div>
            <div className="text-2xl font-bold text-yellow-600">
              {records.filter(r => r.status === 'late').length}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-sm text-gray-600 mb-1">Tidak Hadir</div>
            <div className="text-2xl font-bold text-red-600">
              {records.filter(r => r.status === 'absent').length}
            </div>
          </div>
        </div>
      )}

      {/* Records List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Data Absensi</h2>
        <div className="space-y-3">
          {records.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>Tidak ada data absensi pada periode ini</p>
            </div>
          ) : (
            records.map(record => (
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

export default AttendanceReportPage;

