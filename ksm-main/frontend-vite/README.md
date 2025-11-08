# KSM Main Frontend - Vite

Frontend aplikasi KSM Main menggunakan React + Vite + TypeScript dengan full Tailwind CSS.

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

Atau gunakan setup script:
- **Linux/Mac**: `bash setup.sh`
- **Windows**: `setup.bat`

### 2. Setup Environment

Copy `.env.example` ke `.env` dan edit sesuai konfigurasi:

```bash
cp .env.example .env
```

Edit `.env`:
```env
VITE_APP_API_URL=http://localhost:8000
VITE_APP_ENVIRONMENT=development
```

### 3. Run Development Server

```bash
npm run dev
```

Aplikasi akan berjalan di `http://localhost:3004`

### 4. Build untuk Production

```bash
npm run build
```

Output akan ada di folder `dist/`

## Struktur Project

```
frontend-vite/
├── src/
│   ├── app/              # App configuration (store, router, providers)
│   ├── core/             # Core abstractions (api, config, types, utils)
│   ├── features/         # Feature-based modules
│   │   ├── auth/        # Authentication feature
│   │   ├── dashboard/   # Dashboard feature
│   │   └── _template/   # Template untuk feature baru
│   ├── shared/          # Shared components & utilities
│   │   ├── components/  # Reusable components
│   │   ├── hooks/       # Shared hooks
│   │   └── utils/       # Shared utilities
│   └── styles/          # Global styles
├── public/              # Static assets
└── package.json
```

## Features

### ✅ Sudah Diimplementasikan

- **Authentication** - Login dengan JWT token
- **Dashboard** - Dashboard dengan statistik sistem
- **Layout** - Admin layout dengan Header & Sidebar
- **UI Components** - Table, Modal, Card, Form components, dll
- **Routing** - React Router dengan protected routes

### 🚧 Akan Dimigrasi

- Vendor Management
- Request Pembelian
- Stok Barang
- Mobil Management
- Attendance
- Notifications
- User Management
- Role Management
- Permission Management

## Migration Guide

Lihat `MIGRATION_GUIDE.md` untuk panduan lengkap migrasi feature dari CRA ke Vite.

## Tech Stack

- **React 18** - UI Library
- **Vite** - Build tool
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling (full Tailwind, no CSS modules)
- **Redux Toolkit** - State management
- **React Router v6** - Routing
- **Axios** - HTTP client
- **SweetAlert2** - Notifications

## Development

### Port Configuration

- **Development**: `http://localhost:3004`
- **Docker Production**: `3005:3000`

### Environment Variables

Semua environment variables menggunakan prefix `VITE_*` (bukan `REACT_APP_*`):

- `VITE_APP_API_URL` - API base URL
- `VITE_APP_API_KEY` - API key
- `VITE_APP_ENVIRONMENT` - Environment (development/production)
- `VITE_APP_DEBUG` - Debug mode

## Docker

### Build & Run

```bash
docker-compose up ksm-frontend-vite-prod
```

Aplikasi akan tersedia di `http://localhost:3005`

## Best Practices

1. **Full Tailwind** - Semua styling menggunakan Tailwind classes
2. **No CSS Modules** - Tidak ada file CSS atau CSS modules
3. **Mobile First** - Responsive dengan mobile-first approach
4. **Feature-Based** - Setiap feature terisolasi di folder sendiri
5. **Shared Components** - Gunakan shared components sebanyak mungkin
6. **Type Safety** - Gunakan TypeScript untuk semua file

## Troubleshooting

### Tailwind classes tidak ter-apply
- Pastikan class ada di `tailwind.config.js` content paths
- Restart dev server setelah mengubah config

### Port sudah digunakan
- Ubah port di `vite.config.ts` atau hentikan aplikasi yang menggunakan port 3004

### API connection error
- Pastikan backend berjalan di `http://localhost:8000`
- Check `VITE_APP_API_URL` di `.env`

## Support

Untuk pertanyaan atau issue, silakan buat issue di repository.

