-- Migration: Add KTP fields to vendors table
-- Date: 2024-01-XX
-- Description: Menambahkan field KTP Direktur/Penanggung Jawab dan file attachment

-- Add new columns to vendors table
ALTER TABLE vendors 
ADD COLUMN ktp_director_name VARCHAR(255) NULL COMMENT 'Nama direktur/penanggung jawab' AFTER bank_account,
ADD COLUMN ktp_director_number VARCHAR(50) NULL COMMENT 'Nomor KTP direktur/penanggung jawab' AFTER ktp_director_name,
ADD COLUMN ktp_director_file_path VARCHAR(500) NULL COMMENT 'Path file KTP yang diupload' AFTER ktp_director_number,
ADD COLUMN ktp_director_file_name VARCHAR(255) NULL COMMENT 'Nama file KTP asli' AFTER ktp_director_file_path,
ADD COLUMN ktp_director_file_size BIGINT NULL COMMENT 'Ukuran file KTP dalam bytes' AFTER ktp_director_file_name,
ADD COLUMN ktp_director_upload_date DATETIME NULL COMMENT 'Tanggal upload file KTP' AFTER ktp_director_file_size;

-- Add indexes for better performance
CREATE INDEX idx_vendor_ktp_director ON vendors(ktp_director_number);
CREATE INDEX idx_vendor_ktp_upload ON vendors(ktp_director_upload_date);