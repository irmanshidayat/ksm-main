/**
 * Telegram Bot Management Page
 * Halaman untuk mengelola Telegram Bot dengan Tailwind CSS
 */

import React, { useState } from 'react';
import {
  useGetBotStatusQuery,
  useGetBotSettingsQuery,
  useUpdateBotSettingsMutation,
  useTestBotMutation,
  useGetWebhookInfoQuery,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { BotSettings } from '../types';

const TelegramBotManagementPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [showTokenInput, setShowTokenInput] = useState(false);
  const [botToken, setBotToken] = useState('');

  const { data: botStatus, isLoading: loadingStatus, refetch: refetchStatus } = useGetBotStatusQuery();
  const { data: botSettings, isLoading: loadingSettings, refetch: refetchSettings } = useGetBotSettingsQuery();
  const { data: webhookInfo, isLoading: loadingWebhook } = useGetWebhookInfoQuery();
  const [updateSettings] = useUpdateBotSettingsMutation();
  const [testBot, { isLoading: testing }] = useTestBotMutation();

  const handleUpdateSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!botToken) {
      await sweetAlert.showError('Error', 'Bot token wajib diisi');
      return;
    }

    try {
      await updateSettings({
        bot_token: botToken,
        is_active: true,
      }).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Settings berhasil diupdate');
      setShowTokenInput(false);
      setBotToken('');
      refetchSettings();
      refetchStatus();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal update settings');
    }
  };

  const handleTestBot = async () => {
    try {
      const result = await testBot().unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', result.message || 'Test bot berhasil');
      refetchStatus();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal test bot');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'online':
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'inactive':
      case 'offline':
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'loading':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loadingStatus || loadingSettings) {
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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🤖 Telegram Bot Management</h1>
            <p className="text-gray-600">Kelola konfigurasi Telegram Bot</p>
          </div>
          <Button
            variant="primary"
            onClick={handleTestBot}
            isLoading={testing}
          >
            🧪 Test Bot
          </Button>
        </div>
      </div>

      {/* Bot Status */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Bot Status</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Status</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(botStatus?.status || 'unknown')}`}>
              {botStatus?.status || 'Unknown'}
            </span>
          </div>
          {botStatus?.message && (
            <div>
              <span className="text-sm text-gray-600">Message: </span>
              <span className="text-sm text-gray-800">{botStatus.message}</span>
            </div>
          )}
          {botStatus?.bot_info && (
            <div>
              <span className="text-sm text-gray-600">Bot Info: </span>
              <span className="text-sm text-gray-800">
                {botStatus.bot_info.first_name} (@{botStatus.bot_info.username})
              </span>
            </div>
          )}
          {botStatus?.timestamp && (
            <div>
              <span className="text-sm text-gray-600">Last Update: </span>
              <span className="text-sm text-gray-800">
                {new Date(botStatus.timestamp).toLocaleString('id-ID')}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Bot Settings */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800">Bot Settings</h2>
          <Button
            variant="outline"
            onClick={() => {
              setShowTokenInput(!showTokenInput);
              setBotToken(botSettings?.bot_token || '');
            }}
          >
            {showTokenInput ? '✕ Batal' : '✏️ Edit Settings'}
          </Button>
        </div>

        {showTokenInput ? (
          <form onSubmit={handleUpdateSettings} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Bot Token</label>
              <Input
                type="password"
                value={botToken}
                onChange={(e) => setBotToken(e.target.value)}
                placeholder="Masukkan bot token"
                required
              />
            </div>
            <div className="flex gap-4">
              <Button type="submit" variant="primary">
                💾 Simpan
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowTokenInput(false);
                  setBotToken('');
                }}
              >
                Batal
              </Button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Bot Token</span>
              <span className="text-sm text-gray-800">
                {botSettings?.bot_token ? '••••••••' : 'Belum diatur'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Is Active</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                botSettings?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {botSettings?.is_active ? 'Aktif' : 'Tidak Aktif'}
              </span>
            </div>
            {botSettings?.updated_at && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Last Updated</span>
                <span className="text-sm text-gray-800">
                  {new Date(botSettings.updated_at).toLocaleString('id-ID')}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Webhook Info */}
      {webhookInfo && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Webhook Info</h2>
          {loadingWebhook ? (
            <LoadingSpinner />
          ) : (
            <div className="space-y-4">
              <div>
                <span className="text-sm text-gray-600">URL: </span>
                <span className="text-sm text-gray-800">{webhookInfo.url || 'N/A'}</span>
              </div>
              <div>
                <span className="text-sm text-gray-600">Pending Updates: </span>
                <span className="text-sm text-gray-800">{webhookInfo.pending_update_count || 0}</span>
              </div>
              {webhookInfo.last_error_message && (
                <div>
                  <span className="text-sm text-red-600">Last Error: </span>
                  <span className="text-sm text-red-800">{webhookInfo.last_error_message}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TelegramBotManagementPage;

