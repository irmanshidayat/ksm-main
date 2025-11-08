/**
 * Agent Status Page
 * Halaman untuk melihat status Agent AI dengan Tailwind CSS
 */

import React, { useEffect } from 'react';
import { useGetAgentStatusQuery } from '../store';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';

const AgentStatusPage: React.FC = () => {
  const { data: agentStatus, isLoading, refetch } = useGetAgentStatusQuery();

  // Auto refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!document.hidden) {
        refetch();
      }
    }, 30000);

    // Refresh when page becomes visible
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        refetch();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [refetch]);

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'online':
      case 'success':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'error':
      case 'offline':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'loading':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusText = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'online':
      case 'success':
        return 'Online';
      case 'error':
      case 'offline':
        return 'Offline';
      case 'loading':
        return 'Loading...';
      default:
        return status || 'Unknown';
    }
  };

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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🤖 Agent Status</h1>
            <p className="text-gray-600">Status Agent AI Service</p>
          </div>
          <Button
            variant="outline"
            onClick={() => refetch()}
          >
            🔄 Refresh
          </Button>
        </div>
      </div>

      {/* Status Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800">Status</h2>
          <span className={`px-4 py-2 rounded-lg border-2 font-semibold ${getStatusColor(agentStatus?.status || 'unknown')}`}>
            {getStatusText(agentStatus?.status || 'unknown')}
          </span>
        </div>

        <div className="space-y-4">
          {agentStatus?.message && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
              <p className="text-gray-800">{agentStatus.message}</p>
            </div>
          )}
          {agentStatus?.service && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Service</label>
              <p className="text-gray-800">{agentStatus.service}</p>
            </div>
          )}
          {agentStatus?.timestamp && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Last Update</label>
              <p className="text-gray-800">
                {new Date(agentStatus.timestamp).toLocaleString('id-ID')}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentStatusPage;

