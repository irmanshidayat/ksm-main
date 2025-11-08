/**
 * Leave Request Page
 * Form untuk pengajuan izin dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateLeaveRequestMutation, useGetLeaveRequestsQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { LEAVE_TYPE_LABELS, LEAVE_STATUS_LABELS } from '../types';

const LeaveRequestPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [createLeaveRequest, { isLoading }] = useCreateLeaveRequestMutation();
  const { data: myRequests, isLoading: loadingRequests } = useGetLeaveRequestsQuery({ page: 1, per_page: 10 });

  const [formData, setFormData] = useState({
    leave_type: 'sick' as const,
    start_date: '',
    end_date: '',
    reason: '',
    emergency_contact: '',
    emergency_phone: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.start_date || !formData.end_date || !formData.reason) {
      await sweetAlert.showError('Error', 'Mohon lengkapi semua field yang wajib diisi');
      return;
    }

    if (new Date(formData.start_date) > new Date(formData.end_date)) {
      await sweetAlert.showError('Error', 'Tanggal mulai tidak boleh lebih besar dari tanggal selesai');
      return;
    }

    try {
      await createLeaveRequest(formData).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Pengajuan izin berhasil dibuat');
      navigate('/attendance/dashboard');
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal membuat pengajuan izin');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loadingRequests) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const myRequestsList = myRequests?.items || [];

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📝 Pengajuan Izin</h1>
            <p className="text-gray-600">Ajukan izin atau cuti</p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/attendance/dashboard')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Form Pengajuan</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipe Izin *
              </label>
              <select
                name="leave_type"
                value={formData.leave_type}
                onChange={handleInputChange}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                {Object.entries(LEAVE_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tanggal Mulai *
              </label>
              <Input
                type="date"
                name="start_date"
                value={formData.start_date}
                onChange={handleInputChange}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tanggal Selesai *
              </label>
              <Input
                type="date"
                name="end_date"
                value={formData.end_date}
                onChange={handleInputChange}
                min={formData.start_date}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Alasan *
              </label>
              <textarea
                name="reason"
                value={formData.reason}
                onChange={handleInputChange}
                rows={4}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                placeholder="Jelaskan alasan izin..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Kontak Darurat
              </label>
              <Input
                type="text"
                name="emergency_contact"
                value={formData.emergency_contact}
                onChange={handleInputChange}
                placeholder="Nama kontak darurat"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nomor Telepon Darurat
              </label>
              <Input
                type="tel"
                name="emergency_phone"
                value={formData.emergency_phone}
                onChange={handleInputChange}
                placeholder="08xxxxxxxxxx"
              />
            </div>

            <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/attendance/dashboard')}
                disabled={isLoading}
              >
                Batal
              </Button>
              <Button
                type="submit"
                variant="primary"
                isLoading={isLoading}
              >
                Ajukan Izin
              </Button>
            </div>
          </form>
        </div>

        {/* My Requests */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Pengajuan Saya</h2>
          <div className="space-y-4">
            {myRequestsList.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>Belum ada pengajuan izin</p>
              </div>
            ) : (
              myRequestsList.map(request => (
                <div key={request.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-800">
                        {LEAVE_TYPE_LABELS[request.leave_type]}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {new Date(request.start_date).toLocaleDateString('id-ID')} - {new Date(request.end_date).toLocaleDateString('id-ID')}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                      {LEAVE_STATUS_LABELS[request.status]}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">{request.reason}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeaveRequestPage;

