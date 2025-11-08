/**
 * Permission Matrix Page
 * Halaman untuk manage permissions untuk role tertentu dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  useGetRoleByIdQuery,
  useGetRolePermissionsQuery,
  useUpdateRolePermissionsMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { LoadingSpinner } from '@/shared/components/feedback';
import { Button } from '@/shared/components/ui';
import type { PermissionMatrixItem } from '../types';

const PermissionMatrixPage: React.FC = () => {
  const { roleId } = useParams<{ roleId: string }>();
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [permissions, setPermissions] = useState<PermissionMatrixItem[]>([]);
  const [hasChanges, setHasChanges] = useState(false);

  const roleIdNum = roleId ? parseInt(roleId) : 0;
  const { data: role, isLoading: roleLoading } = useGetRoleByIdQuery(roleIdNum, { skip: !roleIdNum });
  const { data: rolePermissions = [], isLoading: permissionsLoading, refetch } = useGetRolePermissionsQuery(roleIdNum, { skip: !roleIdNum });
  const [updatePermissions, { isLoading: saving }] = useUpdateRolePermissionsMutation();

  useEffect(() => {
    if (rolePermissions.length > 0) {
      setPermissions(JSON.parse(JSON.stringify(rolePermissions)));
      setHasChanges(false);
    }
  }, [rolePermissions]);

  const handleTogglePermission = (permissionId: number) => {
    setPermissions(prev => prev.map(p => 
      p.permission_id === permissionId 
        ? { ...p, is_granted: !p.is_granted }
        : p
    ));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await updatePermissions({
        roleId: roleIdNum,
        data: {
          permissions: permissions.map(p => ({
            permission_id: p.permission_id,
            is_granted: p.is_granted,
          })),
        },
      }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Permissions berhasil diupdate');
      setHasChanges(false);
      refetch();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal update permissions');
    }
  };

  const groupedPermissions = permissions.reduce((acc, perm) => {
    if (!acc[perm.module]) {
      acc[perm.module] = [];
    }
    acc[perm.module].push(perm);
    return acc;
  }, {} as Record<string, PermissionMatrixItem[]>);

  if (roleLoading || permissionsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!role) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Role tidak ditemukan</h2>
          <Button variant="primary" onClick={() => navigate('/permissions')}>
            Kembali ke Permission Management
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">
              🔐 Permission Matrix - {role.name}
            </h1>
            <p className="text-gray-600">Kelola permissions untuk role ini</p>
          </div>
          <div className="flex gap-2">
            {hasChanges && (
              <Button
                variant="primary"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : '💾 Save Changes'}
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => navigate('/permissions')}
            >
              ← Kembali
            </Button>
          </div>
        </div>
      </div>

      {/* Role Info */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-600 mb-1">Department</div>
            <div className="font-semibold">{role.department_name || '-'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">Level</div>
            <div className="font-semibold">Level {role.level}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">Permissions</div>
            <div className="font-semibold">{permissions.filter(p => p.is_granted).length} / {permissions.length}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">Status</div>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              role.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
            }`}>
              {role.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
      </div>

      {/* Permission Matrix */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">Permissions by Module</h2>
        </div>
        <div className="p-6 space-y-6">
          {Object.entries(groupedPermissions).map(([module, modulePermissions]) => (
            <div key={module} className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-4">{module}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {modulePermissions.map((perm) => (
                  <div
                    key={perm.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      perm.is_granted
                        ? 'bg-green-50 border-green-300'
                        : 'bg-gray-50 border-gray-300'
                    }`}
                    onClick={() => handleTogglePermission(perm.permission_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-sm text-gray-900">
                          {perm.action}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {perm.resource_type}
                        </div>
                        {perm.description && (
                          <div className="text-xs text-gray-400 mt-1">
                            {perm.description}
                          </div>
                        )}
                      </div>
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                        perm.is_granted
                          ? 'bg-green-500 border-green-600'
                          : 'bg-white border-gray-400'
                      }`}>
                        {perm.is_granted && (
                          <span className="text-white text-xs">✓</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PermissionMatrixPage;

