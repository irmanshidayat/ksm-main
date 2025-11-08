/**
 * Enhanced Database Page
 * Halaman untuk manage property mappings Notion databases dengan Tailwind CSS
 */

import React, { useState } from 'react';
import {
  useGetDatabasesWithMappingsQuery,
  useGetMappingStatisticsQuery,
  useGetDatabaseMappingsQuery,
  useAnalyzeDatabaseMappingMutation,
  useUpdatePropertyMappingMutation,
  useToggleMappingActiveMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { DatabaseInfo, PropertyMapping } from '../types';

const EnhancedDatabasePage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');

  const { data: databases = [], isLoading, refetch } = useGetDatabasesWithMappingsQuery();
  const { data: statistics, refetch: refetchStats } = useGetMappingStatisticsQuery();
  const { data: mappings = [], isLoading: mappingsLoading, refetch: refetchMappings } = useGetDatabaseMappingsQuery(
    selectedDatabase,
    { skip: !selectedDatabase }
  );
  const [analyzeMapping, { isLoading: analyzing }] = useAnalyzeDatabaseMappingMutation();
  const [updateMapping] = useUpdatePropertyMappingMutation();
  const [toggleActive] = useToggleMappingActiveMutation();

  const handleAnalyze = async (databaseId: string) => {
    try {
      await analyzeMapping(databaseId).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Mapping analysis berhasil dijalankan');
      refetchMappings();
      refetch();
      refetchStats();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal menjalankan analysis');
    }
  };

  const handleToggleActive = async (mapping: PropertyMapping) => {
    try {
      await toggleActive({ mappingId: mapping.id, isActive: !mapping.is_active }).unwrap();
      await sweetAlert.showSuccessAuto(
        'Berhasil',
        `Mapping ${!mapping.is_active ? 'diaktifkan' : 'dinonaktifkan'}`
      );
      refetchMappings();
      refetchStats();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal mengubah status mapping');
    }
  };

  const handleUpdateMapping = async (mappingId: number, field: string, value: any) => {
    try {
      await updateMapping({ mappingId, data: { [field]: value } }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Mapping berhasil diupdate');
      refetchMappings();
      refetchStats();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal update mapping');
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-orange-100 text-orange-800';
  };

  const databaseColumns = [
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
      render: (_value: any, item: DatabaseInfo) => <span>{item.employee_name}</span>,
    },
    {
      key: 'quality',
      label: 'Quality Score',
      render: (_value: any, item: DatabaseInfo) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getQualityColor(item.mapping_quality_score)}`}>
          {Math.round(item.mapping_quality_score * 100)}%
        </span>
      ),
    },
    {
      key: 'mappings',
      label: 'Mappings',
      render: (_value: any, item: DatabaseInfo) => (
        <div className="text-sm">
          <div>Total: {item.mapping_statistics?.total_mappings || 0}</div>
          <div>Active: {item.mapping_statistics?.active_mappings || 0}</div>
          <div>High Confidence: {item.mapping_statistics?.high_confidence_mappings || 0}</div>
        </div>
      ),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: DatabaseInfo) => (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedDatabase(item.database_id)}
          >
            View Mappings
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => handleAnalyze(item.database_id)}
            disabled={analyzing}
          >
            {analyzing ? 'Analyzing...' : 'Analyze'}
          </Button>
        </div>
      ),
    },
  ];

  const mappingColumns = [
    {
      key: 'notion_property_name',
      label: 'Notion Property',
      render: (_value: any, item: PropertyMapping) => (
        <div>
          <div className="font-medium text-gray-900">{item.notion_property_name}</div>
          <div className="text-xs text-gray-500 mt-1">Type: {item.property_type}</div>
        </div>
      ),
    },
    {
      key: 'mapped_field',
      label: 'Mapped Field',
      render: (_value: any, item: PropertyMapping) => (
        <Input
          type="text"
          value={item.mapped_field}
          onChange={(e) => handleUpdateMapping(item.id, 'mapped_field', e.target.value)}
          className="w-full"
        />
      ),
    },
    {
      key: 'confidence',
      label: 'Confidence',
      render: (_value: any, item: PropertyMapping) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(item.confidence_score)}`}>
          {Math.round(item.confidence_score * 100)}%
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: PropertyMapping) => (
        <div className="space-y-1">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
            {item.is_active ? 'Active' : 'Inactive'}
          </span>
          {item.is_required && (
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 block mt-1">
              Required
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: PropertyMapping) => (
        <Button
          variant={item.is_active ? 'outline' : 'primary'}
          size="sm"
          onClick={() => handleToggleActive(item)}
        >
          {item.is_active ? 'Deactivate' : 'Activate'}
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🗄️ Enhanced Database</h1>
            <p className="text-gray-600">Manage property mappings untuk Notion databases</p>
          </div>
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Total Databases</div>
            <div className="text-2xl font-bold text-gray-800">{statistics.total_databases}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Total Mappings</div>
            <div className="text-2xl font-bold text-blue-600">{statistics.total_mappings}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Active Mappings</div>
            <div className="text-2xl font-bold text-green-600">{statistics.active_mappings}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">High Quality</div>
            <div className="text-2xl font-bold text-purple-600">{statistics.high_quality_mappings}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Avg per DB</div>
            <div className="text-2xl font-bold text-orange-600">{statistics.average_mappings_per_database.toFixed(1)}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Coverage</div>
            <div className="text-2xl font-bold text-indigo-600">{statistics.mapping_coverage_percentage.toFixed(1)}%</div>
          </div>
        </div>
      )}

      {/* Database List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden mb-6">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">Databases ({databases.length})</h2>
        </div>
        <Table
          data={databases}
          columns={databaseColumns}
          loading={isLoading}
          emptyMessage="Tidak ada database ditemukan"
        />
      </div>

      {/* Mappings for Selected Database */}
      {selectedDatabase && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-800">
                Property Mappings ({mappings.length})
              </h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedDatabase('')}
              >
                ✕ Close
              </Button>
            </div>
          </div>
          {mappingsLoading ? (
            <div className="p-8 text-center">
              <LoadingSpinner />
            </div>
          ) : (
            <Table
              data={mappings}
              columns={mappingColumns}
              loading={mappingsLoading}
              emptyMessage="Tidak ada mapping ditemukan"
            />
          )}
        </div>
      )}
    </div>
  );
};

export default EnhancedDatabasePage;

