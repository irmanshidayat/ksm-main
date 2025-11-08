/**
 * Telegram Bot Management Types
 */

export interface BotStatus {
  status: string;
  message: string;
  timestamp?: string;
  bot_info?: {
    first_name: string;
    username: string;
  };
}

export interface BotSettings {
  bot_token: string;
  is_active: boolean;
  updated_at: string;
}

export interface WebhookInfo {
  url: string;
  has_custom_certificate: boolean;
  pending_update_count: number;
  last_error_date?: number;
  last_error_message?: string;
  max_connections?: number;
  allowed_updates?: string[];
}

