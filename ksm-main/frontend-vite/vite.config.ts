import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables dengan fallback strategy:
  // 1. Coba load dari root ksm-main/.env (unified env)
  // 2. Fallback ke local frontend-vite/.env jika ada
  const rootEnvPath = path.resolve(__dirname, '../');
  const localEnvPath = __dirname;
  
  // Load env dari root dulu (priority)
  const rootEnv = loadEnv(mode, rootEnvPath, 'VITE_');
  // Load env dari local (akan di-override oleh root jika ada)
  const localEnv = loadEnv(mode, localEnvPath, 'VITE_');
  
  // Merge: root env takes priority
  const env = { ...localEnv, ...rootEnv };
  
  // Log untuk debugging
  if (Object.keys(rootEnv).length > 0) {
    console.log('📁 Loaded VITE_* env from root folder:', rootEnvPath);
  }
  if (Object.keys(localEnv).length > 0 && Object.keys(rootEnv).length === 0) {
    console.log('📁 Loaded VITE_* env from local folder:', localEnvPath);
  }
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3004,
      host: true,
      strictPort: false,
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'redux-vendor': ['@reduxjs/toolkit', 'react-redux'],
            'ui-vendor': ['@heroicons/react', 'lucide-react', 'sweetalert2'],
          },
        },
      },
    },
  };
});

