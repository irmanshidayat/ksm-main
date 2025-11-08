/**
 * Level Permission Matrix Page
 * Halaman untuk mengelola template permissions berdasarkan level role dengan Tailwind CSS
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useGetMenusQuery,
  useGetLevelTemplateQuery,
  useUpdateLevelTemplateMutation,
  useUpdateMenuSidebarVisibilityGlobalMutation,
  useBulkUpdateMenuOrderMutation,
  permissionApi,
} from '../store';
import { useAppDispatch } from '@/app/store/hooks';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { PermissionMatrix } from '../components';
import type { LevelPermissionMatrixItem } from '../types';

const LevelPermissionMatrixPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const dispatch = useAppDispatch();
  const [level, setLevel] = useState<number>(1);
  const [menus, setMenus] = useState<LevelPermissionMatrixItem[]>([]);
  const [search, setSearch] = useState<string>('');

  const { data: dbMenus = [], isLoading: menusLoading, refetch: refetchMenus } = useGetMenusQuery();
  const { data: template, isLoading: templateLoading, refetch: refetchTemplate } = useGetLevelTemplateQuery(level, {
    skip: !level,
  });
  const [updateTemplate, { isLoading: saving }] = useUpdateLevelTemplateMutation();
  const [updateSidebarGlobal, { isLoading: updatingSidebar }] = useUpdateMenuSidebarVisibilityGlobalMutation();
  const [bulkUpdateMenuOrder, { isLoading: updatingOrder }] = useBulkUpdateMenuOrderMutation();

  useEffect(() => {
    if (dbMenus.length > 0 && template) {
      const map: Record<number, any> = {};
      template.permissions.forEach((p: any) => {
        if (p.menu_id) map[p.menu_id] = p.permissions || {};
      });
      const merged = dbMenus.map(m => ({
        ...m,
        permissions: {
          can_read: !!map[m.menu_id]?.can_read,
          can_create: !!map[m.menu_id]?.can_create,
          can_update: !!map[m.menu_id]?.can_update,
          can_delete: !!map[m.menu_id]?.can_delete,
          show_in_sidebar: map[m.menu_id]?.show_in_sidebar !== false, // Default true jika tidak ada
        }
      }));
      setMenus(merged);
    } else if (dbMenus.length > 0) {
      setMenus(dbMenus.map(m => ({
        ...m,
        permissions: {
          can_read: m.permissions?.can_read || false,
          can_create: m.permissions?.can_create || false,
          can_update: m.permissions?.can_update || false,
          can_delete: m.permissions?.can_delete || false,
          show_in_sidebar: m.permissions?.show_in_sidebar !== false, // Default true jika tidak ada
        }
      })));
    }
  }, [dbMenus, template]);

  useEffect(() => {
    if (level) {
      refetchTemplate();
    }
  }, [level, refetchTemplate]);

  const filteredMenus = useMemo(() => {
    return menus.filter(m => 
      m.menu_name.toLowerCase().includes(search.toLowerCase()) || 
      m.menu_path.toLowerCase().includes(search.toLowerCase())
    );
  }, [menus, search]);

  const updatePerm = (menuId: number, key: keyof LevelPermissionMatrixItem['permissions'], value: boolean) => {
    setMenus(prev => prev.map(m => 
      m.menu_id === menuId 
        ? { ...m, permissions: { ...m.permissions, [key]: value } } 
        : m
    ));
  };

  const setRowAll = (menuId: number, value: boolean) => {
    setMenus(prev => prev.map(m => 
      m.menu_id === menuId 
        ? {
            ...m,
            permissions: {
              ...m.permissions,
              can_read: value,
              can_create: value,
              can_update: value,
              can_delete: value
            }
          } 
        : m
    ));
  };

  const updateSidebarVisibility = async (menuId: number, value: boolean) => {
    try {
      // Update state lokal terlebih dahulu untuk UX yang lebih baik
      setMenus(prev => prev.map(m => 
        m.menu_id === menuId 
          ? { ...m, permissions: { ...m.permissions, show_in_sidebar: value } } 
          : m
      ));

      // Panggil API global untuk update semua role
      await updateSidebarGlobal({
        menuId,
        showInSidebar: value,
      }).unwrap();

      // Invalidate cache untuk memastikan Sidebar langsung refresh
      dispatch(permissionApi.util.invalidateTags(['Permission']));

      await sweetAlert.showSuccessAuto(
        'Berhasil',
        `Menu ${menus.find(m => m.menu_id === menuId)?.menu_name || ''} ${value ? 'ditampilkan' : 'disembunyikan'} di sidebar untuk semua role`
      );
    } catch (error: any) {
      // Rollback state lokal jika error
      setMenus(prev => prev.map(m => 
        m.menu_id === menuId 
          ? { ...m, permissions: { ...m.permissions, show_in_sidebar: !value } } 
          : m
      ));
      await sweetAlert.showError('Gagal', error?.message || 'Gagal memperbarui visibility sidebar');
    }
  };

  const handleChangeLevel = (val: number) => {
    setLevel(val);
  };

  const handleReorder = async (rootMenuId: number, newOrder: LevelPermissionMatrixItem[]) => {
    try {
      // Update local state first for better UX
      setMenus(prev => {
        const updated = [...prev];
        newOrder.forEach((item, index) => {
          const menuIndex = updated.findIndex(m => m.menu_id === item.menu_id);
          if (menuIndex !== -1) {
            updated[menuIndex] = { ...updated[menuIndex], order_index: item.order_index };
          }
        });
        return updated;
      });

      // Prepare menu orders for bulk update
      const menuOrders = newOrder.map((item, index) => ({
        menu_id: item.menu_id,
        order_index: item.order_index || index + 1,
      }));

      // Call API to save order
      await bulkUpdateMenuOrder({ menu_orders: menuOrders }).unwrap();

      // Invalidate cache to refresh menus
      dispatch(permissionApi.util.invalidateTags(['Permission']));

      // Show success message
      await sweetAlert.showSuccessAuto(
        'Berhasil',
        'Urutan menu berhasil diperbarui'
      );
    } catch (error: any) {
      // Rollback on error - refetch menus
      refetchMenus();
      await sweetAlert.showError('Gagal', error?.message || 'Gagal memperbarui urutan menu');
    }
  };

  const handleReorderBoxes = async (newOrder: LevelPermissionMatrixItem[]) => {
    try {
      // Update local state first for better UX
      setMenus(prev => {
        const updated = [...prev];
        newOrder.forEach((item) => {
          const menuIndex = updated.findIndex(m => m.menu_id === item.menu_id);
          if (menuIndex !== -1) {
            updated[menuIndex] = { ...updated[menuIndex], order_index: item.order_index };
          }
        });
        return updated;
      });

      // Prepare menu orders for bulk update (only root menus)
      const menuOrders = newOrder.map((item) => ({
        menu_id: item.menu_id,
        order_index: item.order_index || 0,
      }));

      // Call API to save order
      await bulkUpdateMenuOrder({ menu_orders: menuOrders }).unwrap();

      // Invalidate cache to refresh menus
      dispatch(permissionApi.util.invalidateTags(['Permission']));

      // Show success message
      await sweetAlert.showSuccessAuto(
        'Berhasil',
        'Urutan box menu berhasil diperbarui'
      );
    } catch (error: any) {
      // Rollback on error - refetch menus
      refetchMenus();
      await sweetAlert.showError('Gagal', error?.message || 'Gagal memperbarui urutan box menu');
    }
  };

  const handleSave = async () => {
    try {
      await updateTemplate({
        level,
        data: {
          name: `Level ${level}`,
          permissions: menus
            .filter(m => 
              m.permissions.can_read || 
              m.permissions.can_create || 
              m.permissions.can_update || 
              m.permissions.can_delete ||
              m.permissions.show_in_sidebar !== undefined
            )
            .map(m => ({ 
              menu_id: m.menu_id, 
              permissions: {
                can_read: m.permissions.can_read,
                can_create: m.permissions.can_create,
                can_update: m.permissions.can_update,
                can_delete: m.permissions.can_delete,
                show_in_sidebar: m.permissions.show_in_sidebar !== false, // Default true
              }
            }))
        },
      }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Template level berhasil disimpan');
      refetchTemplate();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal menyimpan template');
    }
  };

  if (menusLoading || templateLoading) {
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🔐 Level Role Permissions</h1>
            <p className="text-gray-600">Atur template hak akses default berdasarkan Level Role</p>
            <p className="text-sm text-amber-600 mt-1">
              ⚠️ Catatan: Checkbox "Show in Sidebar" berlaku global untuk semua role, bukan per level
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/permissions')}
          >
            ← Kembali
          </Button>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Level</label>
            <input
              type="number"
              min={1}
              value={level}
              onChange={(e) => handleChangeLevel(parseInt(e.target.value || '1'))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <Input
              type="text"
              label="Cari Menu"
              placeholder="Cari menu atau path..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex items-end gap-2">
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Menyimpan...' : '💾 Simpan'}
            </Button>
          </div>
        </div>
      </div>

      {/* Permission Matrix */}
      <PermissionMatrix
        items={filteredMenus}
        saving={saving || updatingSidebar || updatingOrder}
        onToggleAction={updatePerm}
        onToggleAll={setRowAll}
        onToggleSidebarVisibility={updateSidebarVisibility}
        onReorder={handleReorder}
        onReorderBoxes={handleReorderBoxes}
      />
    </div>
  );
};

export default LevelPermissionMatrixPage;

