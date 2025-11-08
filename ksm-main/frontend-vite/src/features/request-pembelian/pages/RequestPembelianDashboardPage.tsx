/**
 * Request Pembelian Dashboard Page
 * Halaman dashboard request pembelian dengan Tailwind CSS
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useGetRequestPembelianListQuery, useGetRequestPembelianDashboardStatsQuery } from '../store';
import { LoadingSpinner } from '@/shared/components/feedback';
import { Button } from '@/shared/components/ui';

const RequestPembelianDashboardPage: React.FC = () => {
  const { data: statsData, isLoading: statsLoading } = useGetRequestPembelianDashboardStatsQuery();
  const { data: requestsData, isLoading: requestsLoading } = useGetRequestPembelianListQuery({
    page: 1,
    per_page: 5,
  });

  const stats = statsData?.data || {
    total_requests: 0,
    pending_requests: 0,
    approved_requests: 0,
    rejected_requests: 0,
    total_budget: 0,
    vendors_count: 0,
  };

  const recentRequests = requestsData?.items || [];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'submitted': return 'bg-blue-100 text-blue-800';
      case 'vendor_uploading': return 'bg-yellow-100 text-yellow-800';
      case 'under_analysis': return 'bg-purple-100 text-purple-800';
      case 'vendor_selected': return 'bg-green-100 text-green-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (statsLoading || requestsLoading) {
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Request Pembelian Dashboard</h1>
            <p className="text-gray-600">Overview dan statistik request pembelian</p>
          </div>
          <Link to="/request-pembelian/buat-request">
            <Button variant="primary">
              ➕ Buat Request Baru
            </Button>
          </Link>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📋</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{stats.total_requests}</h3>
              <p className="text-sm text-gray-600">Total Requests</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">⏳</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{stats.pending_requests}</h3>
              <p className="text-sm text-gray-600">Pending Requests</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">✅</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{stats.approved_requests}</h3>
              <p className="text-sm text-gray-600">Approved Requests</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">❌</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{stats.rejected_requests}</h3>
              <p className="text-sm text-gray-600">Rejected Requests</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">💰</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{formatCurrency(stats.total_budget)}</h3>
              <p className="text-sm text-gray-600">Total Budget</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">🏢</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{stats.vendors_count}</h3>
              <p className="text-sm text-gray-600">Total Vendors</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Requests */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800">Recent Requests</h2>
          <Link to="/request-pembelian/daftar-request">
            <Button variant="outline" size="sm">
              Lihat Semua
            </Button>
          </Link>
        </div>

        {recentRequests.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Reference ID</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Title</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Priority</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Budget</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentRequests.map((request) => (
                  <tr key={request.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <span className="font-mono text-sm">{request.reference_id}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-medium text-gray-800">{request.title}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                        {request.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm text-gray-600 capitalize">{request.priority}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm font-medium">{formatCurrency(request.total_budget || 0)}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm text-gray-600">{formatDate(request.created_at)}</span>
                    </td>
                    <td className="py-3 px-4">
                      <Link to={`/request-pembelian/detail/${request.id}`}>
                        <Button variant="outline" size="sm">
                          Detail
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Tidak Ada Request</h3>
            <p className="text-gray-600 mb-4">Belum ada request pembelian yang dibuat</p>
            <Link to="/request-pembelian/buat-request">
              <Button variant="primary">
                Buat Request Pertama
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default RequestPembelianDashboardPage;

