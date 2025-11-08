/**
 * Request Items Modal Component
 * Modal untuk menampilkan detail items dari request pembelian
 */

import React from 'react';
import { useGetRequestPembelianByIdQuery } from '../store';
import { Modal, Table, LoadingSpinner } from '@/shared/components/ui';

interface RequestItemsModalProps {
  isOpen: boolean;
  onClose: () => void;
  requestId: number | null;
}

const RequestItemsModal: React.FC<RequestItemsModalProps> = ({
  isOpen,
  onClose,
  requestId,
}) => {
  const { data: requestData, isLoading, error } = useGetRequestPembelianByIdQuery(
    requestId!,
    { skip: !requestId || !isOpen }
  );

  const items = requestData?.items || [];
  const request = requestData;

  const formatCurrency = (amount?: number) => {
    if (!amount) return '-';
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const columns = [
    {
      key: 'no',
      label: 'No',
      render: (_value: any, _item: any, index: number) => (
        <span className="text-sm text-gray-600">{index + 1}</span>
      ),
    },
    {
      key: 'nama_barang',
      label: 'Nama Barang',
      render: (_value: any, item: any) => (
        <span className="font-medium text-gray-800">{item.nama_barang || '-'}</span>
      ),
    },
    {
      key: 'kategori',
      label: 'Kategori',
      render: (_value: any, item: any) => (
        <span className="text-sm text-gray-600">{item.kategori || '-'}</span>
      ),
    },
    {
      key: 'quantity',
      label: 'Quantity',
      render: (_value: any, item: any) => (
        <span className="text-sm text-gray-600">
          {item.quantity || 0} {item.satuan || 'pcs'}
        </span>
      ),
    },
    {
      key: 'unit_price',
      label: 'Harga Satuan',
      render: (_value: any, item: any) => (
        <span className="font-medium text-gray-800">{formatCurrency(item.unit_price)}</span>
      ),
    },
    {
      key: 'total_price',
      label: 'Harga Total',
      render: (_value: any, item: any) => (
        <span className="font-semibold text-primary-600">{formatCurrency(item.total_price)}</span>
      ),
    },
    {
      key: 'specifications',
      label: 'Spesifikasi',
      render: (_value: any, item: any) => (
        <div className="max-w-xs">
          <p className="text-sm text-gray-600 line-clamp-2">{item.specifications || '-'}</p>
        </div>
      ),
    },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        request ? (
          <div>
            <h3 className="text-xl font-bold text-gray-800">
              Items Request: {request.reference_id}
            </h3>
            <p className="text-sm text-gray-600 mt-1">{request.title}</p>
          </div>
        ) : (
          'Detail Items Request'
        )
      }
      size="xl"
    >
      <div className="space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
            <p className="text-red-600">Gagal memuat data items</p>
          </div>
        ) : items.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
            <p className="text-gray-600">Tidak ada items ditemukan untuk request ini</p>
          </div>
        ) : (
          <>
            {/* Summary Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Total Items</p>
                  <p className="font-semibold text-gray-800">{items.length} items</p>
                </div>
                <div>
                  <p className="text-gray-600">Total Quantity</p>
                  <p className="font-semibold text-gray-800">
                    {items.reduce((sum: number, item: any) => sum + (item.quantity || 0), 0)} pcs
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Total Budget</p>
                  <p className="font-semibold text-primary-600">
                    {formatCurrency(
                      items.reduce((sum: number, item: any) => sum + (item.total_price || 0), 0)
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Items Table */}
            <div className="overflow-x-auto">
              <Table
                data={items}
                columns={columns}
                loading={false}
                emptyMessage="Tidak ada items ditemukan"
              />
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};

export default RequestItemsModal;

