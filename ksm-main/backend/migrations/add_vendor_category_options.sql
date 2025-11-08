-- Migration: Add new vendor category options
-- Date: 2024-01-XX
-- Description: Menambahkan opsi kategori vendor baru dan support untuk kategori custom

-- Add new column for custom category
ALTER TABLE vendors 
ADD COLUMN custom_category VARCHAR(255) NULL COMMENT 'Kategori custom yang dimasukkan manual' AFTER vendor_category;

-- Update existing data to ensure consistency
UPDATE vendors 
SET vendor_category = 'general' 
WHERE vendor_category IS NULL OR vendor_category = '';

-- Add index for better performance on category queries
CREATE INDEX idx_vendor_category ON vendors(vendor_category);
CREATE INDEX idx_vendor_custom_category ON vendors(custom_category);

-- Add constraint to ensure valid categories
ALTER TABLE vendors 
ADD CONSTRAINT chk_vendor_category 
CHECK (vendor_category IN (
    'general', 
    'specialized', 
    'preferred', 
    'supplier', 
    'contractor', 
    'agent_tunggal', 
    'distributor', 
    'jasa', 
    'produk', 
    'custom'
));
