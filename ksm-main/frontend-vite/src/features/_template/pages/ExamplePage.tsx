/**
 * Example Page
 * Template untuk feature page dengan Tailwind
 * 
 * Copy dari frontend CRA:
 * - frontend/src/pages/[Feature]/[Feature].tsx
 * 
 * Migrasi:
 * 1. Hapus semua import CSS
 * 2. Convert CSS classes ke Tailwind
 * 3. Layout (Sidebar + Navbar) otomatis dari ProtectedRoute
 * 4. Gunakan shared components dari @/shared/components/ui
 * 5. Mobile-first responsive design
 */

import React from 'react';
import { Card, Button, LoadingSpinner } from '@/shared/components/ui';

const ExamplePage: React.FC = () => {
  return (
    <div className="max-w-layout mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-text-primary mb-2">Example Page</h1>
          <p className="text-text-secondary">Page description</p>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 desktop:grid-cols-2 gap-6">
          <Card title="Example Card">
            <p className="text-text-secondary">Example content</p>
          </Card>
        </div>
      </div>
  );
};

export default ExamplePage;

