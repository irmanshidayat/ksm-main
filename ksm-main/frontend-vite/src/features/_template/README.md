# Feature Template

Template struktur untuk membuat feature baru di frontend-vite.

## Cara Menggunakan

1. Copy folder `_template` dan rename sesuai feature name
2. Update semua file sesuai kebutuhan feature
3. Hapus contoh code dan ganti dengan implementasi actual
4. Update exports di `index.ts`

## Struktur Folder

```
feature-name/
├── components/     # Feature-specific components (dengan Tailwind)
│   ├── ExampleComponent.tsx
│   └── index.ts
├── hooks/         # Feature-specific hooks
│   ├── useExample.ts
│   └── index.ts
├── services/       # Feature business logic
│   ├── exampleService.ts
│   └── index.ts
├── store/         # Feature Redux slice/API
│   ├── exampleApi.ts
│   └── index.ts
├── types/         # Feature types
│   └── index.ts
├── pages/         # Feature pages (dengan Tailwind)
│   ├── ExamplePage.tsx
│   └── index.ts
├── index.ts       # Public exports
└── README.md      # Feature documentation
```

## Prinsip

1. **Full Tailwind** - Semua styling menggunakan Tailwind classes
2. **No CSS Modules** - Tidak ada file CSS atau CSS modules
3. **Mobile First** - Responsive dengan mobile-first approach
4. **Shared Components** - Gunakan shared components sebanyak mungkin
5. **Barrel Exports** - Export semua public API melalui index.ts

## Checklist

- [ ] Copy types dari CRA
- [ ] Copy hooks dan adapt
- [ ] Copy services dan adapt
- [ ] Copy Redux slices/APIs dan adapt
- [ ] Migrasi components (CSS → Tailwind)
- [ ] Migrasi pages (CSS → Tailwind)
- [ ] Update routes
- [ ] Test functionality
- [ ] Test responsive

