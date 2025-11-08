/**
 * Permission Management Page
 * Halaman utama untuk manage permissions dengan Tailwind CSS
 */

import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useGetPermissionStatsQuery,
  useGetRolesQuery,
} from '../store';
import { Button, Input, Table } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { Role } from '../types';

const PermissionManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('all');
  const [filterType, setFilterType] = useState('all');

  const { data: stats } = useGetPermissionStatsQuery();
  const { data: roles = [], isLoading } = useGetRolesQuery();

  const departments = useMemo(() => {
    return Array.from(new Set(roles.map(role => role.department_name).filter(Boolean))) as string[];
  }, [roles]);

  const filteredRoles = useMemo(() => {
    return roles.filter(role => {
      const matchesSearch = role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           role.code.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesDepartment = filterDepartment === 'all' || 
                               role.department_name === filterDepartment;
      const matchesType = filterType === 'all' || 
                         (filterType === 'system' && role.is_system_role) ||
                         (filterType === 'custom' && !role.is_system_role);
      
      return matchesSearch && matchesDepartment && matchesType;
    });
  }, [roles, searchTerm, filterDepartment, filterType]);

  const columns = [
    {
      key: 'name',
      label: 'Role',
      render: (_value: any, item: Role) => (
        <div>
          <div className="font-medium text-gray-900">{item.name}</div>
          <div className="text-xs text-gray-500">{item.code}</div>
        </div>
      ),
    },
    {
      key: 'department',
      label: 'Department',
      render: (_value: any, item: Role) => (
        <span>{item.department_name || '-'}</span>
      ),
    },
    {
      key: 'level',
      label: 'Level',
      render: (_value: any, item: Role) => (
        <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
          Level {item.level}
        </span>
      ),
    },
    {
      key: 'permissions',
      label: 'Permissions',
      render: (_value: any, item: Role) => (
        <span className="font-semibold">{item.permissions_count || 0}</span>
      ),
    },
    {
      key: 'users',
      label: 'Users',
      render: (_value: any, item: Role) => (
        <span className="font-semibold">{item.users_count || 0}</span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: Role) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {item.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_value: any, item: Role) => (
        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate(`/roles/${item.id}/permissions`)}
        >
          Manage Permissions
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🔐 Permission Management</h1>
            <p className="text-gray-600">Kelola permissions dan hak akses untuk semua roles dalam sistem</p>
          </div>
          <Button
            variant="primary"
            onClick={() => navigate('/permissions/overview')}
          >
            📋 Lihat Semua Permissions
          </Button>
        </div>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Total Permissions</div>
            <div className="text-2xl font-bold text-gray-800">{stats.total_permissions}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Total Roles</div>
            <div className="text-2xl font-bold text-blue-600">{stats.total_roles}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Active</div>
            <div className="text-2xl font-bold text-green-600">{stats.active_permissions}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Inactive</div>
            <div className="text-2xl font-bold text-red-600">{stats.inactive_permissions}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">System</div>
            <div className="text-2xl font-bold text-purple-600">{stats.system_permissions}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Custom</div>
            <div className="text-2xl font-bold text-orange-600">{stats.custom_permissions}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Most Used</div>
            <div className="text-xs text-gray-500">
              {stats.most_used_permissions.slice(0, 3).map((p, idx) => (
                <div key={idx} className="truncate">{p.permission}: {p.count}</div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Input
              type="text"
              placeholder="Cari role..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div>
            <select
              value={filterDepartment}
              onChange={(e) => setFilterDepartment(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Department</option>
              {departments.map((dept) => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>
          <div>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">Semua Tipe</option>
              <option value="system">System Role</option>
              <option value="custom">Custom Role</option>
            </select>
          </div>
        </div>
      </div>

      {/* Roles Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">
            Roles ({filteredRoles.length})
          </h2>
        </div>
        <Table
          data={filteredRoles}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada role ditemukan"
        />
      </div>
    </div>
  );
};

export default PermissionManagementPage;

