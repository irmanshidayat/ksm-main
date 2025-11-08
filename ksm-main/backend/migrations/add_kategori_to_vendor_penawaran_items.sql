-- Migration: Add kategori column to vendor_penawaran_items table
-- Date: 2025-01-22
-- Description: Add kategori field to store category information from bulk import

-- Add kategori column to vendor_penawaran_items table
ALTER TABLE vendor_penawaran_items 
ADD COLUMN kategori VARCHAR(255) NULL;

-- Add index for better performance on kategori queries
CREATE INDEX idx_vendor_penawaran_item_kategori ON vendor_penawaran_items(kategori);

-- Update existing records to set default kategori if needed
-- UPDATE vendor_penawaran_items SET kategori = 'General' WHERE kategori IS NULL;

-- Add comment to the column
ALTER TABLE vendor_penawaran_items 
MODIFY COLUMN kategori VARCHAR(255) NULL COMMENT 'Kategori barang dari vendor';
