/**
 * Main Layout Component
 * Layout wrapper yang dinamis berdasarkan role user
 * Otomatis memilih layout yang sesuai (AdminLayout, VendorLayout, dll)
 */

import React from 'react';
import AdminLayout from './AdminLayout';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  // Untuk sekarang semua role menggunakan AdminLayout
  // Nanti bisa dikembangkan dengan layout berbeda per role
  // Contoh:
  // const { user } = useAppSelector((state) => state.auth);
  // if (user?.role === 'vendor') {
  //   return <VendorLayout>{children}</VendorLayout>;
  // }
  // if (user?.role === 'user') {
  //   return <UserLayout>{children}</UserLayout>;
  // }

  // Default: AdminLayout untuk semua role
  return <AdminLayout>{children}</AdminLayout>;
};

export default MainLayout;

