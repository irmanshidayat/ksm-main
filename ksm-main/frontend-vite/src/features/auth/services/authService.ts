/**
 * Auth Service
 * Service untuk authentication dengan JWT token management
 */

import apiClient from '@/core/api/client';
import { API_ENDPOINTS } from '@/core/api/endpoints';
import Swal from 'sweetalert2';

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

interface User {
  id: number;
  username: string;
  role: string;
  email?: string;
}

interface LoginResponse {
  success: boolean;
  user: User;
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

class AuthService {
  private readonly ACCESS_TOKEN_KEY = 'KSM_access_token';
  private readonly REFRESH_TOKEN_KEY = 'KSM_refresh_token';
  private readonly USER_KEY = 'KSM_user';
  private readonly LAST_ACTIVITY_KEY = 'KSM_last_activity';
  private readonly EXPIRES_AT_KEY = 'KSM_expires_at';
  
  private readonly ACCESS_TOKEN_DURATION = 15 * 60 * 1000; // 15 menit
  private readonly REFRESH_TOKEN_DURATION = 7 * 24 * 60 * 60 * 1000; // 7 hari
  private readonly IDLE_TIMEOUT = 30 * 60 * 1000; // 30 menit idle
  private readonly WARNING_TIMEOUT = 5 * 60 * 1000; // 5 menit warning
  
  private refreshPromise: Promise<boolean> | null = null;
  private idleTimer: NodeJS.Timeout | null = null;
  private warningTimer: NodeJS.Timeout | null = null;

  constructor() {
    this.setupIdleDetection();
  }

  // Login dengan JWT token
  async login(username: string, password: string): Promise<boolean> {
    try {
      const response = await apiClient.post(API_ENDPOINTS.LOGIN, {
        username,
        password,
      });

      const data = response.data;

      if (data.success && data.user && data.access_token && data.refresh_token) {
        const expiresAt = Date.now() + (data.expires_in * 1000);
        
        this.saveTokens({
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          expiresAt
        });
        
        this.saveUser(data.user);
        this.updateLastActivity();
        
        return true;
      }
      
      return false;
    } catch (error: any) {
      console.error('Login error:', error);
      return false;
    }
  }

  // Logout
  logout(): void {
    this.clearTokens();
    this.clearUser();
    this.clearTimers();
  }

  // Get access token dengan auto-refresh
  async getAccessToken(): Promise<string | null> {
    const token = localStorage.getItem(this.ACCESS_TOKEN_KEY);
    const expiresAt = localStorage.getItem(this.EXPIRES_AT_KEY);
    
    if (!token || !expiresAt) {
      return null;
    }

    const expiresAtTime = parseInt(expiresAt, 10);
    const now = Date.now();
    const timeUntilExpiry = expiresAtTime - now;

    // Refresh jika token akan expired dalam 2 menit
    if (timeUntilExpiry < 2 * 60 * 1000) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        return localStorage.getItem(this.ACCESS_TOKEN_KEY);
      }
      return null;
    }

    return token;
  }

  // Refresh access token
  async refreshAccessToken(): Promise<boolean> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      try {
        const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
        if (!refreshToken) {
          return false;
        }

        const response = await apiClient.post(API_ENDPOINTS.REFRESH, {
          refresh_token: refreshToken,
        });

        if (response.data.access_token && response.data.refresh_token) {
          const expiresAt = Date.now() + (response.data.expires_in * 1000);
          this.saveTokens({
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
            expiresAt
          });
          this.updateLastActivity();
          return true;
        }
        
        return false;
      } catch (error) {
        console.error('Refresh token error:', error);
        this.logout();
        return false;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  // Get current user
  getUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) {
      return null;
    }
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = localStorage.getItem(this.ACCESS_TOKEN_KEY);
    const user = this.getUser();
    return !!token && !!user;
  }

  // Save tokens
  private saveTokens(tokens: AuthTokens): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, tokens.accessToken);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, tokens.refreshToken);
    localStorage.setItem(this.EXPIRES_AT_KEY, tokens.expiresAt.toString());
  }

  // Clear tokens
  private clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.EXPIRES_AT_KEY);
  }

  // Save user
  private saveUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  // Clear user
  private clearUser(): void {
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.LAST_ACTIVITY_KEY);
  }

  // Update last activity
  private updateLastActivity(): void {
    localStorage.setItem(this.LAST_ACTIVITY_KEY, Date.now().toString());
    this.resetIdleTimer();
  }

  // Setup idle detection
  private setupIdleDetection(): void {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach((event) => {
      document.addEventListener(event, () => this.updateLastActivity(), true);
    });
  }

  // Reset idle timer
  private resetIdleTimer(): void {
    this.clearTimers();
    
    this.idleTimer = setTimeout(() => {
      Swal.fire({
        title: 'Session akan berakhir',
        text: 'Anda tidak aktif selama 30 menit. Session akan berakhir dalam 5 menit.',
        icon: 'warning',
        timer: 300000,
        timerProgressBar: true,
      });
      
      this.warningTimer = setTimeout(() => {
        this.logout();
        Swal.fire({
          title: 'Session berakhir',
          text: 'Anda telah logout karena tidak aktif.',
          icon: 'info',
        }).then(() => {
          window.location.href = '/login';
        });
      }, this.WARNING_TIMEOUT);
    }, this.IDLE_TIMEOUT);
  }

  // Clear timers
  private clearTimers(): void {
    if (this.idleTimer) {
      clearTimeout(this.idleTimer);
      this.idleTimer = null;
    }
    if (this.warningTimer) {
      clearTimeout(this.warningTimer);
      this.warningTimer = null;
    }
  }
}

export const authService = new AuthService();
export default authService;

