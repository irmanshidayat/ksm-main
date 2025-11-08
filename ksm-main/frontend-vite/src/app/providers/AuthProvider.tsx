/**
 * Auth Provider
 * Provider untuk initialize authentication state saat app mount
 */

import { useEffect } from 'react';
import { useAppDispatch } from '@/app/store/hooks';
import { setInitialAuth } from '@/app/store/slices/authSlice';

interface AuthProviderProps {
  children: React.ReactNode;
}

const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    // Initialize auth state from localStorage
    // Synchronous initialization untuk menghindari stuck
    try {
      // Check localStorage directly
      const token = localStorage.getItem('KSM_access_token');
      const refreshToken = localStorage.getItem('KSM_refresh_token');
      const userStr = localStorage.getItem('KSM_user');
      
      let user = null;
      if (userStr) {
        try {
          user = JSON.parse(userStr);
        } catch (e) {
          console.error('Error parsing user from localStorage:', e);
        }
      }

      const authenticated = !!(token && user);

      dispatch(setInitialAuth({
        user,
        token,
        refreshToken,
        isAuthenticated: authenticated,
      }));
    } catch (error) {
      console.error('Auth initialization error:', error);
      // Pastikan selalu set loading = false
      dispatch(setInitialAuth({
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
      }));
    }
  }, [dispatch]);

  return <>{children}</>;
};

export default AuthProvider;

