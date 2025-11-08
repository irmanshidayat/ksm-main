-- Add vendor_merk field to vendor_penawaran_items table
-- Migration: Add vendor_merk field to vendor_penawaran_items table

ALTER TABLE vendor_penawaran_items 
ADD COLUMN vendor_merk VARCHAR(255) NULL 
AFTER vendor_notes;

-- Add index for better performance
CREATE INDEX idx_vendor_penawaran_items_merk ON vendor_penawaran_items(vendor_merk);

-- Update existing records to have empty string for vendor_merk if NULL
UPDATE vendor_penawaran_items 
SET vendor_merk = '' 
WHERE vendor_merk IS NULL;
