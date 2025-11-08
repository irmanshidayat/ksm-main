/**
 * Upload Penawaran Selector Page
 * Halaman untuk memilih vendor dan request untuk upload penawaran dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetRequestPembelianListQuery } from '../store';
import { useGetVendorsQuery } from '@/features/vendor-management';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';

const UploadPenawaranSelectorPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedVendor, setSelectedVendor] = useState<number | null>(null);
  const [selectedRequest, setSelectedRequest] = useState<number | null>(null);
  const [searchVendor, setSearchVendor] = useState('');
  const [searchRequest, setSearchRequest] = useState('');

  const { data: vendorsData, isLoading: loadingVendors } = useGetVendorsQuery({ page: 1, per_page: 100 });
  const { data: requestsData, isLoading: loadingRequests } = useGetRequestPembelianListQuery({ page: 1, per_page: 100 });

  const vendors = vendorsData?.items || [];
  const requests = requestsData?.items || [];

  const filteredVendors = vendors.filter((v: any) =>
    v.company_name?.toLowerCase().includes(searchVendor.toLowerCase()) ||
    v.email?.toLowerCase().includes(searchVendor.toLowerCase())
  );

  const filteredRequests = requests.filter((r: any) =>
    r.title?.toLowerCase().includes(searchRequest.toLowerCase()) ||
    r.reference_id?.toLowerCase().includes(searchRequest.toLowerCase())
  );

  const handleContinue = () => {
    if (selectedVendor && selectedRequest) {
      navigate(`/request-pembelian/upload-penawaran/${selectedVendor}/${selectedRequest}`);
    }
  };

  if (loadingVendors || loadingRequests) {
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Upload Penawaran</h1>
            <p className="text-gray-600">Pilih vendor dan request untuk upload penawaran</p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/request-pembelian/daftar-request')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vendor Selection */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Pilih Vendor</h2>
          
          <div className="mb-4">
            <Input
              type="text"
              placeholder="Cari vendor..."
              value={searchVendor}
              onChange={(e) => setSearchVendor(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="max-h-96 overflow-y-auto space-y-2">
            {filteredVendors.length > 0 ? (
              filteredVendors.map((vendor: any) => (
                <div
                  key={vendor.id}
                  onClick={() => setSelectedVendor(vendor.id)}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedVendor === vendor.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <h3 className="font-medium text-gray-800">{vendor.company_name}</h3>
                  <p className="text-sm text-gray-600">{vendor.email}</p>
                  <p className="text-xs text-gray-500 mt-1">{vendor.vendor_category}</p>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>Tidak ada vendor ditemukan</p>
              </div>
            )}
          </div>
        </div>

        {/* Request Selection */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Pilih Request</h2>
          
          <div className="mb-4">
            <Input
              type="text"
              placeholder="Cari request..."
              value={searchRequest}
              onChange={(e) => setSearchRequest(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="max-h-96 overflow-y-auto space-y-2">
            {filteredRequests.length > 0 ? (
              filteredRequests.map((request: any) => (
                <div
                  key={request.id}
                  onClick={() => setSelectedRequest(request.id)}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedRequest === request.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <h3 className="font-medium text-gray-800">{request.title}</h3>
                  <p className="text-sm text-gray-600 font-mono">{request.reference_id}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Status: {request.status} | Items: {request.items_count || 0}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>Tidak ada request ditemukan</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Continue Button */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        <div className="flex items-center justify-between">
          <div>
            {selectedVendor && selectedRequest && (
              <p className="text-sm text-gray-600">
                Vendor dan Request sudah dipilih. Klik "Lanjutkan" untuk upload penawaran.
              </p>
            )}
            {(!selectedVendor || !selectedRequest) && (
              <p className="text-sm text-gray-600">
                Silakan pilih vendor dan request terlebih dahulu.
              </p>
            )}
          </div>
          <Button
            variant="primary"
            onClick={handleContinue}
            disabled={!selectedVendor || !selectedRequest}
          >
            Lanjutkan →
          </Button>
        </div>
      </div>
    </div>
  );
};

export default UploadPenawaranSelectorPage;

