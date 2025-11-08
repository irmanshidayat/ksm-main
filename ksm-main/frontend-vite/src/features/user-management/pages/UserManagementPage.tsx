/**
 * User Management Page
 * Halaman untuk mengelola users dengan Tailwind CSS
 */

import React, { useState } from 'react';
import {
  useGetUsersQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeleteUserMutation,
  useGetDepartmentsQuery,
  useGetRolesQuery,
  useGetUserRolesQuery,
  useAssignRoleToUserMutation,
  useRemoveRoleFromUserMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { User, CreateUserRequest } from '../types';

const UserManagementPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [filters, setFilters] = useState({
    search: '',
    role: '',
    is_active: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    password: '',
    email: '',
    role_id: undefined,
  });

  const { data: usersData, isLoading, refetch } = useGetUsersQuery({
    page: currentPage,
    per_page: itemsPerPage,
    ...filters,
  });
  const { data: departments } = useGetDepartmentsQuery();
  const { data: roles } = useGetRolesQuery();
  const { data: userRoles, refetch: refetchUserRoles } = useGetUserRolesQuery(selectedUser?.id || 0, {
    skip: !selectedUser,
  });

  const [createUser] = useCreateUserMutation();
  const [updateUser] = useUpdateUserMutation();
  const [deleteUser] = useDeleteUserMutation();
  const [assignRole] = useAssignRoleToUserMutation();
  const [removeRole] = useRemoveRoleFromUserMutation();

  const users = Array.isArray(usersData) ? usersData : usersData?.items || [];
  const pagination = Array.isArray(usersData) ? null : usersData?.pagination;

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password || !formData.email) {
      await sweetAlert.showError('Error', 'Username, password, dan email wajib diisi');
      return;
    }

    try {
      const result = await createUser(formData).unwrap();
      if (result && formData.role_id) {
        await assignRole({ userId: result.id, roleId: formData.role_id }).unwrap();
      }
      await sweetAlert.showSuccessAuto('Berhasil', 'User berhasil dibuat');
      setShowCreateForm(false);
      setFormData({ username: '', password: '', email: '', role_id: undefined });
      refetch();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal membuat user');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus',
      'Apakah Anda yakin ingin menghapus user ini?',
      'warning'
    );

    if (confirmed) {
      try {
        await deleteUser(userId).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'User berhasil dihapus');
        refetch();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus user');
      }
    }
  };

  const handleAssignRole = async (userId: number, roleId: number) => {
    try {
      await assignRole({ userId, roleId }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Role berhasil diassign');
      if (selectedUser?.id === userId) {
        refetchUserRoles();
      }
      refetch();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal assign role');
    }
  };

  const handleRemoveRole = async (userId: number, userRoleId: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus Role',
      'Apakah Anda yakin ingin menghapus role ini dari user?',
      'warning'
    );

    if (confirmed) {
      try {
        await removeRole({ userId, userRoleId }).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Role berhasil dihapus');
        refetchUserRoles();
        refetch();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus role');
      }
    }
  };

  const columns = [
    {
      key: 'username',
      label: 'Username',
      render: (_value: any, item: User) => (
        <span className="font-medium">{item.username}</span>
      ),
    },
    {
      key: 'email',
      label: 'Email',
      render: (_value: any, item: User) => item.email || '-',
    },
    {
      key: 'role',
      label: 'Role',
      render: (_value: any, item: User) => (
        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
          {item.role_details?.name || item.role || 'N/A'}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: User) => (
        <span className={`px-2 py-1 rounded-full text-xs ${
          item.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {item.is_active !== false ? 'Aktif' : 'Tidak Aktif'}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: User) => (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedUser(item)}
          >
            👁️ Detail
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => handleDeleteUser(item.id)}
          >
            🗑️ Hapus
          </Button>
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">👥 User Management</h1>
            <p className="text-gray-600">Kelola users dan roles</p>
          </div>
          <Button
            variant="primary"
            onClick={() => setShowCreateForm(true)}
          >
            ➕ Tambah User
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input
            type="text"
            placeholder="Cari username atau email..."
            value={filters.search}
            onChange={(e) => {
              setFilters(prev => ({ ...prev, search: e.target.value }));
              setCurrentPage(1);
            }}
          />
          <select
            value={filters.role}
            onChange={(e) => {
              setFilters(prev => ({ ...prev, role: e.target.value }));
              setCurrentPage(1);
            }}
            className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Semua Role</option>
            {roles?.map(role => (
              <option key={role.id} value={role.name}>{role.name}</option>
            ))}
          </select>
          <select
            value={filters.is_active}
            onChange={(e) => {
              setFilters(prev => ({ ...prev, is_active: e.target.value }));
              setCurrentPage(1);
            }}
            className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Semua Status</option>
            <option value="true">Aktif</option>
            <option value="false">Tidak Aktif</option>
          </select>
        </div>
      </div>

      {/* Create User Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Tambah User</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowCreateForm(false);
                    setFormData({ username: '', password: '', email: '', role_id: undefined });
                  }}
                >
                  ✕
                </Button>
              </div>
              <form onSubmit={handleCreateUser} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Username *</label>
                  <Input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email *</label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Password *</label>
                  <Input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
                  <select
                    value={formData.role_id || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, role_id: e.target.value ? parseInt(e.target.value) : undefined }))}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Pilih Role</option>
                    {roles?.map(role => (
                      <option key={role.id} value={role.id}>{role.name}</option>
                    ))}
                  </select>
                </div>
                <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowCreateForm(false);
                      setFormData({ username: '', password: '', email: '', role_id: undefined });
                    }}
                  >
                    Batal
                  </Button>
                  <Button type="submit" variant="primary">
                    Simpan
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* User Detail Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Detail User: {selectedUser.username}</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedUser(null)}
                >
                  ✕
                </Button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                  <p className="text-gray-800">{selectedUser.username}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <p className="text-gray-800">{selectedUser.email || '-'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <p className="text-gray-800">{selectedUser.role_details?.name || selectedUser.role || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <p className="text-gray-800">{selectedUser.is_active !== false ? 'Aktif' : 'Tidak Aktif'}</p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">User Roles</h3>
                  <div className="space-y-2">
                    {userRoles && userRoles.length > 0 ? (
                      userRoles.map(userRole => (
                        <div key={userRole.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <span className="text-sm">{userRole.role?.name || 'N/A'}</span>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleRemoveRole(selectedUser.id, userRole.id)}
                          >
                            Hapus
                          </Button>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500">Belum ada role yang diassign</p>
                    )}
                  </div>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Assign Role Baru</label>
                    <div className="flex gap-2">
                      <select
                        id="assign-role-select"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Pilih Role</option>
                        {roles?.map(role => (
                          <option key={role.id} value={role.id}>{role.name}</option>
                        ))}
                      </select>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          const select = document.getElementById('assign-role-select') as HTMLSelectElement;
                          const roleId = parseInt(select.value);
                          if (roleId) {
                            handleAssignRole(selectedUser.id, roleId);
                            select.value = '';
                          }
                        }}
                      >
                        Assign
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <Table
          data={users}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada user ditemukan"
        />
      </div>
    </div>
  );
};

export default UserManagementPage;

