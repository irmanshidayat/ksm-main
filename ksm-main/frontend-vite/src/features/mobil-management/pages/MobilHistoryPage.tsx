/**
 * Mobil History Page
 * History reservasi mobil dengan filter & pagination dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useGetReservationsQuery, useGetMobilsQuery } from '../store';
import { Button, Input, Table, Pagination } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';

const MobilHistoryPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    mobil_id: searchParams.get('mobil_id') || '',
    search: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  const { data: reservationsData, isLoading } = useGetReservationsQuery({
    ...filters,
    page: currentPage,
    per_page: itemsPerPage,
  });
  const { data: mobilsData } = useGetMobilsQuery({ page: 1, per_page: 100 });

  const reservations = reservationsData?.items || [];
  const pagination = reservationsData?.pagination || { page: 1, per_page: 10, total: 0, pages: 1 };
  const mobils = mobilsData?.items || [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const columns = [
    {
      key: 'id',
      label: 'ID',
      render: (_value: any, item: any) => (
        <span className="font-mono text-sm">#{item.id}</span>
      ),
    },
    {
      key: 'mobil',
      label: 'Mobil',
      render: (_value: any, item: any) => (
        <span className="font-medium">{item.mobil?.nama || item.mobil?.nama_mobil || 'N/A'}</span>
      ),
    },
    {
      key: 'user',
      label: 'Pemohon',
      render: (_value: any, item: any) => (
        <span>{item.user?.username || 'N/A'}</span>
      ),
    },
    {
      key: 'dates',
      label: 'Tanggal',
      render: (_value: any, item: any) => {
        const start = item.tanggal_mulai || item.start_date;
        const end = item.tanggal_selesai || item.end_date;
        return (
          <span className="text-sm">
            {formatDate(start)} - {formatDate(end)}
          </span>
        );
      },
    },
    {
      key: 'keperluan',
      label: 'Keperluan',
      render: (_value: any, item: any) => (
        <span className="text-sm">{item.keperluan || item.purpose || '-'}</span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: any) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
          {item.status}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_value: any, item: any) => (
        <Link to={`/mobil/history?request_id=${item.id}`}>
          <Button variant="outline" size="sm">Detail</Button>
        </Link>
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

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📋 History Reservasi Mobil</h1>
            <p className="text-gray-600">Lihat riwayat semua reservasi mobil</p>
          </div>
          <Link to="/mobil/dashboard">
            <Button variant="outline">← Kembali</Button>
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <select
              value={filters.mobil_id}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, mobil_id: e.target.value }));
                setCurrentPage(1);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Semua Mobil</option>
              {mobils.map(mobil => (
                <option key={mobil.id} value={mobil.id}>
                  {mobil.nama || mobil.nama_mobil} - {mobil.plat_nomor}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={reservations}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada reservasi ditemukan"
        />
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, pagination.total)} dari {pagination.total} reservasi
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

export default MobilHistoryPage;

