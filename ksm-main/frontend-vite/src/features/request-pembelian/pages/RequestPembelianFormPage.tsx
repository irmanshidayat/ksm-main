/**
 * Request Pembelian Form Page
 * Halaman form untuk create/edit request pembelian dengan Tailwind CSS
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useGetRequestPembelianByIdQuery, useCreateRequestPembelianMutation, useUpdateRequestPembelianMutation, useGetRequestAttachmentsQuery } from '../store';
import type { RequestPembelianItem, EmailAttachment } from '../types';
import { useSweetAlert } from '@/shared/hooks';
import { useAuth } from '@/features/auth/hooks';
import { Button, Input, NumberInput } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { ENV } from '@/core/config/env';
import Swal from 'sweetalert2';

interface RequestItem {
  id?: number;
  nama_barang: string;
  quantity: number;
  satuan: string;
  spesifikasi: string;
  estimated_price?: number;
}

const RequestPembelianFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const sweetAlert = useSweetAlert();
  const { user } = useAuth();
  const isEditMode = !!id;
  const requestId = id ? parseInt(id) : 0;

  const { data: requestData, isLoading: loadingRequest } = useGetRequestPembelianByIdQuery(requestId, { skip: !isEditMode || !requestId });
  const { data: existingAttachments = [], isLoading: loadingAttachments, error: attachmentsError } = useGetRequestAttachmentsQuery(requestId, { skip: !isEditMode || !requestId });
  const [createRequest, { isLoading: creating }] = useCreateRequestPembelianMutation();
  const [updateRequest, { isLoading: updating }] = useUpdateRequestPembelianMutation();

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    required_date: '',
    total_budget: 0,
  });

  const [items, setItems] = useState<RequestItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load request data for edit mode
  useEffect(() => {
    if (isEditMode && requestData) {
      setFormData({
        title: requestData.title,
        description: requestData.description || '',
        priority: requestData.priority,
        required_date: requestData.required_date ? requestData.required_date.split('T')[0] : '',
        total_budget: requestData.total_budget || 0,
      });
      
      // Load existing items from requestData
      if (requestData.items && requestData.items.length > 0) {
        const existingItems: RequestItem[] = requestData.items.map((item: RequestPembelianItem) => ({
          id: item.id,
          nama_barang: item.nama_barang || '',
          quantity: item.quantity || 1,
          satuan: item.satuan || 'pcs',
          spesifikasi: item.specifications || item.spesifikasi || '',
          estimated_price: item.unit_price || item.estimated_price || 0,
        }));
        setItems(existingItems);
      }
      
      // Reset new files when loading edit data (existing files shown separately)
      setSelectedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } else if (!isEditMode) {
      // Reset everything when in create mode
      setItems([]);
      setSelectedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [isEditMode, requestData]);

  // Debug: Log attachments data
  useEffect(() => {
    if (isEditMode && requestId) {
      console.log('🔍 Debug Attachments:', {
        requestId,
        isEditMode,
        loadingAttachments,
        attachmentsError,
        existingAttachments,
        attachmentsCount: existingAttachments?.length || 0
      });
    }
  }, [isEditMode, requestId, loadingAttachments, attachmentsError, existingAttachments]);

  const addItem = () => {
    setItems(prev => [...prev, {
      nama_barang: '',
      quantity: 1,
      satuan: 'pcs',
      spesifikasi: '',
      estimated_price: 0,
    }]);
  };

  const updateItem = (index: number, field: keyof RequestItem, value: any) => {
    setItems(prev => {
      const updated = prev.map((item, i) => {
        if (i === index) {
          return { ...item, [field]: value };
        }
        return item;
      });
      
      // Recalculate total budget after updating items
      if (field === 'quantity' || field === 'estimated_price') {
        const totalBudget = updated.reduce((sum, item) => 
          sum + (item.quantity * (item.estimated_price || 0)), 0
        );
        setFormData(prevForm => ({ ...prevForm, total_budget: totalBudget }));
      }
      
      return updated;
    });
  };

  const removeItem = (index: number) => {
    setItems(prev => {
      const updated = prev.filter((_, i) => i !== index);
      const totalBudget = updated.reduce((sum, item) => 
        sum + (item.quantity * (item.estimated_price || 0)), 0
      );
      setFormData(prevForm => ({ ...prevForm, total_budget: totalBudget }));
      return updated;
    });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    // Validate files
    const allowedExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.txt', '.csv'];
    const maxSizeMB = 50;
    const maxSizeBytes = maxSizeMB * 1024 * 1024;

    const validFiles: File[] = [];
    const errors: string[] = [];

    files.forEach(file => {
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!allowedExtensions.includes(fileExtension)) {
        errors.push(`${file.name}: Format file tidak didukung`);
        return;
      }
      if (file.size > maxSizeBytes) {
        errors.push(`${file.name}: Ukuran file melebihi ${maxSizeMB}MB`);
        return;
      }
      validFiles.push(file);
    });

    if (errors.length > 0) {
      sweetAlert.showError('Error Validasi File', errors.join('\n'));
    }

    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
    }

    // Reset input to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.title.trim()) {
      setError('Title harus diisi');
      return;
    }

    if (items.length === 0) {
      setError('Minimal harus ada 1 item');
      return;
    }

    const hasInvalidItems = items.some(item => !item.nama_barang.trim());
    if (hasInvalidItems) {
      setError('Semua item harus memiliki nama barang');
      return;
    }

    try {
      Swal.fire({
        title: isEditMode ? 'Memperbarui...' : 'Membuat...',
        text: isEditMode ? 'Sedang memperbarui request...' : 'Sedang membuat request...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const requestPayload = {
        ...formData,
        user_id: user?.id || 0,
        department_id: (user as any)?.department_id || 1, // Default to 1 if not available
        items: items.map(item => ({
          nama_barang: item.nama_barang,
          quantity: item.quantity,
          satuan: item.satuan,
          spesifikasi: item.spesifikasi,
          estimated_price: item.estimated_price,
        })),
      };

      if (isEditMode) {
        await updateRequest({ id: requestId, data: requestPayload }).unwrap();
      } else {
        await createRequest(requestPayload).unwrap();
      }

      Swal.close();
      await sweetAlert.showSuccessAuto(
        'Berhasil',
        isEditMode ? 'Request berhasil diperbarui' : 'Request berhasil dibuat'
      );
      navigate('/request-pembelian/daftar-request');
    } catch (error: any) {
      Swal.close();
      setError(error?.data?.message || 'Terjadi kesalahan saat menyimpan request');
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menyimpan request');
    }
  };

  if (loadingRequest) {
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">
              {isEditMode ? 'Edit Request Pembelian' : 'Buat Request Pembelian Baru'}
            </h1>
            <p className="text-gray-600">Isi form untuk {isEditMode ? 'memperbarui' : 'membuat'} request pembelian</p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/request-pembelian/daftar-request')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Basic Info */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Informasi Request</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title <span className="text-red-500">*</span>
              </label>
              <Input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Masukkan title request"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={4}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                placeholder="Masukkan description request"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Required Date</label>
              <Input
                type="date"
                value={formData.required_date}
                onChange={(e) => setFormData(prev => ({ ...prev, required_date: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Total Budget</label>
              <NumberInput
                value={formData.total_budget}
                onChange={(value) => setFormData(prev => ({ ...prev, total_budget: typeof value === 'number' ? value : parseFloat(value) || 0 }))}
                placeholder="0"
                min="0"
                step="0.01"
              />
            </div>
          </div>
        </div>

        {/* Existing Items (Read-only) - Only show in edit mode */}
        {isEditMode && requestData?.items && requestData.items.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Items yang Sudah Ada</h2>
            <div className="space-y-3">
              {requestData.items.map((item: RequestPembelianItem, index: number) => (
                <div key={item.id || index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                    <div className="md:col-span-2">
                      <p className="text-sm font-medium text-gray-700">Nama Barang</p>
                      <p className="text-sm text-gray-900 mt-1">{item.nama_barang || '-'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Quantity</p>
                      <p className="text-sm text-gray-900 mt-1">{item.quantity || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Satuan</p>
                      <p className="text-sm text-gray-900 mt-1">{item.satuan || '-'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Harga</p>
                      <p className="text-sm text-gray-900 mt-1">
                        {item.unit_price ? `Rp ${Number(item.unit_price).toLocaleString('id-ID')}` : '-'}
                      </p>
                    </div>
                    {(item.specifications || item.spesifikasi) && (
                      <div className="md:col-span-2">
                        <p className="text-sm font-medium text-gray-700">Spesifikasi</p>
                        <p className="text-sm text-gray-900 mt-1">{item.specifications || item.spesifikasi}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-4">
              * Items di atas adalah data yang sudah tersimpan di database. Gunakan form di bawah untuk menambah atau mengubah items.
            </p>
          </div>
        )}

        {/* Items */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Items</h2>
            <Button
              type="button"
              variant="outline"
              onClick={addItem}
            >
              ➕ Tambah Item
            </Button>
          </div>

          {items.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>Belum ada item. Klik "Tambah Item" untuk menambahkan.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {items.map((item, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="font-medium text-gray-800">Item #{index + 1}</h3>
                    <Button
                      type="button"
                      variant="danger"
                      size="sm"
                      onClick={() => removeItem(index)}
                    >
                      🗑️ Hapus
                    </Button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Nama Barang <span className="text-red-500">*</span>
                      </label>
                      <Input
                        type="text"
                        value={item.nama_barang}
                        onChange={(e) => updateItem(index, 'nama_barang', e.target.value)}
                        placeholder="Masukkan nama barang"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
                      <NumberInput
                        value={item.quantity}
                        onChange={(value) => updateItem(index, 'quantity', typeof value === 'number' ? value : parseInt(String(value), 10) || 1)}
                        min="1"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Satuan</label>
                      <Input
                        type="text"
                        value={item.satuan}
                        onChange={(e) => updateItem(index, 'satuan', e.target.value)}
                        placeholder="pcs"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Estimated Price</label>
                      <NumberInput
                        value={item.estimated_price || 0}
                        onChange={(value) => updateItem(index, 'estimated_price', typeof value === 'number' ? value : parseFloat(String(value)) || 0)}
                        min="0"
                        step="0.01"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Spesifikasi</label>
                      <textarea
                        value={item.spesifikasi}
                        onChange={(e) => updateItem(index, 'spesifikasi', e.target.value)}
                        rows={2}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                        placeholder="Masukkan spesifikasi"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Existing Documents (Read-only) - Only show in edit mode */}
        {isEditMode && existingAttachments.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Dokumen yang Sudah Di-upload</h2>
            <div className="space-y-3">
              {existingAttachments.map((attachment: EmailAttachment) => (
                <div key={attachment.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-800">{attachment.original_filename}</p>
                      <div className="flex items-center gap-4 mt-1">
                        <p className="text-xs text-gray-600">
                          Ukuran: {formatFileSize(attachment.file_size)}
                        </p>
                        <p className="text-xs text-gray-600">
                          Tipe: {attachment.mime_type || attachment.file_extension || '-'}
                        </p>
                        <p className="text-xs text-gray-600">
                          Upload: {new Date(attachment.created_at).toLocaleDateString('id-ID')}
                        </p>
                      </div>
                    </div>
                    <a
                      href={`${ENV.API_URL}/api/email/download-attachment/${attachment.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 text-sm text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded transition-colors"
                      download
                    >
                      📥 Download
                    </a>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-4">
              * Dokumen di atas adalah file yang sudah tersimpan di database. Gunakan form di bawah untuk menambah dokumen baru.
            </p>
          </div>
        )}

        {/* File Upload Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Upload Dokumen</h2>
          <div className="space-y-4">
            {/* Existing Files from Database - Only show in edit mode */}
            {isEditMode && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  File yang Sudah Di-upload
                </label>
                {loadingAttachments ? (
                  <div className="text-center py-4 text-gray-500">
                    <LoadingSpinner size="sm" />
                    <p className="mt-2 text-sm">Memuat file...</p>
                  </div>
                ) : attachmentsError ? (
                  <div className="text-center py-4 text-red-500">
                    <p className="text-sm">Error memuat file: {attachmentsError ? 'data' in attachmentsError ? String(attachmentsError.data) : String(attachmentsError) : 'Unknown error'}</p>
                  </div>
                ) : existingAttachments && existingAttachments.length > 0 ? (
                  <div className="space-y-2">
                    {existingAttachments.map((attachment: EmailAttachment) => (
                      <div
                        key={attachment.id}
                        className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg"
                      >
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-800">{attachment.original_filename}</p>
                          <div className="flex items-center gap-4 mt-1">
                            <p className="text-xs text-gray-600">
                              Ukuran: {formatFileSize(attachment.file_size)}
                            </p>
                            <p className="text-xs text-gray-600">
                              Tipe: {attachment.mime_type || attachment.file_extension || '-'}
                            </p>
                            <p className="text-xs text-gray-600">
                              Upload: {new Date(attachment.created_at).toLocaleDateString('id-ID')}
                            </p>
                          </div>
                        </div>
                        <a
                          href={`${ENV.API_URL}/api/email/download-attachment/${attachment.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1 text-sm text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded transition-colors"
                          download
                        >
                          📥 Download
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <p className="text-sm">Belum ada file yang di-upload untuk request ini.</p>
                  </div>
                )}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload File (Opsional)
              </label>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleFileSelect}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.zip,.rar,.txt,.csv"
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 cursor-pointer"
                disabled={creating || updating}
              />
              {selectedFiles.length > 0 && (
                <div className="space-y-2 mt-4">
                  {selectedFiles.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg"
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium text-green-800">{file.name}</p>
                        <p className="text-xs text-green-600 mt-1">
                          Ukuran: {formatFileSize(file.size)}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveFile(index)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Hapus file"
                        disabled={creating || updating}
                      >
                        <XMarkIcon className="w-5 h-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500">
              Format yang didukung: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, JPG, PNG, ZIP, RAR, TXT, CSV. Maksimal 50MB per file.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-end gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/request-pembelian/daftar-request')}
              disabled={creating || updating}
            >
              Batal
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={creating || updating}
            >
              {isEditMode ? 'Update Request' : 'Buat Request'}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default RequestPembelianFormPage;

