/**
 * Admin Layout Component
 * Main layout wrapper untuk admin pages - Responsif
 */

import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/app/store/hooks';
import { setSidebarOpen } from '@/app/store/slices/uiSlice';
import Header from './Header';
import Sidebar from './Sidebar';

interface AdminLayoutProps {
  children: React.ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const dispatch = useAppDispatch();
  const { sidebarOpen } = useAppSelector((state) => state.ui);

  // Set initial sidebar state berdasarkan screen size
  useEffect(() => {
    const checkScreenSize = () => {
      if (window.innerWidth >= 1024) {
        // Desktop: sidebar selalu visible
        dispatch(setSidebarOpen(true));
      } else {
        // Mobile/Tablet: sidebar default hidden
        dispatch(setSidebarOpen(false));
      }
    };

    // Check saat mount
    checkScreenSize();

    // Listen untuk resize
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, [dispatch]);

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden lg:ml-0">
        <Header />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;

