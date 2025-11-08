-- Migration: Add selected_quantity column to vendor_penawaran_items table
-- Date: 2025-10-17
-- Description: Add selected_quantity field to support quantity splitting in vendor selection

-- Add selected_quantity column to vendor_penawaran_items table
ALTER TABLE vendor_penawaran_items 
ADD COLUMN selected_quantity INTEGER NULL 
COMMENT 'Quantity yang dipilih untuk split selection';

-- Add index for better performance on selected_quantity queries
CREATE INDEX idx_vendor_penawaran_item_selected_quantity 
ON vendor_penawaran_items(selected_quantity);

-- Update existing records to set selected_quantity = vendor_quantity where is_selected = true
UPDATE vendor_penawaran_items 
SET selected_quantity = vendor_quantity 
WHERE is_selected = true AND selected_quantity IS NULL;
