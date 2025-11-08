/**
 * Approval Management Page
 * Halaman untuk mengelola approval requests dengan Tailwind CSS
 */

import React, { useState } from 'react';
import {
  useGetApprovalRequestsQuery,
  useGetApprovalStatsQuery,
  useApproveRequestMutation,
  useRejectRequestMutation,
  useCancelRequestMutation,
  useGetApprovalActionsQuery,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { ApprovalRequest } from '../types';

const ApprovalManagementPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [filters, setFilters] = useState({
    status: 'all',
    module: 'all',
    search: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [selectedRequest, setSelectedRequest] = useState<ApprovalRequest | null>(null);

  const { data: requestsData, isLoading, refetch } = useGetApprovalRequestsQuery({
    ...filters,
    page: currentPage,
    per_page: itemsPerPage,
  });
  const { data: stats, refetch: refetchStats } = useGetApprovalStatsQuery();
  const { data: actions } = useGetApprovalActionsQuery(selectedRequest?.id || 0, {
    skip: !selectedRequest,
  });

  const [approveRequest] = useApproveRequestMutation();
  const [rejectRequest] = useRejectRequestMutation();
  const [cancelRequest] = useCancelRequestMutation();

  const requests = requestsData?.items || [];
  const pagination = requestsData?.pagination || { page: 1, per_page: 20, total: 0, pages: 1 };

  const handleApprove = async (id: number) => {
    const { value: comment } = await sweetAlert.showInput(
      'Konfirmasi Approval',
      'Tambahkan komentar (opsional):',
      'info',
      '',
      'textarea'
    );

    if (comment !== null) {
      try {
        await approveRequest({ id, comment: comment || undefined }).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Request berhasil disetujui');
        refetch();
        refetchStats();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menyetujui request');
      }
    }
  };

  const handleReject = async (id: number) => {
    const { value: reason } = await sweetAlert.showInput(
      'Konfirmasi Reject',
      'Alasan penolakan:',
      'warning',
      '',
      'textarea'
    );

    if (reason) {
      try {
        await rejectRequest({ id, reason }).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Request berhasil ditolak');
        refetch();
        refetchStats();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menolak request');
      }
    }
  };

  const handleCancel = async (id: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Cancel',
      'Apakah Anda yakin ingin membatalkan request ini?',
      'warning'
    );

    if (confirmed) {
      try {
        await cancelRequest(id).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Request berhasil dibatalkan');
        refetch();
        refetchStats();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal membatalkan request');
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'expired': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      approved: 'Disetujui',
      rejected: 'Ditolak',
      pending: 'Menunggu',
      expired: 'Kedaluwarsa',
      cancelled: 'Dibatalkan',
    };
    return labels[status] || status;
  };

  const columns = [
    {
      key: 'workflow',
      label: 'Workflow',
      render: (_value: any, item: ApprovalRequest) => (
        <span className="font-medium">{item.workflow_name}</span>
      ),
    },
    {
      key: 'requester',
      label: 'Requester',
      render: (_value: any, item: ApprovalRequest) => item.requester_name,
    },
    {
      key: 'module',
      label: 'Module',
      render: (_value: any, item: ApprovalRequest) => item.module,
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: ApprovalRequest) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
          {getStatusLabel(item.status)}
        </span>
      ),
    },
    {
      key: 'created',
      label: 'Dibuat',
      render: (_value: any, item: ApprovalRequest) => {
        const date = new Date(item.created_at);
        return date.toLocaleDateString('id-ID', { year: 'numeric', month: 'short', day: 'numeric' });
      },
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: ApprovalRequest) => (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedRequest(item)}
          >
            👁️ Detail
          </Button>
          {item.status === 'pending' && (
            <>
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleApprove(item.id)}
              >
                ✓ Approve
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleReject(item.id)}
              >
                ✗ Reject
              </Button>
            </>
          )}
          {item.status === 'pending' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCancel(item.id)}
            >
              🗑️ Cancel
            </Button>
          )}
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">✅ Approval Management</h1>
            <p className="text-gray-600">Kelola approval requests</p>
          </div>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-sm text-gray-600 mb-1">Pending</div>
            <div className="text-2xl font-bold text-yellow-600">{stats.pending_approvals}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-sm text-gray-600 mb-1">My Requests</div>
            <div className="text-2xl font-bold text-blue-600">{stats.my_requests}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-sm text-gray-600 mb-1">Approved</div>
            <div className="text-2xl font-bold text-green-600">{stats.approved_requests}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-sm text-gray-600 mb-1">Rejected</div>
            <div className="text-2xl font-bold text-red-600">{stats.rejected_requests}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Input
              type="text"
              placeholder="Cari..."
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
              <option value="all">Semua Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="expired">Expired</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <select
              value={filters.module}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, module: e.target.value }));
                setCurrentPage(1);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Module</option>
              <option value="request_pembelian">Request Pembelian</option>
              <option value="leave_request">Leave Request</option>
              <option value="overtime">Overtime</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={requests}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada approval request ditemukan"
        />
      </div>

      {/* Detail Modal */}
      {selectedRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Detail Approval Request</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedRequest(null)}
                >
                  ✕
                </Button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Workflow</label>
                  <p className="text-gray-800">{selectedRequest.workflow_name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Requester</label>
                  <p className="text-gray-800">{selectedRequest.requester_name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Module</label>
                  <p className="text-gray-800">{selectedRequest.module}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedRequest.status)}`}>
                    {getStatusLabel(selectedRequest.status)}
                  </span>
                </div>
                {selectedRequest.rejection_reason && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Alasan Penolakan</label>
                    <p className="text-gray-800">{selectedRequest.rejection_reason}</p>
                  </div>
                )}

                {actions && actions.length > 0 && (
                  <div className="border-t border-gray-200 pt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">History Actions</h3>
                    <div className="space-y-2">
                      {actions.map(action => (
                        <div key={action.id} className="p-2 bg-gray-50 rounded">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{action.approver_name}</span>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              action.action === 'approve' ? 'bg-green-100 text-green-800' :
                              action.action === 'reject' ? 'bg-red-100 text-red-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {action.action}
                            </span>
                          </div>
                          {action.comment && (
                            <p className="text-xs text-gray-600 mt-1">{action.comment}</p>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(action.created_at).toLocaleString('id-ID')}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApprovalManagementPage;

