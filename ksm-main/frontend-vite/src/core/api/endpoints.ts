/**
 * API Endpoints Configuration
 * Centralized API endpoints dengan helper function untuk create URL
 */

import { ENV } from '../config/env';

// Helper function untuk menghindari duplikasi /api dan trailing slash
export const createApiUrl = (endpoint: string) => {
  // Hapus trailing slash dan trailing "/api" (dengan/ tanpa slash)
  const baseUrl = ENV.API_URL
    .trim()
    .replace(/\/+$/, '')
    .replace(/\/api\/?$/i, '');

  // Bersihkan endpoint dari slash berlebih
  const cleanEndpoint = endpoint
    .trim()
    .replace(/^\/+/, '/') // Pastikan dimulai dengan satu slash
    .replace(/\/+$/, ''); // Hapus trailing slash
  
  // Jika endpoint kosong atau hanya slash, return base URL + /api
  if (!cleanEndpoint || cleanEndpoint === '/') {
    return `${baseUrl}/api`;
  }
  
  return `${baseUrl}/api${cleanEndpoint}`;
};

// API Endpoints
export const API_ENDPOINTS = {
  // Base URL
  API_BASE_URL: ENV.API_URL,
  
  // Auth endpoints
  LOGIN: createApiUrl('/auth/login'),
  LOGOUT: createApiUrl('/auth/logout'),
  REFRESH: createApiUrl('/refresh'),
  AUTH_ME: createApiUrl('/auth/me'),
  AUTH_VALIDATE: createApiUrl('/auth/validate'),
  
  // Knowledge Base endpoints
  KNOWLEDGE_BASE: {
    CATEGORIES: createApiUrl('/knowledge-base/categories'),
    TAGS: createApiUrl('/knowledge-base/tags'),
    FILES: createApiUrl('/knowledge-base/files'),
  },
  
  // RAG endpoints
  RAG: {
    DOCUMENTS: createApiUrl('/rag/documents'),
    LOCAL_DOCUMENTS: createApiUrl('/local-rag/documents'),
  },
  
  // Request Pembelian endpoints
  REQUEST_PEMBELIAN: {
    DASHBOARD_STATS: createApiUrl('/request-pembelian/dashboard/stats'),
    REQUESTS: createApiUrl('/request-pembelian/requests'),
  },
  
  // Email endpoints
  EMAIL: {
    SEND_VENDOR_EMAIL: createApiUrl('/email/send-vendor-email'),
    GET_VENDOR_DATA: createApiUrl('/email/get-vendor-data'),
    GET_TEMPLATES: createApiUrl('/email/get-email-templates'),
    VALIDATE_CONFIG: createApiUrl('/email/validate-email-config'),
    PREVIEW_EMAIL: createApiUrl('/email/preview-email'),
  },
  
  // Gmail API endpoints
  GMAIL: {
    AUTH: {
      STATUS: createApiUrl('/gmail/auth/status'),
      CONNECT: createApiUrl('/gmail/auth/connect'),
      CALLBACK: createApiUrl('/gmail/auth/callback'),
      DISCONNECT: createApiUrl('/gmail/auth/disconnect'),
      TEST_SEND: createApiUrl('/gmail/auth/test-send'),
    }
  },
  
  // Stok Barang endpoints
  STOK_BARANG: {
    DASHBOARD: createApiUrl('/stok-barang/dashboard'),
    BARANG: createApiUrl('/stok-barang/barang'),
    SUPPLIER: createApiUrl('/stok-barang/supplier'),
    KATEGORI: createApiUrl('/stok-barang/kategori'),
    EXPORT: createApiUrl('/stok-barang/barang/export'),
  },
  
  // Mobil endpoints
  MOBIL: {
    MOBILS: createApiUrl('/mobil/mobils'),
    REQUESTS: createApiUrl('/mobil/requests'),
    CALENDAR: createApiUrl('/mobil/calendar'),
    AVAILABILITY: createApiUrl('/mobil/availability'),
    BACKUP_OPTIONS: createApiUrl('/mobil/backup-options'),
    RECURRING_PREVIEW: createApiUrl('/mobil/recurring-preview'),
    DEBUG: {
      REQUESTS: createApiUrl('/mobil/debug/requests'),
      CALENDAR: createApiUrl('/mobil/debug/calendar'),
    }
  },
  
  // Notifications endpoints
  NOTIFICATIONS: createApiUrl('/notifications'),
  
  // Telegram endpoints
  TELEGRAM: {
    STATUS: createApiUrl('/telegram/status'),
    CONFIG: createApiUrl('/telegram/settings'),
    TEST: createApiUrl('/telegram/test'),
    SETTINGS_PUBLIC: createApiUrl('/telegram/settings/public'),
    WEBHOOK_INFO: createApiUrl('/telegram/webhook-info'),
  },
  
  // Agent endpoints
  AGENT: {
    STATUS: createApiUrl('/agent/status'),
    LIST: createApiUrl('/agent/list'),
    CREATE: createApiUrl('/agent/create'),
  },
  
  // Notion endpoints
  NOTION: {
    ENHANCED_TASKS: createApiUrl('/notion/enhanced-tasks'),
    ENHANCED_STATISTICS: createApiUrl('/notion/enhanced-statistics'),
    ENHANCED_EMPLOYEES: createApiUrl('/notion/enhanced-employees'),
    DATABASES_WITH_MAPPINGS: createApiUrl('/notion/databases/with-mappings-test'),
    MAPPING_STATISTICS: createApiUrl('/notion/mapping/statistics-test'),
    DISCOVER_AND_ANALYZE: createApiUrl('/notion/discover-and-analyze'),
  },
  
  // Qdrant endpoints
  QDRANT: {
    STATS: createApiUrl('/qdrant-knowledge-base/stats'),
    DOCUMENTS: createApiUrl('/qdrant-knowledge-base/documents'),
    COLLECTIONS: createApiUrl('/qdrant-knowledge-base/collections'),
    SEARCH: createApiUrl('/qdrant-knowledge-base/search'),
    QUERY: createApiUrl('/qdrant-knowledge-base/query'),
    CONFIG: createApiUrl('/qdrant-knowledge-base/config'),
    HEALTH: createApiUrl('/qdrant-knowledge-base/health'),
  },
  
  // Knowledge AI endpoints
  KNOWLEDGE_AI: {
    STATS: createApiUrl('/knowledge-ai/stats'),
    CHAT: createApiUrl('/knowledge-ai/chat'),
    SEARCH: createApiUrl('/knowledge-ai/search'),
  },
  
  // User Management endpoints
  USERS: createApiUrl('/auth/users'),
  USERS_DELETE: createApiUrl('/users'),
  
  // Vendor endpoints
  VENDOR: {
    LOGIN: createApiUrl('/login'),
    VALIDATE: createApiUrl('/vendor/validate'),
    DASHBOARD: createApiUrl('/vendor/dashboard'),
    PROFILE: createApiUrl('/vendor/profile'),
    HISTORY: createApiUrl('/vendor/history'),
    REQUESTS: createApiUrl('/vendor/requests'),
    TEMPLATES: createApiUrl('/vendor/templates'),
    NOTIFICATIONS: createApiUrl('/vendor/notifications'),
    UPLOAD_LIMITS: createApiUrl('/vendor/upload/limits'),
    ORDERS: {
      MY_ORDERS: createApiUrl('/vendor-orders/my-orders'),
      DETAIL: createApiUrl('/vendor-orders/:orderId'),
      CONFIRM: createApiUrl('/vendor-orders/:orderId/confirm'),
      UPDATE_STATUS: createApiUrl('/vendor-orders/:orderId/status'),
      STATISTICS: createApiUrl('/vendor-orders/statistics'),
      STATUS_OPTIONS: createApiUrl('/vendor-orders/status-options'),
      STREAM: createApiUrl('/vendor-orders/stream'),
      EXPORT: createApiUrl('/vendor-orders/export'),
      ADMIN_ALL_ORDERS: createApiUrl('/vendor-orders/admin/all-orders'),
      ADMIN_UPDATE_STATUS: createApiUrl('/vendor-orders/admin/order/:orderId'),
    }
  }
};

// API Configuration for backward compatibility
export const API_CONFIG = {
  BASE_URL: ENV.API_URL,
  API_KEY: ENV.API_KEY,
};

export default API_ENDPOINTS;

