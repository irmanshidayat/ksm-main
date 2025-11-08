/**
 * Admin Route Guard
 * Route guard untuk melindungi routes yang hanya dapat diakses oleh Admin
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAppSelector } from '@/app/store/hooks';
import { LoadingSpinner } from '@/shared/components/feedback';

interface AdminRouteGuardProps {
  children: React.ReactNode;
}

const AdminRouteGuard: React.FC<AdminRouteGuardProps> = ({ children }) => {
  const { user, loading } = useAppSelector((state) => state.auth);

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <LoadingSpinner />
      </div>
    );
  }

  // Check if user is admin
  if (!user || user.role !== 'admin') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
        <div className="text-center max-w-md">
          <h1 className="text-3xl font-bold text-red-600 mb-4">🚫 Akses Ditolak</h1>
          <p className="text-gray-600 mb-6">
            Halaman ini hanya dapat diakses oleh Admin.
          </p>
          <p className="text-gray-500 text-sm mb-6">
            Role Anda saat ini: <strong className="text-gray-700">{user?.role || 'Tidak diketahui'}</strong>
          </p>
          <button
            onClick={() => window.history.back()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            ← Kembali
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default AdminRouteGuard;

