/**
 * Example Component
 * Template untuk feature-specific component dengan Tailwind
 * 
 * Prinsip:
 * - Gunakan Tailwind classes, tidak ada CSS modules
 * - Gunakan shared components dari @/shared/components/ui jika memungkinkan
 * - Mobile-first responsive design
 */

import React from 'react';
import { Card, Button } from '@/shared/components/ui';

interface ExampleComponentProps {
  title: string;
  onAction?: () => void;
}

const ExampleComponent: React.FC<ExampleComponentProps> = ({
  title,
  onAction,
}) => {
  return (
    <Card title={title} className="mb-4">
      <div className="space-y-4">
        <p className="text-text-secondary">Example component content</p>
        {onAction && (
          <Button onClick={onAction} variant="primary">
            Action
          </Button>
        )}
      </div>
    </Card>
  );
};

export default ExampleComponent;

