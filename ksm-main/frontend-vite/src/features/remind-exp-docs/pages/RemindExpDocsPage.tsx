/**
 * Remind Exp Docs Page
 * Halaman untuk mengelola dokumen yang akan expired dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import {
  useGetDocumentsQuery,
  useGetStatisticsQuery,
  useCreateDocumentMutation,
  useUpdateDocumentMutation,
  useDeleteDocumentMutation,
  useExportDocumentsMutation,
  useImportDocumentsMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table, Pagination } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { RemindExpDoc, CreateRemindExpDocRequest } from '../types';

const RemindExpDocsPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    document_type: '',
    sort_by: 'expiry_date',
    sort_order: 'asc' as 'asc' | 'desc',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showImportExport, setShowImportExport] = useState(false);
  const [editingDocument, setEditingDocument] = useState<RemindExpDoc | null>(null);
  const [formData, setFormData] = useState<CreateRemindExpDocRequest>({
    document_name: '',
    document_number: '',
    document_type: '',
    issuer: '',
    expiry_date: '',
    reminder_days_before: 30,
    description: '',
  });

  const { data: documentsData, isLoading, refetch } = useGetDocumentsQuery({
    ...filters,
    page: currentPage,
    per_page: itemsPerPage,
  });
  const { data: statistics, refetch: refetchStats } = useGetStatisticsQuery();
  const [createDocument] = useCreateDocumentMutation();
  const [updateDocument] = useUpdateDocumentMutation();
  const [deleteDocument] = useDeleteDocumentMutation();
  const [exportDocuments] = useExportDocumentsMutation();
  const [importDocuments, { isLoading: importing }] = useImportDocumentsMutation();

  const documents = documentsData?.items || [];
  const pagination = documentsData?.pagination || { page: 1, per_page: 10, total: 0, pages: 1 };

  const handleSaveDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.document_name || !formData.expiry_date) {
      await sweetAlert.showError('Error', 'Nama dokumen dan tanggal expired wajib diisi');
      return;
    }

    try {
      if (editingDocument) {
        await updateDocument({ id: editingDocument.id, data: formData }).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Dokumen berhasil diupdate');
      } else {
        await createDocument(formData).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Dokumen berhasil dibuat');
      }
      setShowCreateForm(false);
      setEditingDocument(null);
      setFormData({
        document_name: '',
        document_number: '',
        document_type: '',
        issuer: '',
        expiry_date: '',
        reminder_days_before: 30,
        description: '',
      });
      refetch();
      refetchStats();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal menyimpan dokumen');
    }
  };

  const handleDeleteDocument = async (id: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus',
      'Apakah Anda yakin ingin menghapus dokumen ini?',
      'warning'
    );

    if (confirmed) {
      try {
        await deleteDocument(id).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Dokumen berhasil dihapus');
        refetch();
        refetchStats();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus dokumen');
      }
    }
  };

  const handleEdit = (doc: RemindExpDoc) => {
    setEditingDocument(doc);
    setFormData({
      document_name: doc.document_name,
      document_number: doc.document_number || '',
      document_type: doc.document_type || '',
      issuer: doc.issuer || '',
      expiry_date: doc.expiry_date,
      reminder_days_before: doc.reminder_days_before,
      description: doc.description || '',
    });
    setShowCreateForm(true);
  };

  const handleExport = async () => {
    try {
      const result = await exportDocuments(filters).unwrap();
      const a = document.createElement('a');
      a.href = result.download_url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(result.download_url);
      document.body.removeChild(a);
      await sweetAlert.showSuccessAuto('Berhasil', 'Dokumen berhasil diexport');
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal export dokumen');
    }
  };

  const handleImport = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const result = await importDocuments(formData).unwrap();
      await sweetAlert.showSuccessAuto(
        'Berhasil',
        `${result.imported} dokumen berhasil diimport${result.errors.length > 0 ? `. ${result.errors.length} error.` : ''}`
      );
      refetch();
      refetchStats();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal import dokumen');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'expired': return 'bg-red-100 text-red-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      active: 'Aktif',
      expired: 'Expired',
      inactive: 'Tidak Aktif',
    };
    return labels[status] || status;
  };

  const isExpiringSoon = (expiryDate: string, daysBefore: number) => {
    const expiry = new Date(expiryDate);
    const today = new Date();
    const diffTime = expiry.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays <= daysBefore && diffDays >= 0;
  };

  const isExpired = (expiryDate: string) => {
    return new Date(expiryDate) < new Date();
  };

  const columns = [
    {
      key: 'document_name',
      label: 'Nama Dokumen',
      render: (_value: any, item: RemindExpDoc) => (
        <span className="font-medium">{item.document_name}</span>
      ),
    },
    {
      key: 'document_type',
      label: 'Tipe',
      render: (_value: any, item: RemindExpDoc) => item.document_type || '-',
    },
    {
      key: 'expiry_date',
      label: 'Tanggal Expired',
      render: (_value: any, item: RemindExpDoc) => {
        const date = new Date(item.expiry_date);
        const isExp = isExpired(item.expiry_date);
        const isSoon = isExpiringSoon(item.expiry_date, item.reminder_days_before);
        return (
          <span className={isExp ? 'text-red-600 font-semibold' : isSoon ? 'text-yellow-600 font-semibold' : ''}>
            {date.toLocaleDateString('id-ID', { year: 'numeric', month: 'long', day: 'numeric' })}
            {isExp && ' ⚠️ Expired'}
            {isSoon && !isExp && ' ⏰ Expiring Soon'}
          </span>
        );
      },
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: RemindExpDoc) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
          {getStatusLabel(item.status)}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: RemindExpDoc) => (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleEdit(item)}
          >
            ✏️ Edit
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => handleDeleteDocument(item.id)}
          >
            🗑️ Hapus
          </Button>
        </div>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📄 Remind Exp Docs</h1>
            <p className="text-gray-600">Kelola dokumen dan sertifikasi yang akan expired</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setShowImportExport(true)}
            >
              📥 Import/Export
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setShowCreateForm(true);
                setEditingDocument(null);
                setFormData({
                  document_name: '',
                  document_number: '',
                  document_type: '',
                  issuer: '',
                  expiry_date: '',
                  reminder_days_before: 30,
                  description: '',
                });
              }}
            >
              ➕ Tambah Dokumen
            </Button>
          </div>
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Total</div>
            <div className="text-2xl font-bold text-gray-800">{statistics.total_documents}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Aktif</div>
            <div className="text-2xl font-bold text-green-600">{statistics.active_documents}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Expired</div>
            <div className="text-2xl font-bold text-red-600">{statistics.expired_documents}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Tidak Aktif</div>
            <div className="text-2xl font-bold text-gray-600">{statistics.inactive_documents}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Expiring 30d</div>
            <div className="text-2xl font-bold text-yellow-600">{statistics.expiring_30_days}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Expiring 7d</div>
            <div className="text-2xl font-bold text-orange-600">{statistics.expiring_7_days}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Already Expired</div>
            <div className="text-2xl font-bold text-red-600">{statistics.already_expired}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <Input
              type="text"
              placeholder="Cari dokumen..."
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
              <option value="active">Aktif</option>
              <option value="expired">Expired</option>
              <option value="inactive">Tidak Aktif</option>
            </select>
          </div>
          <div>
            <Input
              type="text"
              placeholder="Tipe dokumen..."
              value={filters.document_type}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, document_type: e.target.value }));
                setCurrentPage(1);
              }}
            />
          </div>
          <div>
            <select
              value={filters.sort_order}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, sort_order: e.target.value as 'asc' | 'desc' }));
                setCurrentPage(1);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="asc">Sort: A-Z</option>
              <option value="desc">Sort: Z-A</option>
            </select>
          </div>
        </div>
      </div>

      {/* Create/Edit Form Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">
                  {editingDocument ? 'Edit Dokumen' : 'Tambah Dokumen'}
                </h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowCreateForm(false);
                    setEditingDocument(null);
                    setFormData({
                      document_name: '',
                      document_number: '',
                      document_type: '',
                      issuer: '',
                      expiry_date: '',
                      reminder_days_before: 30,
                      description: '',
                    });
                  }}
                >
                  ✕
                </Button>
              </div>
              <form onSubmit={handleSaveDocument} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Nama Dokumen *</label>
                  <Input
                    type="text"
                    value={formData.document_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, document_name: e.target.value }))}
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Nomor Dokumen</label>
                    <Input
                      type="text"
                      value={formData.document_number}
                      onChange={(e) => setFormData(prev => ({ ...prev, document_number: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Tipe Dokumen</label>
                    <Input
                      type="text"
                      value={formData.document_type}
                      onChange={(e) => setFormData(prev => ({ ...prev, document_type: e.target.value }))}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Issuer</label>
                  <Input
                    type="text"
                    value={formData.issuer}
                    onChange={(e) => setFormData(prev => ({ ...prev, issuer: e.target.value }))}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Tanggal Expired *</label>
                    <Input
                      type="date"
                      value={formData.expiry_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, expiry_date: e.target.value }))}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Reminder (Hari Sebelum)</label>
                    <Input
                      type="number"
                      value={formData.reminder_days_before}
                      onChange={(e) => setFormData(prev => ({ ...prev, reminder_days_before: parseInt(e.target.value) || 30 }))}
                      min="1"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                  />
                </div>
                <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowCreateForm(false);
                      setEditingDocument(null);
                      setFormData({
                        document_name: '',
                        document_number: '',
                        document_type: '',
                        issuer: '',
                        expiry_date: '',
                        reminder_days_before: 30,
                        description: '',
                      });
                    }}
                  >
                    Batal
                  </Button>
                  <Button type="submit" variant="primary">
                    {editingDocument ? 'Update' : 'Simpan'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Import/Export Modal */}
      {showImportExport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Import/Export</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowImportExport(false)}
                >
                  ✕
                </Button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Export Dokumen</label>
                  <Button
                    variant="primary"
                    onClick={handleExport}
                    className="w-full"
                  >
                    📥 Export Excel
                  </Button>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Import Dokumen</label>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        handleImport(file);
                        setShowImportExport(false);
                      }
                    }}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={documents}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada dokumen ditemukan"
        />
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, pagination.total)} dari {pagination.total} dokumen
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

export default RemindExpDocsPage;

