/**
 * Permission Overview Page
 * Halaman untuk melihat semua permissions dengan Tailwind CSS
 */

import React, { useState, useMemo } from 'react';
import {
  useGetPermissionsQuery,
  useBulkUpdatePermissionsMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table, Pagination } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { Permission } from '../types';

const PermissionOverviewPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [filters, setFilters] = useState({
    search: '',
    module: 'all',
    action: 'all',
    resource_type: 'all',
    is_system: 'all',
    is_active: 'all',
  });
  const [selectedPermissions, setSelectedPermissions] = useState<number[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  const { data: permissions = [], isLoading, refetch } = useGetPermissionsQuery();
  const [bulkUpdate] = useBulkUpdatePermissionsMutation();

  const modules = useMemo(() => {
    return Array.from(new Set(permissions.map(p => p.module)));
  }, [permissions]);

  const actions = useMemo(() => {
    return Array.from(new Set(permissions.map(p => p.action)));
  }, [permissions]);

  const resourceTypes = useMemo(() => {
    return Array.from(new Set(permissions.map(p => p.resource_type)));
  }, [permissions]);

  const filteredPermissions = useMemo(() => {
    return permissions.filter(permission => {
      const matchesSearch = permission.module.toLowerCase().includes(filters.search.toLowerCase()) ||
                           permission.action.toLowerCase().includes(filters.search.toLowerCase()) ||
                           permission.resource_type.toLowerCase().includes(filters.search.toLowerCase()) ||
                           permission.description.toLowerCase().includes(filters.search.toLowerCase());
      
      const matchesModule = filters.module === 'all' || permission.module === filters.module;
      const matchesAction = filters.action === 'all' || permission.action === filters.action;
      const matchesResource = filters.resource_type === 'all' || permission.resource_type === filters.resource_type;
      const matchesSystem = filters.is_system === 'all' || 
                           (filters.is_system === 'system' && permission.is_system_permission) ||
                           (filters.is_system === 'custom' && !permission.is_system_permission);
      const matchesActive = filters.is_active === 'all' ||
                           (filters.is_active === 'active' && permission.is_active) ||
                           (filters.is_active === 'inactive' && !permission.is_active);
      
      return matchesSearch && matchesModule && matchesAction && matchesResource && matchesSystem && matchesActive;
    });
  }, [permissions, filters]);

  const totalPages = Math.ceil(filteredPermissions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentPagePermissions = filteredPermissions.slice(startIndex, startIndex + itemsPerPage);

  const handleBulkActivate = async () => {
    if (selectedPermissions.length === 0) {
      await sweetAlert.showError('Error', 'Pilih permissions terlebih dahulu');
      return;
    }

    try {
      await bulkUpdate({ permissionIds: selectedPermissions, isActive: true }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Permissions berhasil diaktifkan');
      setSelectedPermissions([]);
      refetch();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal mengaktifkan permissions');
    }
  };

  const handleBulkDeactivate = async () => {
    if (selectedPermissions.length === 0) {
      await sweetAlert.showError('Error', 'Pilih permissions terlebih dahulu');
      return;
    }

    try {
      await bulkUpdate({ permissionIds: selectedPermissions, isActive: false }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Permissions berhasil dinonaktifkan');
      setSelectedPermissions([]);
      refetch();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal menonaktifkan permissions');
    }
  };

  const columns = [
    {
      key: 'select',
      label: '',
      render: (_value: any, item: Permission) => (
        <input
          type="checkbox"
          checked={selectedPermissions.includes(item.id)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedPermissions(prev => [...prev, item.id]);
            } else {
              setSelectedPermissions(prev => prev.filter(id => id !== item.id));
            }
          }}
          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
      ),
    },
    {
      key: 'permission',
      label: 'Permission',
      render: (_value: any, item: Permission) => (
        <div>
          <div className="font-medium text-gray-900">{item.module}.{item.action}</div>
          <div className="text-xs text-gray-500">{item.resource_type}</div>
        </div>
      ),
    },
    {
      key: 'description',
      label: 'Description',
      render: (_value: any, item: Permission) => (
        <span className="text-sm">{item.description}</span>
      ),
    },
    {
      key: 'usage',
      label: 'Usage',
      render: (_value: any, item: Permission) => (
        <div className="text-sm">
          <div>Roles: {item.roles_count || 0}</div>
          <div>Usage: {item.usage_count || 0}</div>
        </div>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: Permission) => (
        <div className="space-y-1">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
          }`}>
            {item.is_active ? 'Active' : 'Inactive'}
          </span>
          {item.is_system_permission && (
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 block mt-1">
              System
            </span>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📋 Permission Overview</h1>
            <p className="text-gray-600">Lihat dan kelola semua permissions dalam sistem</p>
          </div>
          {selectedPermissions.length > 0 && (
            <div className="flex gap-2">
              <Button
                variant="primary"
                size="sm"
                onClick={handleBulkActivate}
              >
                ✅ Activate Selected
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleBulkDeactivate}
              >
                ❌ Deactivate Selected
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <Input
              type="text"
              placeholder="Cari permission..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            />
          </div>
          <div>
            <select
              value={filters.module}
              onChange={(e) => setFilters(prev => ({ ...prev, module: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Module</option>
              {modules.map((module) => (
                <option key={module} value={module}>{module}</option>
              ))}
            </select>
          </div>
          <div>
            <select
              value={filters.action}
              onChange={(e) => setFilters(prev => ({ ...prev, action: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Action</option>
              {actions.map((action) => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
          </div>
          <div>
            <select
              value={filters.is_system}
              onChange={(e) => setFilters(prev => ({ ...prev, is_system: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Tipe</option>
              <option value="system">System</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div>
            <select
              value={filters.is_active}
              onChange={(e) => setFilters(prev => ({ ...prev, is_active: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={currentPagePermissions}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada permission ditemukan"
        />
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {startIndex + 1} - {Math.min(startIndex + itemsPerPage, filteredPermissions.length)} dari {filteredPermissions.length} permissions
            </div>
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={(page) => {
                setCurrentPage(page);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default PermissionOverviewPage;

