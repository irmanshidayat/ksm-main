/**
 * Vendor Route Guard
 * Route guard untuk melindungi routes yang hanya dapat diakses oleh Vendor
 */

import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAppSelector } from '@/app/store/hooks';
import { LoadingSpinner } from '@/shared/components/feedback';

interface VendorRouteGuardProps {
  children: React.ReactNode;
}

const VendorRouteGuard: React.FC<VendorRouteGuardProps> = ({ children }) => {
  const { isAuthenticated, loading, user } = useAppSelector((state) => state.auth);
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    if (!loading) {
      const timer = setTimeout(() => {
        setShowContent(true);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [loading]);

  // Show loading spinner while checking auth
  if (loading || !showContent) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <LoadingSpinner message="Memverifikasi akses..." />
      </div>
    );
  }

  // Check if user is authenticated and is vendor
  if (!isAuthenticated || !user || user.role !== 'vendor') {
    console.log('❌ User not authenticated or not vendor, redirecting to access denied');
    return <Navigate to="/vendor/access-denied" replace />;
  }

  console.log('✅ Vendor authenticated, allowing access');
  return <>{children}</>;
};

export default VendorRouteGuard;

