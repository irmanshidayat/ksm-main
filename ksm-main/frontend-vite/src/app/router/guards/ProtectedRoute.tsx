/**
 * Protected Route Guard
 * Route guard untuk melindungi routes yang memerlukan authentication
 * Otomatis wrap dengan MainLayout (Sidebar + Navbar)
 */

import { Navigate } from 'react-router-dom';
import { useAppSelector } from '@/app/store/hooks';
import { MainLayout } from '@/shared/components/layout';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading, user } = useAppSelector((state) => state.auth);

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Memuat...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Wrap dengan MainLayout untuk otomatis menampilkan Sidebar dan Navbar
  return <MainLayout>{children}</MainLayout>;
};

export default ProtectedRoute;

