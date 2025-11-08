/**
 * Notifications Types
 */

export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  data?: any;
  priority: 'low' | 'normal' | 'high' | 'urgent' | 'critical';
  action_required: boolean;
  is_read: boolean;
  created_at: string;
  time_since_created?: string;
}

export interface NotificationStats {
  total: number;
  unread: number;
  read: number;
  by_priority: {
    low: number;
    normal: number;
    high: number;
    urgent: number;
    critical: number;
  };
}

