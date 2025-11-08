/**
 * Stat Card Component
 * Component untuk menampilkan statistik di dashboard dengan Tailwind
 */

import React from 'react';
import { Card } from '@/shared/components/ui';
import { Badge } from '@/shared/components/ui';
import { StatCard as StatCardType } from '../types';

interface StatCardProps {
  stat: StatCardType;
  className?: string;
}

const StatCard: React.FC<StatCardProps> = ({ stat, className = '' }) => {
  const variantColors = {
    primary: 'bg-primary-100 text-primary-800',
    success: 'bg-success text-white',
    warning: 'bg-warning text-white',
    danger: 'bg-danger text-white',
    info: 'bg-info text-white',
  };

  return (
    <Card className={`${className}`} hoverable>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-text-secondary mb-1">{stat.title}</p>
          <p className="text-2xl font-bold text-text-primary">{stat.value}</p>
          {stat.trend && (
            <div className="mt-2">
              <Badge
                variant={stat.trend.isPositive ? 'success' : 'danger'}
                size="sm"
              >
                {stat.trend.isPositive ? '+' : ''}
                {stat.trend.value}%
              </Badge>
            </div>
          )}
        </div>
        {stat.icon && (
          <div className={`p-3 rounded-lg ${variantColors[stat.variant || 'primary']}`}>
            {stat.icon}
          </div>
        )}
      </div>
    </Card>
  );
};

export default StatCard;

