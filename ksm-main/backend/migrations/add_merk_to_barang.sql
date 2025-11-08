-- Migration: Add merk column to barang table
-- Date: 2024-01-XX
-- Description: Menambahkan kolom merk (optional) ke tabel barang untuk menyimpan informasi merek produk

-- Add merk column to barang table
ALTER TABLE barang 
ADD COLUMN merk VARCHAR(100) NULL 
COMMENT 'Merek/brand dari produk (optional)';

-- Add index for better performance on merk searches
CREATE INDEX idx_barang_merk ON barang(merk);

-- Update existing records to have NULL merk (optional field)
-- No need to update existing data as it's optional
