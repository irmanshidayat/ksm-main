/**
 * Dashboard Page
 * Main dashboard page dengan Tailwind CSS
 * Template untuk migrasi feature dari CRA ke Vite
 */

import React, { useState, useEffect } from 'react';
import { Card, Badge, LoadingSpinner } from '@/shared/components/ui';
import StatCard from '../components/StatCard';
import { DashboardStats } from '../types';
import apiClient from '@/core/api/client';
import { API_ENDPOINTS } from '@/core/api/endpoints';

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    telegramStatus: 'loading',
    agentStatus: 'loading',
    totalUsers: 0,
    lastUpdate: new Date().toLocaleString('id-ID'),
  });
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      setLoading(true);
      
      // Fetch Telegram and Agent status in parallel
      const [telegramResponse, agentResponse] = await Promise.allSettled([
        apiClient.get(API_ENDPOINTS.TELEGRAM.STATUS),
        apiClient.get(API_ENDPOINTS.AGENT.STATUS),
      ]);

      let telegramStatus = 'unknown';
      let agentStatus = 'unknown';
      let telegramBotInfo = undefined;

      if (telegramResponse.status === 'fulfilled' && telegramResponse.value.data?.success) {
        const telegramData = telegramResponse.value.data.data;
        telegramStatus = telegramData?.status || 'unknown';
        telegramBotInfo = telegramData?.bot_info;
      } else {
        telegramStatus = 'error';
      }

      if (agentResponse.status === 'fulfilled' && agentResponse.value.data?.success) {
        const agentData = agentResponse.value.data.data;
        agentStatus = agentData?.status || 'unknown';
      } else {
        agentStatus = 'error';
      }

      setStats({
        telegramStatus,
        agentStatus,
        totalUsers: 1,
        lastUpdate: new Date().toLocaleString('id-ID'),
        telegramBotInfo,
      });
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      setStats((prev) => ({
        ...prev,
        telegramStatus: 'error',
        agentStatus: 'error',
        lastUpdate: new Date().toLocaleString('id-ID'),
      }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    
    // Polling setiap 30 detik
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'danger'> = {
      active: 'success',
      running: 'success',
      connected: 'success',
      loading: 'warning',
      error: 'danger',
      disconnected: 'danger',
    };

    return (
      <Badge variant={variants[status] || 'warning'} size="sm">
        {status}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-layout mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-text-primary mb-2">Dashboard</h1>
          <p className="text-text-secondary">Ringkasan status sistem dan statistik</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 tablet:grid-cols-2 desktop:grid-cols-4 gap-4 mb-6">
          <StatCard
            stat={{
              title: 'Telegram Bot',
              value: stats.telegramBotInfo?.first_name || 'N/A',
              variant: stats.telegramStatus === 'active' ? 'success' : 'danger',
            }}
          />
          <StatCard
            stat={{
              title: 'Agent Status',
              value: stats.agentStatus,
              variant: stats.agentStatus === 'running' ? 'success' : 'warning',
            }}
          />
          <StatCard
            stat={{
              title: 'Total Users',
              value: stats.totalUsers,
              variant: 'primary',
            }}
          />
          <StatCard
            stat={{
              title: 'Last Update',
              value: stats.lastUpdate,
              variant: 'info',
            }}
          />
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 desktop:grid-cols-2 gap-6">
          <Card title="System Status">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-text-primary">Telegram Bot</span>
                {getStatusBadge(stats.telegramStatus)}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-primary">Agent AI</span>
                {getStatusBadge(stats.agentStatus)}
              </div>
            </div>
          </Card>

          <Card title="System Information">
            <div className="space-y-2">
              <p className="text-sm text-text-secondary">
                <span className="font-medium">Last Update:</span> {stats.lastUpdate}
              </p>
              {stats.telegramBotInfo && (
                <p className="text-sm text-text-secondary">
                  <span className="font-medium">Bot Username:</span> @{stats.telegramBotInfo.username}
                </p>
              )}
            </div>
          </Card>
        </div>
      </div>
  );
};

export default DashboardPage;

