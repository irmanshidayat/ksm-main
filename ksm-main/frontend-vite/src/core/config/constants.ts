/**
 * Application Constants
 * Centralized constants used across the application
 */

export const APP_CONSTANTS = {
  APP_NAME: 'KSM Main',
  APP_VERSION: '1.0.0',
  
  // Pagination
  DEFAULT_PAGE_SIZE: 10,
  MAX_PAGE_SIZE: 100,
  
  // Timeouts
  REQUEST_TIMEOUT: 30000, // 30 seconds
  DEBOUNCE_DELAY: 300, // 300ms
  
  // File Upload
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_FILE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'],
  
  // Cache
  CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
};

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  VENDOR: '/vendor',
  REQUEST_PEMBELIAN: '/request-pembelian',
  STOK_BARANG: '/stok-barang',
  MOBIL: '/mobil',
  ATTENDANCE: '/attendance',
  NOTIFICATIONS: '/notifications',
  USER_MANAGEMENT: '/user-management',
  ROLE_MANAGEMENT: '/role-management',
  PERMISSION_MANAGEMENT: '/permission-management',
};

export default APP_CONSTANTS;

