/**
 * useAuth Hook
 * Hook untuk authentication dengan Redux
 */

import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/app/store/hooks';
import { setCredentials, logout as logoutAction, setInitialAuth } from '@/app/store/slices/authSlice';
import { useGetCurrentUserQuery } from '../store/authApi';
import { authService } from '../services/authService';
import { RootState } from '@/app/store';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const { user, isAuthenticated, loading } = useAppSelector((state: RootState) => state.auth);
  const { data: currentUser, isLoading: userLoading } = useGetCurrentUserQuery(undefined, {
    skip: !isAuthenticated,
  });

  useEffect(() => {
    if (currentUser && isAuthenticated) {
      dispatch(setCredentials({
        user: currentUser,
        token: localStorage.getItem('KSM_access_token') || '',
        refreshToken: localStorage.getItem('KSM_refresh_token') || '',
      }));
    }
  }, [currentUser, isAuthenticated, dispatch]);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const success = await authService.login(username, password);
      if (success) {
        const user = authService.getUser();
        const token = await authService.getAccessToken();
        const refreshToken = localStorage.getItem('KSM_refresh_token') || '';

        if (user && token) {
          dispatch(setCredentials({
            user,
            token,
            refreshToken,
          }));
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    authService.logout();
    dispatch(logoutAction());
  };

  const getAccessToken = async (): Promise<string | null> => {
    return await authService.getAccessToken();
  };

  return {
    user,
    isAuthenticated,
    loading: loading || userLoading,
    login,
    logout,
    getAccessToken,
  };
};

