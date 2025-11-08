/**
 * Auth Slice
 * Redux slice untuk authentication state
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { User } from '@/core/types';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
}

const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  loading: true,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action: PayloadAction<{
      user: User;
      token: string;
      refreshToken: string;
    }>) => {
      const { user, token, refreshToken } = action.payload;
      state.user = user;
      state.token = token;
      state.refreshToken = refreshToken;
      state.isAuthenticated = true;
      state.loading = false;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.loading = false;
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setInitialAuth: (state, action: PayloadAction<{
      user: User | null;
      token: string | null;
      refreshToken: string | null;
      isAuthenticated: boolean;
    }>) => {
      const { user, token, refreshToken, isAuthenticated } = action.payload;
      state.user = user;
      state.token = token;
      state.refreshToken = refreshToken;
      state.isAuthenticated = isAuthenticated;
      state.loading = false;
    },
  },
});

export const { 
  setCredentials, 
  logout, 
  updateUser, 
  setLoading, 
  setInitialAuth 
} = authSlice.actions;

export default authSlice.reducer;

