/**
 * Dashboard Types
 * Types untuk Dashboard feature
 */

export interface DashboardStats {
  telegramStatus: string;
  agentStatus: string;
  totalUsers: number;
  lastUpdate: string;
  telegramBotInfo?: {
    first_name: string;
    username: string;
  };
}

export interface StatCard {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

