-- Migration: Add vendor attachment fields
-- Date: 2024-01-XX
-- Description: Menambahkan field untuk upload dokumen perusahaan vendor

-- Add attachment columns to vendors table
ALTER TABLE vendors 
ADD COLUMN akta_perusahaan_file_path VARCHAR(500) NULL COMMENT 'Path file akta perusahaan',
ADD COLUMN akta_perusahaan_file_name VARCHAR(255) NULL COMMENT 'Nama file akta perusahaan',
ADD COLUMN akta_perusahaan_file_size BIGINT NULL COMMENT 'Ukuran file akta perusahaan',
ADD COLUMN akta_perusahaan_upload_date DATETIME NULL COMMENT 'Tanggal upload akta perusahaan',

ADD COLUMN nib_file_path VARCHAR(500) NULL COMMENT 'Path file NIB',
ADD COLUMN nib_file_name VARCHAR(255) NULL COMMENT 'Nama file NIB',
ADD COLUMN nib_file_size BIGINT NULL COMMENT 'Ukuran file NIB',
ADD COLUMN nib_upload_date DATETIME NULL COMMENT 'Tanggal upload NIB',

ADD COLUMN npwp_file_path VARCHAR(500) NULL COMMENT 'Path file NPWP',
ADD COLUMN npwp_file_name VARCHAR(255) NULL COMMENT 'Nama file NPWP',
ADD COLUMN npwp_file_size BIGINT NULL COMMENT 'Ukuran file NPWP',
ADD COLUMN npwp_upload_date DATETIME NULL COMMENT 'Tanggal upload NPWP',

ADD COLUMN company_profile_file_path VARCHAR(500) NULL COMMENT 'Path file company profile',
ADD COLUMN company_profile_file_name VARCHAR(255) NULL COMMENT 'Nama file company profile',
ADD COLUMN company_profile_file_size BIGINT NULL COMMENT 'Ukuran file company profile',
ADD COLUMN company_profile_upload_date DATETIME NULL COMMENT 'Tanggal upload company profile',

ADD COLUMN surat_keagenan_file_path VARCHAR(500) NULL COMMENT 'Path file surat keagenan',
ADD COLUMN surat_keagenan_file_name VARCHAR(255) NULL COMMENT 'Nama file surat keagenan',
ADD COLUMN surat_keagenan_file_size BIGINT NULL COMMENT 'Ukuran file surat keagenan',
ADD COLUMN surat_keagenan_upload_date DATETIME NULL COMMENT 'Tanggal upload surat keagenan',

ADD COLUMN tkdn_file_path VARCHAR(500) NULL COMMENT 'Path file TKDN',
ADD COLUMN tkdn_file_name VARCHAR(255) NULL COMMENT 'Nama file TKDN',
ADD COLUMN tkdn_file_size BIGINT NULL COMMENT 'Ukuran file TKDN',
ADD COLUMN tkdn_upload_date DATETIME NULL COMMENT 'Tanggal upload TKDN',

ADD COLUMN surat_pernyataan_manufaktur_file_path VARCHAR(500) NULL COMMENT 'Path file surat pernyataan manufaktur',
ADD COLUMN surat_pernyataan_manufaktur_file_name VARCHAR(255) NULL COMMENT 'Nama file surat pernyataan manufaktur',
ADD COLUMN surat_pernyataan_manufaktur_file_size BIGINT NULL COMMENT 'Ukuran file surat pernyataan manufaktur',
ADD COLUMN surat_pernyataan_manufaktur_upload_date DATETIME NULL COMMENT 'Tanggal upload surat pernyataan manufaktur';

-- Add indexes for better performance
CREATE INDEX idx_vendor_akta_perusahaan ON vendors(akta_perusahaan_upload_date);
CREATE INDEX idx_vendor_nib ON vendors(nib_upload_date);
CREATE INDEX idx_vendor_npwp ON vendors(npwp_upload_date);
CREATE INDEX idx_vendor_company_profile ON vendors(company_profile_upload_date);
CREATE INDEX idx_vendor_surat_keagenan ON vendors(surat_keagenan_upload_date);
CREATE INDEX idx_vendor_tkdn ON vendors(tkdn_upload_date);
CREATE INDEX idx_vendor_surat_manufaktur ON vendors(surat_pernyataan_manufaktur_upload_date);
