/**
 * Database Discovery Page
 * Halaman untuk discover dan manage Notion databases dengan Tailwind CSS
 */

import React, { useState } from 'react';
import {
  useGetDatabasesQuery,
  useGetEmployeesQuery,
  useGetStatisticsQuery,
  useRunDiscoveryMutation,
  useToggleSyncMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Table } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { DatabaseInfo } from '../types';

const DatabaseDiscoveryPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [filter, setFilter] = useState({
    type: 'all',
    employee: '',
    validOnly: true,
  });

  const { data: databases = [], isLoading, refetch } = useGetDatabasesQuery({
    type: filter.type !== 'all' ? filter.type : undefined,
    employee: filter.employee || undefined,
    valid_only: filter.validOnly,
  });
  const { data: employees = [], refetch: refetchEmployees } = useGetEmployeesQuery();
  const { data: statistics, refetch: refetchStats } = useGetStatisticsQuery();
  const [runDiscovery, { isLoading: discovering }] = useRunDiscoveryMutation();
  const [toggleSync] = useToggleSyncMutation();

  const handleRunDiscovery = async () => {
    try {
      const result = await runDiscovery().unwrap();
      await sweetAlert.showSuccessAuto(
        'Berhasil',
        result.message || `Ditemukan ${result.discovered || 0} database baru`
      );
      refetch();
      refetchStats();
      refetchEmployees();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal menjalankan discovery');
    }
  };

  const handleToggleSync = async (databaseId: string, currentEnabled: boolean) => {
    try {
      await toggleSync({ databaseId, enabled: !currentEnabled }).unwrap();
      await sweetAlert.showSuccessAuto(
        'Berhasil',
        `Sync ${!currentEnabled ? 'diaktifkan' : 'dinonaktifkan'}`
      );
      refetch();
      refetchStats();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal mengubah status sync');
    }
  };

  const getStatusColor = (valid: boolean, confidence: number) => {
    if (!valid) return 'bg-red-100 text-red-800';
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-orange-100 text-orange-800';
  };

  const columns = [
    {
      key: 'database_title',
      label: 'Nama Database',
      render: (_value: any, item: DatabaseInfo) => (
        <div>
          <div className="font-medium text-gray-900">{item.database_title}</div>
          <div className="text-xs text-gray-500 mt-1">ID: {item.database_id}</div>
        </div>
      ),
    },
    {
      key: 'employee_name',
      label: 'Employee',
      render: (_value: any, item: DatabaseInfo) => (
        <span>{item.employee_name || '-'}</span>
      ),
    },
    {
      key: 'database_type',
      label: 'Tipe',
      render: (_value: any, item: DatabaseInfo) => (
        <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
          {item.database_type}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: DatabaseInfo) => (
        <div className="space-y-1">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.structure_valid, item.confidence_score)}`}>
            {item.structure_valid ? 'Valid' : 'Invalid'} ({Math.round(item.confidence_score * 100)}%)
          </span>
          <div className="text-xs text-gray-500">
            {item.is_task_database && '📋 Task DB'}
            {item.is_employee_specific && ' 👤 Employee'}
          </div>
        </div>
      ),
    },
    {
      key: 'sync',
      label: 'Sync',
      render: (_value: any, item: DatabaseInfo) => (
        <div className="space-y-1">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.sync_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
            {item.sync_enabled ? 'Enabled' : 'Disabled'}
          </span>
          {item.last_synced && (
            <div className="text-xs text-gray-500">
              Last: {new Date(item.last_synced).toLocaleDateString('id-ID')}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: DatabaseInfo) => (
        <Button
          variant={item.sync_enabled ? 'outline' : 'primary'}
          size="sm"
          onClick={() => handleToggleSync(item.database_id, item.sync_enabled)}
        >
          {item.sync_enabled ? 'Disable Sync' : 'Enable Sync'}
        </Button>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🔍 Database Discovery</h1>
            <p className="text-gray-600">Discover dan manage Notion databases</p>
          </div>
          <Button
            variant="primary"
            onClick={handleRunDiscovery}
            disabled={discovering}
          >
            {discovering ? '⏳ Discovering...' : '🔍 Run Discovery'}
          </Button>
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Total Databases</div>
            <div className="text-2xl font-bold text-gray-800">{statistics.total_databases}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Task Databases</div>
            <div className="text-2xl font-bold text-blue-600">{statistics.task_databases}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Employee Databases</div>
            <div className="text-2xl font-bold text-purple-600">{statistics.employee_databases}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Valid Databases</div>
            <div className="text-2xl font-bold text-green-600">{statistics.valid_databases}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Enabled Sync</div>
            <div className="text-2xl font-bold text-orange-600">{statistics.enabled_databases}</div>
          </div>
        </div>
      )}

      {/* Employee Statistics */}
      {employees.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Employee Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {employees.map((emp) => (
              <div key={emp.employee_name} className="border border-gray-200 rounded-lg p-4">
                <div className="font-medium text-gray-900 mb-2">{emp.employee_name}</div>
                <div className="text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total:</span>
                    <span className="font-semibold">{emp.total_databases}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Task DB:</span>
                    <span className="font-semibold">{emp.task_databases}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Valid:</span>
                    <span className="font-semibold">{emp.valid_databases}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg Confidence:</span>
                    <span className="font-semibold">{Math.round(emp.average_confidence * 100)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tipe Database</label>
            <select
              value={filter.type}
              onChange={(e) => setFilter(prev => ({ ...prev, type: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Tipe</option>
              <option value="task">Task Database</option>
              <option value="employee">Employee Specific</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Employee</label>
            <select
              value={filter.employee}
              onChange={(e) => setFilter(prev => ({ ...prev, employee: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Semua Employee</option>
              {employees.map((emp) => (
                <option key={emp.employee_name} value={emp.employee_name}>
                  {emp.employee_name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filter.validOnly}
                onChange={(e) => setFilter(prev => ({ ...prev, validOnly: e.target.checked }))}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Hanya Valid Databases</span>
            </label>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-800">
              Databases ({databases.length})
            </h2>
          </div>
        </div>
        <Table
          data={databases}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada database ditemukan"
        />
      </div>
    </div>
  );
};

export default DatabaseDiscoveryPage;

