/**
 * Bulk Vendor Import Page
 * Halaman untuk bulk import vendor dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBulkImportVendorMutation } from '@/features/vendor-management';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import Swal from 'sweetalert2';

const BulkVendorImportPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [bulkImportVendor, { isLoading }] = useBulkImportVendorMutation();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<{
    success: boolean;
    message: string;
    imported_count?: number;
    errors?: string[];
  } | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      // Validate file type
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls') && !file.name.endsWith('.csv')) {
        sweetAlert.showError('Error', 'File harus berformat .xlsx, .xls, atau .csv');
        return;
      }
      setSelectedFile(file);
      setImportResult(null);
    }
  };

  const handleDownloadTemplate = () => {
    // Create a simple template
    const template = `Company Name,Contact Person,Email,Phone,Address,Business License,Tax ID,Bank Account,Vendor Category,Vendor Type,Business Model
PT Example Vendor,John Doe,john@example.com,081234567890,Jl. Example No. 123,SIUP-123456,123456789012345,1234567890,general,internal,supplier`;

    const blob = new Blob([template], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vendor_import_template.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleImport = async () => {
    if (!selectedFile) {
      await sweetAlert.showError('Error', 'Silakan pilih file terlebih dahulu');
      return;
    }

    try {
      Swal.fire({
        title: 'Mengimport...',
        text: 'Sedang mengimport vendor...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const result = await bulkImportVendor({ file: selectedFile }).unwrap();
      Swal.close();

      setImportResult(result);

      if (result.success) {
        await sweetAlert.showSuccessAuto(
          'Berhasil',
          `Berhasil mengimport ${result.imported_count || 0} vendor`
        );
        // Reset form after successful import
        setSelectedFile(null);
        const fileInput = document.getElementById('file-input') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      } else {
        await sweetAlert.showError('Gagal', result.message || 'Gagal mengimport vendor');
      }
    } catch (error: any) {
      Swal.close();
      const errorMessage = error?.data?.message || error?.message || 'Terjadi kesalahan saat mengimport';
      await sweetAlert.showError('Kesalahan', errorMessage);
      setImportResult({
        success: false,
        message: errorMessage,
        errors: error?.data?.errors || [],
      });
    }
  };

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Bulk Vendor Import</h1>
            <p className="text-gray-600">Import multiple vendor sekaligus dari file Excel/CSV</p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/vendor/daftar')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Import Form */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Upload File</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pilih File (.xlsx, .xls, atau .csv)
              </label>
              <input
                id="file-input"
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
              />
              {selectedFile && (
                <p className="text-sm text-gray-600 mt-2">
                  File dipilih: <span className="font-medium">{selectedFile.name}</span> ({(selectedFile.size / 1024).toFixed(2)} KB)
                </p>
              )}
            </div>

            <div className="flex gap-4">
              <Button
                variant="outline"
                onClick={handleDownloadTemplate}
              >
                📥 Download Template
              </Button>
              <Button
                variant="primary"
                onClick={handleImport}
                disabled={!selectedFile || isLoading}
                isLoading={isLoading}
              >
                📤 Import Vendor
              </Button>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Instruksi</h2>
          <div className="space-y-3 text-sm text-gray-600">
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">Format File:</h3>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>File harus berformat .xlsx, .xls, atau .csv</li>
                <li>Baris pertama adalah header kolom</li>
                <li>Setiap baris berikutnya adalah data vendor</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">Kolom yang Diperlukan:</h3>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li><strong>Company Name</strong> - Nama perusahaan (wajib)</li>
                <li><strong>Contact Person</strong> - Nama kontak (wajib)</li>
                <li><strong>Email</strong> - Email vendor (wajib)</li>
                <li><strong>Phone</strong> - Nomor telepon</li>
                <li><strong>Address</strong> - Alamat</li>
                <li><strong>Business License</strong> - Nomor SIUP</li>
                <li><strong>Tax ID</strong> - NPWP</li>
                <li><strong>Bank Account</strong> - Nomor rekening</li>
                <li><strong>Vendor Category</strong> - Kategori vendor</li>
                <li><strong>Vendor Type</strong> - Tipe vendor (internal/external)</li>
                <li><strong>Business Model</strong> - Model bisnis (supplier/distributor/dll)</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">Tips:</h3>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>Download template terlebih dahulu untuk melihat format yang benar</li>
                <li>Pastikan email unik dan tidak duplikat</li>
                <li>Periksa kembali data sebelum import</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Import Result */}
      {importResult && (
        <div className={`mt-6 bg-white rounded-lg shadow-md p-6 ${
          importResult.success ? 'border-l-4 border-green-500' : 'border-l-4 border-red-500'
        }`}>
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            {importResult.success ? '✅ Import Berhasil' : '❌ Import Gagal'}
          </h2>
          <div className="space-y-2">
            <p className="text-sm text-gray-700">
              <strong>Message:</strong> {importResult.message}
            </p>
            {importResult.imported_count !== undefined && (
              <p className="text-sm text-gray-700">
                <strong>Imported:</strong> {importResult.imported_count} vendor
              </p>
            )}
            {importResult.errors && importResult.errors.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Errors:</p>
                <ul className="list-disc list-inside space-y-1 text-sm text-red-600">
                  {importResult.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkVendorImportPage;

