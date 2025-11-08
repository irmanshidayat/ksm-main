/**
 * Role Management Page
 * Halaman untuk mengelola roles, departments, dan permissions dengan Tailwind CSS
 */

import React, { useState } from 'react';
import {
  useGetRolesQuery,
  useGetDepartmentsQuery,
  useGetPermissionsQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,
  useCreateDepartmentMutation,
  useUpdateDepartmentMutation,
  useDeleteDepartmentMutation,
  useGetRolePermissionsQuery,
  useAssignPermissionToRoleMutation,
  useRemovePermissionFromRoleMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { LevelPermissionMatrixPage } from '@/features/permission-management';
import type { Role, Department, Permission } from '../types';

const RoleManagementPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [activeTab, setActiveTab] = useState<'roles' | 'departments' | 'permissions' | 'level-role-management'>('roles');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null);
  const [formData, setFormData] = useState<any>({});

  const { data: roles, isLoading: loadingRoles, refetch: refetchRoles } = useGetRolesQuery();
  const { data: departments, isLoading: loadingDepartments, refetch: refetchDepartments } = useGetDepartmentsQuery();
  const { data: permissions, isLoading: loadingPermissions } = useGetPermissionsQuery();
  const { data: rolePermissions, refetch: refetchRolePermissions } = useGetRolePermissionsQuery(selectedRole?.id || 0, {
    skip: !selectedRole,
  });


  const [createRole] = useCreateRoleMutation();
  const [updateRole] = useUpdateRoleMutation();
  const [deleteRole] = useDeleteRoleMutation();
  const [createDepartment] = useCreateDepartmentMutation();
  const [updateDepartment] = useUpdateDepartmentMutation();
  const [deleteDepartment] = useDeleteDepartmentMutation();
  const [assignPermission] = useAssignPermissionToRoleMutation();
  const [removePermission] = useRemovePermissionFromRoleMutation();

  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.code || !formData.department_id) {
      await sweetAlert.showError('Error', 'Nama, code, dan department wajib diisi');
      return;
    }

    try {
      await createRole({
        name: formData.name,
        code: formData.code,
        department_id: parseInt(formData.department_id),
        description: formData.description || '',
        level: parseInt(formData.level || '1'),
        is_management: formData.is_management === 'true',
      }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Role berhasil dibuat');
      setShowCreateForm(false);
      setFormData({});
      refetchRoles();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal membuat role');
    }
  };

  const handleCreateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.code) {
      await sweetAlert.showError('Error', 'Nama dan code wajib diisi');
      return;
    }

    try {
      await createDepartment({
        name: formData.name,
        code: formData.code,
        description: formData.description || '',
        level: parseInt(formData.level || '1'),
      }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Department berhasil dibuat');
      setShowCreateForm(false);
      setFormData({});
      refetchDepartments();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal membuat department');
    }
  };

  const handleDeleteRole = async (roleId: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus',
      'Apakah Anda yakin ingin menghapus role ini?',
      'warning'
    );

    if (confirmed) {
      try {
        await deleteRole(roleId).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Role berhasil dihapus');
        refetchRoles();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus role');
      }
    }
  };

  const handleDeleteDepartment = async (departmentId: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus',
      'Apakah Anda yakin ingin menghapus department ini?',
      'warning'
    );

    if (confirmed) {
      try {
        await deleteDepartment(departmentId).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Department berhasil dihapus');
        refetchDepartments();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus department');
      }
    }
  };

  const handleAssignPermission = async (roleId: number, permissionId: number) => {
    try {
      await assignPermission({ roleId, permissionId }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Permission berhasil diassign');
      refetchRolePermissions();
      refetchRoles();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal assign permission');
    }
  };

  const handleRemovePermission = async (roleId: number, permissionId: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus Permission',
      'Apakah Anda yakin ingin menghapus permission ini dari role?',
      'warning'
    );

    if (confirmed) {
      try {
        await removePermission({ roleId, permissionId }).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Permission berhasil dihapus');
        refetchRolePermissions();
        refetchRoles();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus permission');
      }
    }
  };

  const roleColumns = [
    {
      key: 'name',
      label: 'Nama',
      render: (_value: any, item: Role) => (
        <span className="font-medium">{item.name}</span>
      ),
    },
    {
      key: 'code',
      label: 'Code',
      render: (_value: any, item: Role) => item.code,
    },
    {
      key: 'department',
      label: 'Department',
      render: (_value: any, item: Role) => item.department_name || 'N/A',
    },
    {
      key: 'level',
      label: 'Level',
      render: (_value: any, item: Role) => item.level,
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: Role) => (
        <span className={`px-2 py-1 rounded-full text-xs ${
          item.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {item.is_active ? 'Aktif' : 'Tidak Aktif'}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: Role) => (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setSelectedRole(item);
              setShowCreateForm(false);
            }}
          >
            👁️ Detail
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => handleDeleteRole(item.id)}
            disabled={item.is_system_role}
          >
            🗑️ Hapus
          </Button>
        </div>
      ),
    },
  ];

  const departmentColumns = [
    {
      key: 'name',
      label: 'Nama',
      render: (_value: any, item: Department) => (
        <span className="font-medium">{item.name}</span>
      ),
    },
    {
      key: 'code',
      label: 'Code',
      render: (_value: any, item: Department) => item.code,
    },
    {
      key: 'level',
      label: 'Level',
      render: (_value: any, item: Department) => item.level,
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: Department) => (
        <span className={`px-2 py-1 rounded-full text-xs ${
          item.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {item.is_active ? 'Aktif' : 'Tidak Aktif'}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Aksi',
      render: (_value: any, item: Department) => (
        <Button
          variant="danger"
          size="sm"
          onClick={() => handleDeleteDepartment(item.id)}
        >
          🗑️ Hapus
        </Button>
      ),
    },
  ];

  const isLoading = loadingRoles || loadingDepartments || loadingPermissions;

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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🔐 Role Management</h1>
            <p className="text-gray-600">Kelola roles, departments, dan permissions</p>
          </div>
          <Button
            variant="primary"
            onClick={() => {
              setShowCreateForm(true);
              setSelectedRole(null);
              setSelectedDepartment(null);
              setFormData({});
            }}
          >
            ➕ {activeTab === 'roles' ? 'Tambah Role' : activeTab === 'departments' ? 'Tambah Department' : 'Tambah Permission'}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex gap-2 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('roles')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'roles'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Roles
          </button>
          <button
            onClick={() => setActiveTab('departments')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'departments'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Departments
          </button>
          <button
            onClick={() => setActiveTab('permissions')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'permissions'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Permissions
          </button>
          <button
            onClick={() => setActiveTab('level-role-management')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'level-role-management'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Level Role Management
          </button>
        </div>
      </div>

      {/* Create Form Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">
                  {activeTab === 'roles' ? 'Tambah Role' : 'Tambah Department'}
                </h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowCreateForm(false);
                    setFormData({});
                  }}
                >
                  ✕
                </Button>
              </div>
              <form onSubmit={activeTab === 'roles' ? handleCreateRole : handleCreateDepartment} className="space-y-4">
                {activeTab === 'roles' ? (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Nama Role *</label>
                      <Input
                        type="text"
                        value={formData.name || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Code *</label>
                      <Input
                        type="text"
                        value={formData.code || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value }))}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Department *</label>
                      <select
                        value={formData.department_id || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, department_id: e.target.value }))}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        required
                      >
                        <option value="">Pilih Department</option>
                        {departments?.map(dept => (
                          <option key={dept.id} value={dept.id}>{dept.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Level</label>
                      <Input
                        type="number"
                        value={formData.level || '1'}
                        onChange={(e) => setFormData(prev => ({ ...prev, level: e.target.value }))}
                        min="1"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Is Management</label>
                      <select
                        value={formData.is_management || 'false'}
                        onChange={(e) => setFormData(prev => ({ ...prev, is_management: e.target.value }))}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="false">Tidak</option>
                        <option value="true">Ya</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                      <textarea
                        value={formData.description || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        rows={3}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Nama Department *</label>
                      <Input
                        type="text"
                        value={formData.name || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Code *</label>
                      <Input
                        type="text"
                        value={formData.code || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value }))}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Level</label>
                      <Input
                        type="number"
                        value={formData.level || '1'}
                        onChange={(e) => setFormData(prev => ({ ...prev, level: e.target.value }))}
                        min="1"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                      <textarea
                        value={formData.description || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        rows={3}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                      />
                    </div>
                  </>
                )}
                <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowCreateForm(false);
                      setFormData({});
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

      {/* Role Detail Modal */}
      {selectedRole && !showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Detail Role: {selectedRole.name}</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedRole(null)}
                >
                  ✕
                </Button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nama</label>
                  <p className="text-gray-800">{selectedRole.name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Code</label>
                  <p className="text-gray-800">{selectedRole.code}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                  <p className="text-gray-800">{selectedRole.department_name || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Level</label>
                  <p className="text-gray-800">{selectedRole.level}</p>
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Role Permissions</h3>
                  <div className="space-y-2 mb-4">
                    {rolePermissions && rolePermissions.length > 0 ? (
                      rolePermissions.map((rp, index) => {
                        // Data yang diterima adalah Menu Permissions, bukan Role Permissions
                        // Struktur: menu_id, menu_name, menu_path, permissions: {can_read, can_create, can_update, can_delete}
                        
                        // Get permission name dari menu_name (ini adalah menu permissions)
                        let permissionName = 'N/A';
                        
                        // Priority 1: Check menu_name (ini yang paling reliable untuk menu permissions)
                        if ((rp as any).menu_name) {
                          permissionName = (rp as any).menu_name;
                        }
                        // Priority 2: Check flat fields (module, action) di root - untuk role permissions
                        else if ((rp as any).module && (rp as any).action) {
                          const mod = (rp as any).module;
                          const act = (rp as any).action;
                          const desc = (rp as any).description;
                          permissionName = desc || `${mod} - ${act}`;
                        }
                        // Priority 3: Check nested permission object
                        else if (rp.permission) {
                          permissionName = rp.permission.description || 
                            `${rp.permission.module || 'Unknown'} - ${rp.permission.action || 'Unknown'}`;
                        }
                        // Priority 4: Check description field langsung
                        else if ((rp as any).description) {
                          permissionName = (rp as any).description;
                        }
                        // Priority 5: Lookup dari permissions list menggunakan permission_id
                        else if (rp.permission_id) {
                          const perm = permissions?.find(p => p.id === rp.permission_id);
                          if (perm) {
                            permissionName = perm.description || `${perm.module} - ${perm.action}`;
                          } else {
                            permissionName = `Permission ID: ${rp.permission_id}`;
                          }
                        }
                        
                        // Get menu_id atau permission_id untuk tombol hapus
                        const itemId = (rp as any).menu_id || rp.permission_id || (rp as any).id;
                        
                        // Gunakan kombinasi id dan index untuk key yang unik
                        const uniqueKey = itemId ? `rp-${itemId}-${index}` : `rp-${index}`;
                        
                        return (
                          <div key={uniqueKey} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <span className="text-sm font-medium text-gray-800">{permissionName}</span>
                            <Button
                              variant="danger"
                              size="sm"
                              onClick={() => {
                                // Untuk menu permissions, gunakan menu_id
                                // Untuk role permissions, gunakan permission_id
                                const idToRemove = (rp as any).menu_id || rp.permission_id;
                                if (idToRemove) {
                                  handleRemovePermission(selectedRole.id, idToRemove);
                                }
                              }}
                            >
                              Hapus
                            </Button>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-sm text-gray-500">Belum ada permission yang diassign</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Assign Permission Baru</label>
                    <div className="flex gap-2">
                      <select
                        id="assign-permission-select"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Pilih Permission</option>
                        {permissions?.filter(p => !rolePermissions?.some(rp => rp.permission_id === p.id)).map(permission => (
                          <option key={permission.id} value={permission.id}>
                            {permission.module} - {permission.action}
                          </option>
                        ))}
                      </select>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          const select = document.getElementById('assign-permission-select') as HTMLSelectElement;
                          const permissionId = parseInt(select.value);
                          if (permissionId) {
                            handleAssignPermission(selectedRole.id, permissionId);
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

      {/* Content */}
      {activeTab === 'roles' && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <Table
            data={roles || []}
            columns={roleColumns}
            loading={loadingRoles}
            emptyMessage="Tidak ada role ditemukan"
          />
        </div>
      )}

      {activeTab === 'departments' && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <Table
            data={departments || []}
            columns={departmentColumns}
            loading={loadingDepartments}
            emptyMessage="Tidak ada department ditemukan"
          />
        </div>
      )}

      {activeTab === 'permissions' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Permissions</h2>
          <div className="space-y-2">
            {permissions && permissions.length > 0 ? (
              permissions.map(permission => (
                <div key={permission.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-800">{permission.module} - {permission.action}</h3>
                      <p className="text-sm text-gray-600 mt-1">{permission.description}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      permission.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {permission.is_active ? 'Aktif' : 'Tidak Aktif'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-center py-8 text-gray-500">Tidak ada permission ditemukan</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'level-role-management' && (
        <LevelPermissionMatrixPage />
      )}
    </div>
  );
};

export default RoleManagementPage;

