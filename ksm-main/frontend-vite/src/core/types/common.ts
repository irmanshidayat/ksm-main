/**
 * Common Types
 * Types yang digunakan di seluruh aplikasi
 */

export interface User {
  id: number;
  username: string;
  role: string;
  email?: string;
  name?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in?: number;
}

export interface SelectOption {
  label: string;
  value: string | number;
  disabled?: boolean;
}

export interface TableColumn<T = any> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: any, record: T) => React.ReactNode;
}

export interface FilterOption {
  key: string;
  label: string;
  value: any;
}

