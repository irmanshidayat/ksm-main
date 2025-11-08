/**
 * Mobil Management Types
 */

export interface Mobil {
  id: number;
  nama_mobil?: string;
  nama?: string;
  plat_nomor: string;
  merk?: string;
  model?: string;
  tahun?: number;
  kapasitas?: number;
  status: string;
  is_backup?: boolean;
  priority_score?: number;
  created_at: string;
  updated_at: string;
}

export interface MobilReservation {
  id: number;
  mobil_id: number;
  user_id: number;
  start_date: string;
  end_date: string;
  tanggal_mulai?: string;
  tanggal_selesai?: string;
  jam_mulai?: string;
  jam_selesai?: string;
  purpose?: string;
  keperluan?: string;
  status: string;
  is_recurring?: boolean;
  recurring_pattern?: string;
  recurring_end_date?: string;
  created_at: string;
  updated_at: string;
  mobil?: Mobil;
  user?: {
    id: number;
    username: string;
    email?: string;
    role?: string;
    department?: string;
  };
}

export interface MobilQueryParams {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  merk?: string;
}

export interface ReservationQueryParams {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  user_id?: number;
  mobil_id?: number;
  start_date?: string;
  end_date?: string;
}

export interface PaginatedMobilResponse {
  items: Mobil[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface PaginatedReservationResponse {
  items: MobilReservation[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface MobilAvailabilityCheck {
  available: boolean;
  conflicting_reservations: MobilReservation[];
}

export interface BackupOption {
  id: number;
  nama: string;
  plat_nomor: string;
  priority: number;
  is_backup: boolean;
}

export interface RecurringPreview {
  dates: Array<{
    start: string;
    end: string;
  }>;
  total_occurrences: number;
}

