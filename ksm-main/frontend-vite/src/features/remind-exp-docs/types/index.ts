/**
 * Remind Exp Docs Types
 */

export interface RemindExpDoc {
  id: number;
  document_name: string;
  document_number?: string;
  document_type?: string;
  issuer?: string;
  expiry_date: string;
  reminder_days_before: number;
  status: 'active' | 'expired' | 'inactive';
  description?: string;
  file_path?: string;
  created_at: string;
  updated_at: string;
}

export interface RemindExpDocsStatistics {
  total_documents: number;
  active_documents: number;
  expired_documents: number;
  inactive_documents: number;
  expiring_30_days: number;
  expiring_7_days: number;
  already_expired: number;
}

export interface RemindExpDocsQueryParams {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  document_type?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedRemindExpDocsResponse {
  items: RemindExpDoc[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
  has_next?: boolean;
  has_prev?: boolean;
}

export interface CreateRemindExpDocRequest {
  document_name: string;
  document_number?: string;
  document_type?: string;
  issuer?: string;
  expiry_date: string;
  reminder_days_before: number;
  description?: string;
  file_path?: string;
}

