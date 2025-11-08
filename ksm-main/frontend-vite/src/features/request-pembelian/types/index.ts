/**
 * Request Pembelian Types
 * Types untuk Request Pembelian dan Vendor Catalog
 */

export interface RequestPembelian {
  id: number;
  reference_id: string;
  request_number?: string;
  user_id: number;
  department_id: number;
  status: string;
  priority: string;
  total_budget?: number;
  request_date: string;
  required_date?: string;
  vendor_upload_deadline?: string;
  analysis_deadline?: string;
  approval_deadline?: string;
  title: string;
  description?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  items?: RequestPembelianItem[];
  items_count: number;
  vendor_penawarans_count: number;
  is_overdue: boolean;
  days_remaining?: number;
  user?: {
    id: number;
    username: string;
  };
}

export interface RequestPembelianItem {
  id: number;
  request_id: number;
  barang_id?: number;
  nama_barang?: string;
  quantity: number;
  satuan?: string;
  specifications?: string;
  spesifikasi?: string;
  unit_price?: number;
  total_price?: number;
  estimated_price?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface VendorPenawaran {
  id: number;
  request_id: number;
  vendor_id: number;
  reference_id: string;
  status: string;
  submission_date: string;
  total_quoted_price?: number;
  files_count: number;
  items_count: number;
  vendor?: {
    id: number;
    company_name: string;
    contact_person: string;
    email: string;
  };
}

export interface VendorPenawaranItem {
  id: number;
  vendor_penawaran_id: number;
  nama_barang: string;
  quantity: number;
  harga_satuan: number;
  harga_total: number;
  spesifikasi?: string;
  kategori?: string;
  satuan?: string;
  merek?: string;
  garansi?: string;
  created_at: string;
  updated_at: string;
}

export interface RequestPembelianListParams {
  page?: number;
  per_page?: number;
  status?: string;
  priority?: string;
  search?: string;
  dateFrom?: string;
  dateTo?: string;
}

export interface RequestPembelianListResponse {
  success: boolean;
  items: RequestPembelian[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  message?: string;
}

export interface DashboardStats {
  total_requests: number;
  pending_requests: number;
  approved_requests: number;
  rejected_requests: number;
  total_budget: number;
  vendors_count: number;
}

export interface VendorAnalysisResult {
  request_id: number;
  analysis_date: string;
  total_vendors: number;
  total_penawarans: number;
  best_vendor?: {
    id: number;
    company_name: string;
    total_price: number;
    email: string;
    vendor_category: string;
  };
}

// Status options
export const REQUEST_STATUS_OPTIONS = [
  { value: '', label: 'Semua Status' },
  { value: 'draft', label: 'Draft' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'vendor_uploading', label: 'Vendor Uploading' },
  { value: 'under_analysis', label: 'Under Analysis' },
  { value: 'vendor_selected', label: 'Vendor Selected' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'cancelled', label: 'Cancelled' },
];

export const PRIORITY_OPTIONS = [
  { value: '', label: 'Semua Prioritas' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
];

// Vendor Catalog Item Types
export interface VendorCatalogItem {
  id: number;
  vendor_penawaran_id: number;
  request_item_id?: number;
  vendor_unit_price?: number;
  vendor_total_price?: number;
  vendor_quantity?: number;
  vendor_specifications?: string;
  vendor_notes?: string;
  vendor_merk?: string;
  kategori?: string;
  nama_barang?: string;
  satuan?: string;
  vendor?: {
    id: number;
    company_name: string;
    email: string;
    vendor_category?: string;
  };
  penawaran?: {
    id: number;
    request_id: number;
    status: string;
    submission_date: string;
  };
  request?: {
    id: number;
    reference_id: string;
    title: string;
  };
  request_item?: {
    id: number;
    nama_barang: string;
    quantity: number;
    satuan: string;
  };
  created_at: string;
  updated_at: string;
}

export interface VendorCatalogListParams {
  page?: number;
  per_page?: number;
  vendor_id?: number;
  reference_id?: string;
  status?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  kategori?: string;
  merek?: string;
  vendor_type?: string;
  business_model?: string;
  min_harga?: number;
  max_harga?: number;
  request_id?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface VendorCatalogListResponse {
  success: boolean;
  data: VendorCatalogItem[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  message?: string;
}

// Email Attachment Types
export interface EmailAttachment {
  id: number;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  file_extension?: string;
  request_pembelian_id?: number;
  uploaded_by_user_id: number;
  email_subject?: string;
  email_recipient?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

