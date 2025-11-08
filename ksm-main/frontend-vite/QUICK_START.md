# Quick Start Guide

## Setup Otomatis

### 1. Install Dependencies

```bash
cd frontend-vite
npm install
```

### 2. Setup Environment

```bash
# Linux/Mac
cp .env.example .env

# Windows
copy .env.example .env
```

Edit `.env` file:
```env
VITE_APP_API_URL=http://localhost:8000
VITE_APP_ENVIRONMENT=development
VITE_APP_DEBUG=false
```

### 3. Run Development Server

```bash
npm run dev
```

Aplikasi akan berjalan di **http://localhost:3004**

## Features yang Sudah Siap

✅ **Authentication** - Login page dengan JWT token management
✅ **Dashboard** - Dashboard dengan statistik sistem
✅ **Layout** - Admin layout dengan Header & Sidebar responsive
✅ **UI Components** - Table, Modal, Card, Form components, Badge, Pagination, Tabs, Dropdown
✅ **Routing** - Semua routes sudah disetup dengan placeholder

## Struktur yang Sudah Dibuat

- ✅ Core API client dengan interceptors
- ✅ Redux store dengan RTK Query
- ✅ Auth service dengan token refresh
- ✅ Shared UI components dengan Tailwind
- ✅ Migration utilities & helpers
- ✅ Feature template untuk migrasi

## Next Steps

1. **Migrasi Feature** - Gunakan template di `src/features/_template/` untuk migrasi feature
2. **Lihat Migration Guide** - Baca `MIGRATION_GUIDE.md` untuk panduan lengkap
3. **Test Features** - Test login dan dashboard yang sudah ada

## Troubleshooting

### Error: Cannot find module 'react'
- Pastikan sudah run `npm install`
- Restart TypeScript server di IDE

### Port 3004 sudah digunakan
- Ubah port di `vite.config.ts` atau hentikan aplikasi lain

### API connection error
- Pastikan backend berjalan di `http://localhost:8000`
- Check `VITE_APP_API_URL` di `.env`

