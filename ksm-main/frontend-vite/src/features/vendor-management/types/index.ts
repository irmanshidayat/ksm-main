/**
 * Vendor Management Types
 * Types untuk fitur Vendor Management
 */

export interface Vendor {
  id: number;
  company_name: string;
  contact_person: string;
  email: string;
  phone?: string;
  address?: string;
  vendor_category: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface VendorListParams {
  page?: number;
  per_page?: number;
  search?: string;
  category?: string;
  status?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface VendorListResponse {
  items: Vendor[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface BulkImportRequest {
  file: File;
}

export interface BulkImportResponse {
  success: boolean;
  imported_count: number;
  errors: string[];
}

// Vendor Dashboard Types
export interface VendorInfo {
  id: number;
  company_name: string;
  contact_person: string;
  email: string;
  phone?: string;
  address?: string;
  business_license?: string;
  tax_id?: string;
  bank_account?: string;
  ktp_director_name?: string;
  ktp_director_number?: string;
  vendor_category: string;
  custom_category?: string;
  vendor_type: 'internal' | 'partner';
  business_model: 'supplier' | 'reseller' | 'both';
  status: 'pending' | 'approved' | 'rejected' | 'suspended';
  user_id?: number;
  registration_date?: string;
  approved_date?: string;
  created_at?: string;
  updated_at?: string;
  penawarans_count?: number;
}

export interface DashboardStats {
  total_penawaran: number;
  pending_penawaran: number;
  under_review_penawaran: number;
  approved_penawaran: number;
  rejected_penawaran: number;
  active_requests: number;
  success_rate: number;
}

export interface RecentPenawaran {
  id: number;
  request_id: number;
  reference_id: string;
  status: string;
  submission_date: string;
  total_quoted_price?: number;
  files_count: number;
}

export interface VendorDashboardData {
  vendor: VendorInfo;
  statistics: DashboardStats;
  recent_requests?: any[];
  recent_penawaran?: RecentPenawaran[];
  dashboard_summary?: {
    total_active_requests: number;
    pending_penawaran: number;
    success_rate: number;
    vendor_status: string;
  };
}

// Vendor Self Registration Types
export interface VendorSelfRegistrationRequest {
  company_name: string;
  contact_person: string;
  email: string;
  phone: string;
  address?: string;
  business_license?: string;
  tax_id?: string;
  bank_account?: string;
  vendor_category: string;
  vendor_type: string;
  business_model: string;
  custom_category?: string;
  ktp_director_name?: string;
  ktp_director_number?: string;
  password: string;
}

export interface VendorSelfRegistrationResponse {
  success: boolean;
  data?: Vendor;
  message?: string;
}

