# Migration Guide: CRA ke Vite dengan Full Tailwind

## Overview

Guide ini menjelaskan cara migrasi feature dari frontend CRA ke frontend-vite dengan menggunakan full Tailwind CSS.

## Prinsip Migrasi

1. **Full Tailwind** - Semua styling menggunakan Tailwind classes, tidak ada CSS modules
2. **No Redundancy** - Tidak duplikasi kode antara CRA dan Vite
3. **Feature by Feature** - Migrasi satu feature lengkap sebelum lanjut
4. **Maintain Functionality** - Pastikan fungsionalitas sama persis
5. **Mobile First** - Gunakan Tailwind responsive classes (mobile:, tablet:, desktop:, wide:)

## Checklist Migrasi Per Feature

### 1. Copy Types
- [ ] Copy types dari `frontend/src/pages/[feature]/types.ts` ke `frontend-vite/src/features/[feature]/types/index.ts`
- [ ] Pastikan semua types ter-export dengan benar

### 2. Copy Hooks (jika ada)
- [ ] Copy hooks dari `frontend/src/hooks/` ke `frontend-vite/src/features/[feature]/hooks/`
- [ ] Adapt import paths (gunakan `@/` alias)
- [ ] Pastikan menggunakan API client dari `@/core/api/client`

### 3. Copy Services
- [ ] Copy services dari `frontend/src/services/` ke `frontend-vite/src/features/[feature]/services/`
- [ ] Adapt untuk menggunakan `apiClient` dari `@/core/api/client`
- [ ] Gunakan `API_ENDPOINTS` dari `@/core/api/endpoints`

### 4. Copy Redux Slices/APIs
- [ ] Copy Redux slices dari `frontend/src/store/slices/` ke `frontend-vite/src/features/[feature]/store/`
- [ ] Copy RTK Query APIs dari `frontend/src/store/services/` ke `frontend-vite/src/features/[feature]/store/`
- [ ] Pastikan menggunakan `baseApi` dari `@/app/store/services/baseApi`

### 5. Migrasi Components
- [ ] Copy components dari `frontend/src/components/[feature]/` ke `frontend-vite/src/features/[feature]/components/`
- [ ] **Hapus semua import CSS modules** (`import styles from '...module.css'`)
- [ ] **Convert semua CSS classes ke Tailwind classes**
- [ ] Gunakan shared UI components dari `@/shared/components/ui` jika memungkinkan
- [ ] Pastikan responsive dengan mobile-first approach

### 6. Migrasi Pages
- [ ] Copy pages dari `frontend/src/pages/[feature]/` ke `frontend-vite/src/features/[feature]/pages/`
- [ ] **Hapus semua import CSS** (`import '...css'`)
- [ ] **Convert semua CSS classes ke Tailwind classes**
- [ ] Gunakan `AdminLayout` dari `@/shared/components/layout` untuk layout
- [ ] Pastikan menggunakan shared components

### 7. Update Routes
- [ ] Update `src/app/router/index.tsx` untuk menambahkan route feature baru
- [ ] Pastikan menggunakan `ProtectedRoute` untuk routes yang memerlukan auth

### 8. Testing
- [ ] Test semua fungsionalitas
- [ ] Test responsive (mobile, tablet, desktop)
- [ ] Test error handling
- [ ] Test loading states

## Contoh Konversi CSS ke Tailwind

### CSS Module → Tailwind

**Sebelum (CSS Module):**
```tsx
import styles from './Component.module.css';

<div className={styles.container}>
  <h1 className={styles.title}>Title</h1>
</div>
```

**Sesudah (Tailwind):**
```tsx
<div className="bg-white rounded-lg shadow-md p-6">
  <h1 className="text-2xl font-bold text-text-primary mb-4">Title</h1>
</div>
```

### CSS Classes Mapping

| CSS Variable/Class | Tailwind Class |
|-------------------|----------------|
| `--color-primary` | `text-primary` atau `bg-primary` |
| `--color-bg-secondary` | `bg-bg-secondary` |
| `--color-text-primary` | `text-text-primary` |
| `--spacing-md` | `p-md` atau `m-md` |
| `--shadow-md` | `shadow-md` |
| `--radius-lg` | `rounded-lg` |
| `.container` | `max-w-layout mx-auto` |
| `.flex-center` | `flex items-center justify-center` |

## Shared Components yang Tersedia

Gunakan shared components dari `@/shared/components/ui`:

- `Button` - Button component dengan variants
- `Input` - Input component
- `Table` - Table component dengan sorting, pagination
- `Modal` - Modal component
- `Card` - Card component
- `Badge` - Badge component
- `Pagination` - Pagination component
- `Tabs` - Tabs component
- `Dropdown` - Dropdown component
- `Select`, `Textarea`, `Checkbox`, `Radio` - Form components

## Helper Utilities

Gunakan helper dari `@/shared/utils/tailwind-helpers`:

```tsx
import { cn, responsive, colors, shadows } from '@/shared/utils';

// Combine classes
<div className={cn('base-class', condition && 'conditional-class')} />

// Responsive
<div className={responsive.desktop('grid-cols-3')} />
```

## Contoh Migrasi: Dashboard Feature

Lihat `src/features/dashboard/` sebagai contoh migrasi lengkap:

1. Types: `types/index.ts`
2. Components: `components/StatCard.tsx`
3. Pages: `pages/DashboardPage.tsx`

## Tips & Best Practices

1. **Mobile First**: Mulai dengan mobile styles, lalu tambah `tablet:`, `desktop:`, `wide:` untuk breakpoints lebih besar
2. **Reuse Components**: Gunakan shared components sebanyak mungkin
3. **Consistent Spacing**: Gunakan spacing scale dari Tailwind config (xs, sm, md, lg, xl, 2xl, 3xl)
4. **Semantic Colors**: Gunakan semantic colors (primary, success, warning, danger, info)
5. **No Inline Styles**: Hindari inline styles, gunakan Tailwind classes
6. **Group Related Classes**: Group classes yang related untuk readability

## Troubleshooting

### Tailwind classes tidak ter-apply
- Pastikan class ada di `tailwind.config.js` content paths
- Restart dev server setelah mengubah config

### Custom colors tidak tersedia
- Pastikan sudah ditambahkan di `tailwind.config.js` theme.extend.colors
- Gunakan format: `bg-primary`, `text-primary`, dll

### Responsive tidak bekerja
- Pastikan menggunakan breakpoint prefix: `tablet:`, `desktop:`, `wide:`
- Check di browser dev tools apakah classes ter-apply

## Next Steps

Setelah migrasi feature:
1. Test di development
2. Test di production build
3. Update documentation
4. Lanjut ke feature berikutnya

