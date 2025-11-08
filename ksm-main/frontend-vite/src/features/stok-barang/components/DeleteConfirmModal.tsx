/**
 * Delete Confirm Modal Component
 * Modal konfirmasi hapus barang dengan Tailwind
 */

import React, { useState } from 'react';
import { Modal, Button } from '@/shared/components/ui';
import { useDeleteBarangMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import type { Barang } from '../types';
import Swal from 'sweetalert2';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  item: Barang | null;
}

const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  item
}) => {
  const sweetAlert = useSweetAlert();
  const [deleteBarang, { isLoading }] = useDeleteBarangMutation();

  const handleDelete = async () => {
    if (!item) return;

    Swal.fire({
      title: 'Menghapus...',
      text: 'Sedang menghapus barang...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });

    try {
      await deleteBarang(item.id).unwrap();
      Swal.close();
      await sweetAlert.showSuccessAuto('Berhasil', 'Barang berhasil dihapus');
      onSuccess();
      onClose();
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || 'Gagal menghapus barang');
    }
  };

  if (!isOpen || !item) return null;

  const hasStock = (item.stok?.jumlah_stok || 0) > 0;
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="🗑️ Konfirmasi Hapus Barang"
      size="md"
    >
      <div className="space-y-4">
        {/* Warning */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
          <div className="text-4xl mb-2">⚠️</div>
          <h3 className="text-lg font-semibold text-gray-800">Apakah Anda yakin ingin menghapus barang ini?</h3>
        </div>

        {/* Item Details */}
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <div className="flex justify-between">
            <span className="text-sm font-medium text-gray-600">Kode Barang:</span>
            <span className="text-sm text-gray-800">{item.kode_barang}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium text-gray-600">Nama Barang:</span>
            <span className="text-sm text-gray-800">{item.nama_barang}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium text-gray-600">Kategori:</span>
            <span className="text-sm text-gray-800">{item.kategori?.nama_kategori || '-'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium text-gray-600">Stok Saat Ini:</span>
            <span className={`text-sm font-semibold ${hasStock ? 'text-red-600' : 'text-gray-800'}`}>
              {item.stok?.jumlah_stok || 0} {item.satuan}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium text-gray-600">Harga:</span>
            <span className="text-sm text-gray-800">{formatCurrency(item.harga_per_unit || 0)}</span>
          </div>
        </div>

        {/* Stock Warning */}
        {hasStock && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <span className="text-xl">⚠️</span>
              <div>
                <strong className="text-red-800">Peringatan:</strong>
                <p className="text-sm text-red-700 mt-1">
                  Barang ini masih memiliki stok sebesar {item.stok?.jumlah_stok || 0} {item.satuan}. 
                  Menghapus barang akan menghapus semua data terkait termasuk stok dan riwayat transaksi.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Consequences */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-800 mb-2">Data yang akan dihapus:</h4>
          <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
            <li>Data barang dan informasi detail</li>
            <li>Data stok barang</li>
            <li>Riwayat transaksi barang masuk/keluar</li>
            <li>Semua data terkait barang ini</li>
          </ul>
          <p className="text-sm font-semibold text-red-600 mt-2">
            ⚠️ Perhatian: Tindakan ini tidak dapat dibatalkan!
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Batal
          </Button>
          <Button
            type="button"
            variant="danger"
            onClick={handleDelete}
            isLoading={isLoading}
          >
            Ya, Hapus Barang
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default DeleteConfirmModal;

