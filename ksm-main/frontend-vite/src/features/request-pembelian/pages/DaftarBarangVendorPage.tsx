/**
 * Daftar Barang Vendor Page
 * Halaman untuk melihat daftar barang vendor dengan Tailwind CSS
 * Tab 1: Barang vendor penawaran berdasarkan request ID
 * Tab 2: Semua barang vendor penawaran
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetRequestPembelianListQuery } from '../store';
import { Button, Input, Table, Pagination, Tabs } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import AllVendorItemsTab from '../components/AllVendorItemsTab';
import RequestItemsModal from '../components/RequestItemsModal';

const DaftarBarangVendorPage: React.FC = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [selectedRequestId, setSelectedRequestId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: requestsData, isLoading, error, refetch } = useGetRequestPembelianListQuery({
    search,
    page: currentPage,
    per_page: itemsPerPage,
  });

  const requests = requestsData?.items || [];
  const pagination = requestsData?.pagination || { page: 1, per_page: 10, total: 0, pages: 1 };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleSelectRequest = (requestId: number) => {
    navigate(`/request-pembelian/upload-penawaran?requestId=${requestId}`);
  };

  const handleOpenItemsModal = (requestId: number) => {
    setSelectedRequestId(requestId);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedRequestId(null);
  };

  const columns = [
    {
      key: 'reference_id',
      label: 'Reference ID',
      render: (_value: any, item: any) => (
        <button
          onClick={() => handleOpenItemsModal(item.id)}
          className="font-mono text-sm font-semibold text-primary-600 hover:text-primary-700 hover:underline cursor-pointer transition-colors"
          title="Klik untuk melihat detail items"
        >
          {item.reference_id}
        </button>
      ),
    },
    {
      key: 'title',
      label: 'Title',
      render: (_value: any, item: any) => (
        <button
          onClick={() => handleOpenItemsModal(item.id)}
          className="font-medium text-gray-800 hover:text-primary-600 hover:underline cursor-pointer transition-colors text-left"
          title="Klik untuk melihat detail items"
        >
          {item.title}
        </button>
      ),
    },
    {
      key: 'items_count',
      label: 'Items',
      render: (_value: any, item: any) => (
        <span className="text-sm text-gray-600">{item.items_count || 0} items</span>
      ),
    },
    {
      key: 'vendor_penawarans_count',
      label: 'Penawarans',
      render: (_value: any, item: any) => (
        <span className="text-sm text-gray-600">{item.vendor_penawarans_count || 0}</span>
      ),
    },
    {
      key: 'created_at',
      label: 'Date',
      render: (_value: any, item: any) => formatDate(item.created_at),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_value: any, item: any) => (
        <Button
          variant="primary"
          size="sm"
          onClick={() => handleSelectRequest(item.id)}
        >
          Pilih Request
        </Button>
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
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Gagal memuat data request</p>
          <Button variant="primary" onClick={() => refetch()}>
            Coba Lagi
          </Button>
        </div>
      </div>
    );
  }

  // Tab 1 Content: Request List (existing content)
  const requestListContent = (
    <div className="space-y-6">
      {/* Search */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <Input
          type="text"
          placeholder="Cari request..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setCurrentPage(1);
          }}
          className="w-full"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={requests}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada request ditemukan"
        />
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, pagination.total)} dari {pagination.total} request
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

  const tabs = [
    {
      id: 'by-request',
      label: 'Barang Vendor per Request',
      content: requestListContent,
    },
    {
      id: 'all-items',
      label: 'Semua Barang Vendor',
      content: <AllVendorItemsTab />,
    },
  ];

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Daftar Barang Vendor</h1>
            <p className="text-gray-600">Lihat barang vendor penawaran berdasarkan request atau semua barang</p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/request-pembelian/daftar-request')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <Tabs tabs={tabs} defaultTab="by-request" />
      </div>

      {/* Request Items Modal */}
      <RequestItemsModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        requestId={selectedRequestId}
      />
    </div>
  );
};

export default DaftarBarangVendorPage;

