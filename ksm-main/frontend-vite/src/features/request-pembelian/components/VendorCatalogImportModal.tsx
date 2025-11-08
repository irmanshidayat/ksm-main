/**
 * Vendor Catalog Import Modal Component
 * Modal untuk bulk import barang vendor penawaran dari file Excel
 */

import React, { useState, useRef } from 'react';
import { Modal, Button } from '@/shared/components/ui';
import { useSweetAlert } from '@/shared/hooks';
import Swal from 'sweetalert2';

interface VendorCatalogImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess?: () => void;
}

const VendorCatalogImportModal: React.FC<VendorCatalogImportModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess,
}) => {
  const sweetAlert = useSweetAlert();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDownloadTemplate = async () => {
    try {
      Swal.fire({
        title: 'Mengunduh template...',
        text: 'Sedang memproses template Excel...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const token = localStorage.getItem('KSM_access_token');
      const apiUrl = import.meta.env.VITE_APP_API_URL || 'http://localhost:8000';

      const response = await fetch(`${apiUrl}/api/vendor-catalog/bulk-import/template`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `template_import_barang_vendor_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);

        Swal.close();
        await sweetAlert.showSuccessAuto('Berhasil', 'Template Excel berhasil diunduh');
      } else {
        throw new Error('Gagal mengunduh template');
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.message || 'Gagal mengunduh template');
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const fileExtension = file.name.split('.').pop()?.toLowerCase();
      const allowedExtensions = ['xlsx', 'xls', 'csv'];

      if (!allowedExtensions.includes(fileExtension || '')) {
        sweetAlert.showError('Format Tidak Didukung', 'File harus berformat Excel (.xlsx, .xls) atau CSV (.csv)');
        return;
      }

      setSelectedFile(file);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleImport = async () => {
    if (!selectedFile) {
      await sweetAlert.showError('Peringatan', 'Silakan pilih file terlebih dahulu');
      return;
    }

    try {
      setIsUploading(true);

      Swal.fire({
        title: 'Mengimpor data...',
        text: 'Sedang memproses file Excel...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const token = localStorage.getItem('KSM_access_token');
      const apiUrl = import.meta.env.VITE_APP_API_URL || 'http://localhost:8000';

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${apiUrl}/api/vendor-catalog/bulk-import`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();

      Swal.close();

      if (response.ok && result.success) {
        const importedCount = result.imported_items?.length || 0;
        const failedCount = result.failed_imports || 0;
        const errors = result.errors || [];

        let message = `${importedCount} barang berhasil diimpor`;
        if (failedCount > 0) {
          message += `. ${failedCount} barang gagal diimpor.`;
        }

        if (errors.length > 0 && errors.length <= 5) {
          message += `\n\nError: ${errors.join(', ')}`;
        } else if (errors.length > 5) {
          message += `\n\n${errors.length} error ditemukan.`;
        }

        await sweetAlert.showSuccessAuto('Import Berhasil', message);
        
        // Reset form
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }

        // Call success callback
        if (onImportSuccess) {
          onImportSuccess();
        }

        // Close modal
        onClose();
      } else {
        const errorMessage = result.message || 'Gagal mengimpor data';
        await sweetAlert.showError('Import Gagal', errorMessage);
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Kesalahan', error?.message || 'Terjadi kesalahan saat mengimpor data');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    if (!isUploading) {
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Import Barang Vendor"
      size="lg"
    >
      <div className="space-y-6">
        {/* Download Template Section */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-800 mb-2">📥 Download Template</h4>
          <p className="text-sm text-gray-600 mb-4">
            Download template Excel untuk memastikan format file sesuai dengan yang diperlukan.
          </p>
          <Button
            variant="outline"
            onClick={handleDownloadTemplate}
            className="w-full md:w-auto"
          >
            📄 Download Template Excel
          </Button>
        </div>

        {/* Upload File Section */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pilih File Excel/CSV
            </label>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileSelect}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 cursor-pointer"
                disabled={isUploading}
              />
              {selectedFile && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRemoveFile}
                  disabled={isUploading}
                >
                  Hapus
                </Button>
              )}
            </div>
            {selectedFile && (
              <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  <span className="font-medium">File dipilih:</span> {selectedFile.name}
                </p>
                <p className="text-xs text-green-600 mt-1">
                  Ukuran: {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            )}
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-xs text-yellow-800">
              <strong>Catatan:</strong> Format file yang didukung adalah Excel (.xlsx, .xls) atau CSV (.csv).
              Pastikan file mengikuti format template yang telah diunduh.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-end pt-4 border-t border-gray-200">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isUploading}
          >
            Batal
          </Button>
          <Button
            variant="primary"
            onClick={handleImport}
            disabled={!selectedFile || isUploading}
            className="flex items-center gap-2"
          >
            {isUploading ? (
              <>
                <span className="animate-spin">⏳</span>
                Mengimpor...
              </>
            ) : (
              <>
                <span>📤</span>
                Import Data
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default VendorCatalogImportModal;

