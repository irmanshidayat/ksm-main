/**
 * Environment Configuration
 * Centralized environment variables and configuration
 * Menggunakan VITE_* prefix (bukan REACT_APP_*)
 */

// Default API URL untuk development lokal (XAMPP)
// Untuk production, set VITE_APP_API_URL di .env atau saat build
const getDefaultApiUrl = () => {
  // Jika VITE_APP_API_URL sudah di-set, gunakan itu
  if (import.meta.env.VITE_APP_API_URL) {
    return import.meta.env.VITE_APP_API_URL;
  }
  
  // Jika NODE_ENV adalah production, kemungkinan di Docker, gunakan port 8001
  if (import.meta.env.PROD) {
    return 'http://localhost:8001'; // Backend Docker port
  }
  
  // Jika development dan tidak ada VITE_APP_API_URL, gunakan localhost
  if (import.meta.env.DEV && !import.meta.env.VITE_APP_API_URL) {
    return 'http://localhost:8000'; // Backend default port untuk development
  }
  
  // Fallback ke localhost:8000 jika tidak ada konfigurasi
  return 'http://localhost:8000';
};

export const ENV = {
  API_URL: getDefaultApiUrl(),
  API_KEY: import.meta.env.VITE_APP_API_KEY || 'default-key',
  DEBUG: import.meta.env.VITE_APP_DEBUG === 'true' || import.meta.env.DEV,
  ENVIRONMENT: import.meta.env.VITE_APP_ENVIRONMENT || import.meta.env.MODE || 'development',
};

// Normalisasi API_URL agar tidak berakhiran / atau /api
(() => {
  try {
    const original = ENV.API_URL;
    let normalized = (original || '').trim();
    // Hapus trailing slash berlebih
    normalized = normalized.replace(/\/+$/, '');
    // Hapus trailing /api (dengan/ tanpa slash)
    normalized = normalized.replace(/\/api\/?$/i, '');
    if (normalized !== original) {
      console.warn('⚠️ Normalizing ENV.API_URL to avoid duplication:', { original, normalized });
    }
    ENV.API_URL = normalized;
  } catch (e) {
    console.warn('⚠️ Failed to normalize ENV.API_URL:', e);
  }
})();

// Debug log untuk melihat konfigurasi
console.log('🔧 Environment Configuration (Vite - ' + new Date().toISOString() + '):', {
  API_URL: ENV.API_URL,
  DEBUG: ENV.DEBUG,
  ENVIRONMENT: ENV.ENVIRONMENT,
  VITE_APP_API_URL: import.meta.env.VITE_APP_API_URL,
  'Final ENV.API_URL': ENV.API_URL,
});

export default ENV;

