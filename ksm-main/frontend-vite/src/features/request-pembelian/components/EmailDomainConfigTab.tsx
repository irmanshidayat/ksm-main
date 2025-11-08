/**
 * Email Domain Configuration Tab Component
 * Tab untuk mengkonfigurasi email domain
 */

import React, { useState, useEffect } from 'react';
import { Button, Input } from '@/shared/components/ui';
import { useSweetAlert } from '@/shared/hooks';
import {
  useGetDomainConfigsQuery,
  useCreateDomainConfigMutation,
  useUpdateDomainConfigMutation,
  useDeleteDomainConfigMutation,
  useTestDomainConnectionMutation,
  useSetDefaultDomainMutation,
  type DomainConfig,
  type DomainConfigData,
} from '../services/emailDomainApi';
import { TrashIcon, PencilIcon, CheckIcon, XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import Swal from 'sweetalert2';

interface EmailDomainConfigTabProps {
  onDomainSelect?: (domainId: number | null) => void;
  selectedDomainId?: number | null;
}

const EmailDomainConfigTab: React.FC<EmailDomainConfigTabProps> = ({
  onDomainSelect,
  selectedDomainId,
}) => {
  const sweetAlert = useSweetAlert();
  const { data: configsResponse, isLoading, refetch } = useGetDomainConfigsQuery();
  const [createConfig, { isLoading: isCreating }] = useCreateDomainConfigMutation();
  const [updateConfig, { isLoading: isUpdating }] = useUpdateDomainConfigMutation();
  const [deleteConfig, { isLoading: isDeleting }] = useDeleteDomainConfigMutation();
  const [testConnection, { isLoading: isTesting }] = useTestDomainConnectionMutation();
  const [setDefault, { isLoading: isSettingDefault }] = useSetDefaultDomainMutation();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<DomainConfig | null>(null);
  const [formData, setFormData] = useState<DomainConfigData>({
    domain_name: '',
    smtp_server: '',
    smtp_port: 587,
    username: '',
    password: '',
    from_name: '',
    is_default: false,
  });

  const configs = (configsResponse?.data as DomainConfig[]) || [];

  useEffect(() => {
    if (editingConfig) {
      setFormData({
        domain_name: editingConfig.domain_name,
        smtp_server: editingConfig.smtp_server,
        smtp_port: editingConfig.smtp_port,
        username: editingConfig.username,
        password: '', // Don't pre-fill password
        from_name: editingConfig.from_name,
        is_default: editingConfig.is_default,
      });
      setIsFormOpen(true);
    }
  }, [editingConfig]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'smtp_port' ? parseInt(value) || 587 : name === 'is_default' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const handleResetForm = () => {
    setFormData({
      domain_name: '',
      smtp_server: '',
      smtp_port: 587,
      username: '',
      password: '',
      from_name: '',
      is_default: false,
    });
    setEditingConfig(null);
    setIsFormOpen(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      Swal.fire({
        title: editingConfig ? 'Mengupdate konfigurasi...' : 'Menyimpan konfigurasi...',
        text: 'Mohon tunggu...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      let response;
      if (editingConfig) {
        response = await updateConfig({
          id: editingConfig.id,
          data: formData,
        }).unwrap();
      } else {
        response = await createConfig(formData).unwrap();
      }

      Swal.close();
      if (response.success) {
        await sweetAlert.showSuccessAuto(
          'Berhasil',
          editingConfig ? 'Konfigurasi berhasil diupdate' : 'Konfigurasi berhasil dibuat'
        );
        handleResetForm();
        refetch();
      } else {
        await sweetAlert.showError('Gagal', response.message || 'Terjadi kesalahan');
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || error?.message || 'Terjadi kesalahan');
    }
  };

  const handleDelete = async (config: DomainConfig) => {
    const result = await Swal.fire({
      title: 'Hapus Konfigurasi?',
      text: `Apakah Anda yakin ingin menghapus konfigurasi untuk domain "${config.domain_name}"?`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Ya, Hapus',
      cancelButtonText: 'Batal',
    });

    if (result.isConfirmed) {
      try {
        Swal.fire({
          title: 'Menghapus konfigurasi...',
          text: 'Mohon tunggu...',
          allowOutsideClick: false,
          allowEscapeKey: false,
          showConfirmButton: false,
          didOpen: () => {
            Swal.showLoading();
          },
        });

        const response = await deleteConfig(config.id).unwrap();
        Swal.close();

        if (response.success) {
          await sweetAlert.showSuccessAuto('Berhasil', 'Konfigurasi berhasil dihapus');
          refetch();
          if (selectedDomainId === config.id && onDomainSelect) {
            onDomainSelect(null);
          }
        } else {
          await sweetAlert.showError('Gagal', response.message || 'Gagal menghapus konfigurasi');
        }
      } catch (error: any) {
        Swal.close();
        await sweetAlert.showError('Gagal', error?.data?.message || error?.message || 'Gagal menghapus konfigurasi');
      }
    }
  };

  const handleTestConnection = async (config: DomainConfig) => {
    try {
      Swal.fire({
        title: 'Menguji koneksi...',
        text: 'Mohon tunggu...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const response = await testConnection({ id: config.id }).unwrap();
      Swal.close();

      if (response.success && response.data?.connected) {
        await sweetAlert.showSuccessAuto('Berhasil', 'Koneksi berhasil! Konfigurasi email domain valid.');
      } else {
        await sweetAlert.showError('Gagal', response.data?.error || response.message || 'Koneksi gagal');
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || error?.message || 'Gagal menguji koneksi');
    }
  };

  const handleSetDefault = async (config: DomainConfig) => {
    try {
      Swal.fire({
        title: 'Mengatur default...',
        text: 'Mohon tunggu...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const response = await setDefault(config.id).unwrap();
      Swal.close();

      if (response.success) {
        await sweetAlert.showSuccessAuto('Berhasil', 'Domain default berhasil diatur');
        refetch();
        if (onDomainSelect) {
          onDomainSelect(config.id);
        }
      } else {
        await sweetAlert.showError('Gagal', response.message || 'Gagal mengatur default');
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || error?.message || 'Gagal mengatur default');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header dengan tombol tambah */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">Konfigurasi Email Domain</h3>
          <p className="text-sm text-gray-500 mt-1">
            Kelola konfigurasi email domain untuk mengirim email ke vendor
          </p>
        </div>
        <Button
          type="button"
          variant="primary"
          onClick={() => {
            handleResetForm();
            setIsFormOpen(true);
          }}
          className="flex items-center gap-2"
        >
          <PlusIcon className="w-5 h-5" />
          Tambah Konfigurasi
        </Button>
      </div>

      {/* Form Tambah/Edit */}
      {isFormOpen && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-md font-semibold text-gray-800">
              {editingConfig ? 'Edit Konfigurasi' : 'Tambah Konfigurasi Baru'}
            </h4>
            <button
              type="button"
              onClick={handleResetForm}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nama Domain *
                </label>
                <Input
                  type="text"
                  name="domain_name"
                  value={formData.domain_name}
                  onChange={handleChange}
                  placeholder="contoh: company.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMTP Server *
                </label>
                <Input
                  type="text"
                  name="smtp_server"
                  value={formData.smtp_server}
                  onChange={handleChange}
                  placeholder="contoh: smtp.company.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SMTP Port *
                </label>
                <Input
                  type="number"
                  name="smtp_port"
                  value={formData.smtp_port}
                  onChange={handleChange}
                  placeholder="587"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Username/Email *
                </label>
                <Input
                  type="email"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="user@company.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password *
                  {editingConfig && <span className="text-xs text-gray-500 ml-1">(kosongkan jika tidak diubah)</span>}
                </label>
                <Input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Password email"
                  required={!editingConfig}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nama Pengirim *
                </label>
                <Input
                  type="text"
                  name="from_name"
                  value={formData.from_name}
                  onChange={handleChange}
                  placeholder="Nama Perusahaan"
                  required
                />
              </div>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_default"
                name="is_default"
                checked={formData.is_default}
                onChange={handleChange}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="is_default" className="ml-2 block text-sm text-gray-700">
                Set sebagai default
              </label>
            </div>

            <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
              <Button type="button" variant="outline" onClick={handleResetForm}>
                Batal
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isCreating || isUpdating}
              >
                {isCreating || isUpdating ? 'Menyimpan...' : editingConfig ? 'Update' : 'Simpan'}
            </Button>
          </div>
          </form>
        </div>
      )}

      {/* List Konfigurasi */}
      {configs.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-500">Belum ada konfigurasi email domain</p>
          <p className="text-sm text-gray-400 mt-2">Klik "Tambah Konfigurasi" untuk menambahkan</p>
        </div>
      ) : (
        <div className="space-y-4">
          {configs.map((config) => (
            <div
              key={config.id}
              className={`bg-white border rounded-lg p-4 shadow-sm ${
                config.is_default ? 'border-primary-500 border-2' : 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-semibold text-gray-800">{config.domain_name}</h4>
                    {config.is_default && (
                      <span className="px-2 py-1 text-xs font-medium bg-primary-100 text-primary-700 rounded">
                        Default
                      </span>
                    )}
                    {!config.is_active && (
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded">
                        Tidak Aktif
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-gray-600">
                    <div>
                      <span className="font-medium">SMTP:</span> {config.smtp_server}:{config.smtp_port}
                    </div>
                    <div>
                      <span className="font-medium">Email:</span> {config.username}
                    </div>
                    <div>
                      <span className="font-medium">Pengirim:</span> {config.from_name}
                    </div>
                    <div>
                      <span className="font-medium">Status:</span>{' '}
                      {config.is_active ? (
                        <span className="text-green-600">Aktif</span>
                      ) : (
                        <span className="text-red-600">Tidak Aktif</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 ml-4">
                  {onDomainSelect && (
                    <button
                      type="button"
                      onClick={() => onDomainSelect(config.id)}
                      className={`p-2 rounded-lg transition-colors ${
                        selectedDomainId === config.id
                          ? 'bg-primary-100 text-primary-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                      title="Pilih domain ini"
                    >
                      <CheckIcon className="w-5 h-5" />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => handleTestConnection(config)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Test koneksi"
                    disabled={isTesting}
                  >
                    {isTesting ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    ) : (
                      '🔌'
                    )}
                  </button>
                  {!config.is_default && (
                    <button
                      type="button"
                      onClick={() => handleSetDefault(config)}
                      className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                      title="Set sebagai default"
                      disabled={isSettingDefault}
                    >
                      ⭐
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setEditingConfig(config)}
                    className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors"
                    title="Edit"
                  >
                    <PencilIcon className="w-5 h-5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(config)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Hapus"
                    disabled={isDeleting}
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EmailDomainConfigTab;

