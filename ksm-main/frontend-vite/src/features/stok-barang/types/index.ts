/**
 * Types untuk Stok Barang Feature
 */

export interface Kategori {
  id: number;
  nama_kategori: string;
  kode_kategori: string;
  deskripsi?: string;
  parent_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface Barang {
  id: number;
  kode_barang: string;
  nama_barang: string;
  deskripsi?: string;
  kategori: Kategori;
  satuan: string;
  harga_per_unit: number;
  merk?: string;
  stok: {
    jumlah_stok: number;
    stok_minimum: number;
    stok_maksimum?: number;
  };
}

export interface Supplier {
  id: number;
  nama_supplier: string;
  alamat?: string;
  telepon?: string;
  email?: string;
}

export interface BarangMasukForm {
  barang_id: number;
  supplier_id: number | null;
  jumlah_masuk: number;
  harga_per_unit: number | null;
  tanggal_masuk: string;
  nomor_surat_jalan: string;
  keterangan: string;
}

export interface BarangMasukData extends BarangMasukForm {
  id: number;
  barang: Barang;
  supplier?: Supplier;
  created_at: string;
  total_harga?: number;
}

export interface BarangKeluarForm {
  barang_id: number;
  jumlah_keluar: number;
  tanggal_keluar: string;
  nomor_surat_jalan: string;
  keterangan: string;
  tujuan: string;
}

export interface TambahBarangForm {
  kode_barang: string;
  nama_barang: string;
  kategori_id: number;
  satuan: string;
  stok_minimal: number;
  harga_per_unit: number;
  deskripsi: string;
  merk?: string;
}

export interface TambahKategoriForm {
  kode_kategori: string;
  nama_kategori: string;
  deskripsi: string;
}

export interface DashboardData {
  total_barang: number;
  total_kategori: number;
  stok_menipis: any[];
  stok_habis: any[];
  barang_masuk_hari_ini: number;
  barang_keluar_hari_ini: number;
  total_nilai_stok: number;
}

export interface StokItem {
  barang: Barang;
  jumlah_stok: number;
}

export interface FilterParams {
  search?: string;
  kategori_id?: number;
  supplier_id?: number;
  stok_min?: number;
  stok_max?: number;
  harga_min?: number;
  harga_max?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginationParams {
  page: number;
  per_page: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface BarangListParams {
  page?: number;
  per_page?: number;
  search?: string;
  kategori_id?: number;
  supplier_id?: number;
  stok_min?: number;
  stok_max?: number;
  harga_min?: number;
  harga_max?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface BarangListResponse {
  items: Barang[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

