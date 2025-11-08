/**
 * Vendor Catalog Item Update Modal Component
 * Modal untuk update vendor catalog item
 */

import React, { useState, useEffect } from 'react';
import { Modal, Button, Input } from '@/shared/components/ui';
import { useUpdateVendorCatalogItemMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import Swal from 'sweetalert2';

interface VendorCatalogItemUpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  item: any | null;
  onUpdateSuccess?: () => void;
}

const VendorCatalogItemUpdateModal: React.FC<VendorCatalogItemUpdateModalProps> = ({
  isOpen,
  onClose,
  item,
  onUpdateSuccess,
}) => {
  const sweetAlert = useSweetAlert();
  const [updateItem, { isLoading }] = useUpdateVendorCatalogItemMutation();
  const [formData, setFormData] = useState({
    vendor_unit_price: '',
    vendor_quantity: '',
    vendor_total_price: '',
    vendor_specifications: '',
    vendor_merk: '',
    kategori: '',
    vendor_notes: '',
  });

  useEffect(() => {
    if (item) {
      setFormData({
        vendor_unit_price: item.vendor_unit_price?.toString() || '',
        vendor_quantity: item.vendor_quantity?.toString() || '',
        vendor_total_price: item.vendor_total_price?.toString() || '',
        vendor_specifications: item.vendor_specifications || '',
        vendor_merk: item.vendor_merk || '',
        kategori: item.kategori || '',
        vendor_notes: item.vendor_notes || '',
      });
    }
  }, [item]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => {
      const newData = { ...prev, [name]: value };
      
      // Auto calculate total price if unit price and quantity are provided
      if (name === 'vendor_unit_price' || name === 'vendor_quantity') {
        const unitPrice = name === 'vendor_unit_price' ? parseFloat(value) : parseFloat(prev.vendor_unit_price);
        const quantity = name === 'vendor_quantity' ? parseFloat(value) : parseFloat(prev.vendor_quantity);
        
        if (!isNaN(unitPrice) && !isNaN(quantity) && unitPrice > 0 && quantity > 0) {
          newData.vendor_total_price = (unitPrice * quantity).toString();
        } else {
          newData.vendor_total_price = '';
        }
      }
      
      return newData;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!item) return;

    try {
      Swal.fire({
        title: 'Mengupdate...',
        text: 'Sedang mengupdate data...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const updateData: any = {};
      
      if (formData.vendor_unit_price) updateData.vendor_unit_price = parseFloat(formData.vendor_unit_price);
      if (formData.vendor_quantity) updateData.vendor_quantity = parseInt(formData.vendor_quantity);
      if (formData.vendor_total_price) updateData.vendor_total_price = parseFloat(formData.vendor_total_price);
      if (formData.vendor_specifications) updateData.vendor_specifications = formData.vendor_specifications;
      if (formData.vendor_merk) updateData.vendor_merk = formData.vendor_merk;
      if (formData.kategori) updateData.kategori = formData.kategori;
      if (formData.vendor_notes) updateData.vendor_notes = formData.vendor_notes;

      const response = await updateItem({ id: item.id, data: updateData }).unwrap();

      Swal.close();
      if (response.success) {
        await sweetAlert.showSuccessAuto('Berhasil', 'Barang vendor berhasil diupdate');
        if (onUpdateSuccess) {
          onUpdateSuccess();
        }
        onClose();
      } else {
        await sweetAlert.showError('Gagal', response.message || 'Gagal mengupdate barang vendor');
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || error?.message || 'Gagal mengupdate barang vendor');
    }
  };

  if (!item) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Update Barang Vendor"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <p className="text-sm text-gray-700">
            <span className="font-semibold">Nama Barang:</span> {item.nama_barang || item.request_item?.nama_barang || '-'}
          </p>
          <p className="text-sm text-gray-700 mt-1">
            <span className="font-semibold">Vendor:</span> {item.vendor?.company_name || '-'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Harga Satuan *
            </label>
            <Input
              type="number"
              name="vendor_unit_price"
              value={formData.vendor_unit_price}
              onChange={handleChange}
              placeholder="0"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quantity *
            </label>
            <Input
              type="number"
              name="vendor_quantity"
              value={formData.vendor_quantity}
              onChange={handleChange}
              placeholder="0"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Harga Total
            </label>
            <Input
              type="number"
              name="vendor_total_price"
              value={formData.vendor_total_price}
              onChange={handleChange}
              placeholder="0"
              readOnly
              className="bg-gray-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Kategori
            </label>
            <Input
              type="text"
              name="kategori"
              value={formData.kategori}
              onChange={handleChange}
              placeholder="Kategori"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Merek
            </label>
            <Input
              type="text"
              name="vendor_merk"
              value={formData.vendor_merk}
              onChange={handleChange}
              placeholder="Merek"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Spesifikasi Vendor
          </label>
          <textarea
            name="vendor_specifications"
            value={formData.vendor_specifications}
            onChange={handleChange}
            placeholder="Spesifikasi vendor..."
            rows={4}
            className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Catatan
          </label>
          <textarea
            name="vendor_notes"
            value={formData.vendor_notes}
            onChange={handleChange}
            placeholder="Catatan..."
            rows={3}
            className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-end pt-4 border-t border-gray-200">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Batal
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
          >
            {isLoading ? 'Mengupdate...' : 'Update'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default VendorCatalogItemUpdateModal;

