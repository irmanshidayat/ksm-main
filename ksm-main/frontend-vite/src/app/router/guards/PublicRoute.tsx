/**
 * Public Route Guard
 * Route guard untuk routes yang dapat diakses tanpa authentication
 * Redirect ke dashboard jika sudah authenticated
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAppSelector } from '@/app/store/hooks';
import { LoadingSpinner } from '@/shared/components/feedback';

interface PublicRouteProps {
  children: React.ReactNode;
}

const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const { isAuthenticated, loading, user } = useAppSelector((state) => state.auth);

  console.log('🌐 PublicRoute - isAuthenticated:', isAuthenticated, 'loading:', loading);

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <LoadingSpinner message="Memverifikasi akses..." />
      </div>
    );
  }

  // Redirect vendor to vendor home
  if (user && user.role === 'vendor') {
    console.log('🏪 Vendor detected, redirecting to vendor home');
    return <Navigate to="/vendor/dashboard" replace />;
  }

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    console.log('✅ User already authenticated, redirecting to dashboard');
    return <Navigate to="/dashboard" replace />;
  }

  console.log('👤 User not authenticated, showing public page');
  return <>{children}</>;
};

export default PublicRoute;

