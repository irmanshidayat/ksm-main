/**
 * Export Modal Component
 * Modal untuk export data barang dengan Tailwind
 */

import React, { useState } from 'react';
import { Modal, Button } from '@/shared/components/ui';
import { useSweetAlert } from '@/shared/hooks';
import type { FilterParams } from '../types';
import Swal from 'sweetalert2';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (filters?: FilterParams, exportAll?: boolean) => Promise<boolean>;
  currentFilters?: FilterParams;
  hasActiveFilters: boolean;
}

const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  onExport,
  currentFilters,
  hasActiveFilters
}) => {
  const sweetAlert = useSweetAlert();
  const [exportType, setExportType] = useState<'filtered' | 'all'>('filtered');
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);

    Swal.fire({
      title: 'Mengekspor...',
      text: 'Sedang memproses data untuk ekspor...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });

    try {
      const result = await onExport(
        exportType === 'filtered' ? currentFilters : undefined,
        exportType === 'all'
      );

      Swal.close();
      if (result) {
        await sweetAlert.showSuccessAuto('Export Berhasil', 'File Excel telah berhasil diunduh');
        onClose();
      } else {
        await sweetAlert.showError('Export Gagal', 'Gagal melakukan export data');
      }
    } catch (err) {
      Swal.close();
      await sweetAlert.showError('Kesalahan Export', 'Terjadi kesalahan saat melakukan export');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setExportType('filtered');
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="📊 Export Data Barang"
      size="md"
    >
      <div className="space-y-4">
        {/* Export Options */}
        <div>
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Pilih Data yang Akan Diexport:</h3>
          
          <div className="space-y-3">
            <label className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="exportType"
                value="filtered"
                checked={exportType === 'filtered'}
                onChange={(e) => setExportType(e.target.value as 'filtered' | 'all')}
                disabled={loading}
                className="mt-1"
              />
              <div>
                <strong className="text-gray-800">Data Terfilter</strong>
                <p className="text-xs text-gray-600 mt-1">
                  {hasActiveFilters 
                    ? 'Export data sesuai dengan filter yang sedang aktif'
                    : 'Export semua data (tidak ada filter aktif)'
                  }
                </p>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="radio"
                name="exportType"
                value="all"
                checked={exportType === 'all'}
                onChange={(e) => setExportType(e.target.value as 'filtered' | 'all')}
                disabled={loading}
                className="mt-1"
              />
              <div>
                <strong className="text-gray-800">Semua Data</strong>
                <p className="text-xs text-gray-600 mt-1">
                  Export seluruh data barang tanpa filter
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Active Filters Info */}
        {hasActiveFilters && currentFilters && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-800 mb-2">Filter Aktif:</h4>
            <div className="flex flex-wrap gap-2">
              {currentFilters.search && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  🔍 Pencarian: "{currentFilters.search}"
                </span>
              )}
              {currentFilters.kategori_id && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  🏷️ Kategori: {currentFilters.kategori_id}
                </span>
              )}
              {currentFilters.supplier_id && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  🏢 Supplier: {currentFilters.supplier_id}
                </span>
              )}
              {(currentFilters.stok_min !== undefined || currentFilters.stok_max !== undefined) && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  📦 Stok: {currentFilters.stok_min || 0} - {currentFilters.stok_max || '∞'}
                </span>
              )}
              {(currentFilters.harga_min !== undefined || currentFilters.harga_max !== undefined) && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  💰 Harga: {currentFilters.harga_min || 0} - {currentFilters.harga_max || '∞'}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Format Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-800 mb-2">Format Export:</h4>
          <div className="space-y-1 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <span>📄</span>
              <span>Microsoft Excel (.xlsx)</span>
            </div>
            <div className="flex items-center gap-2">
              <span>📊</span>
              <span>Data lengkap dengan styling</span>
            </div>
            <div className="flex items-center gap-2">
              <span>📅</span>
              <span>Timestamp otomatis</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={loading}
          >
            Batal
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleExport}
            isLoading={loading}
          >
            📊 Export ke Excel
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ExportModal;

