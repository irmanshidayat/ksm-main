-- Migration: Add vendor_type and business_model fields to vendors table
-- Date: 2024-01-XX
-- Description: Menambahkan field vendor_type dan business_model untuk membedakan vendor internal dan mitra

-- Add new columns to vendors table
ALTER TABLE vendors 
ADD COLUMN vendor_type ENUM('internal', 'partner') DEFAULT 'internal' NOT NULL AFTER vendor_category,
ADD COLUMN business_model ENUM('supplier', 'reseller', 'both') DEFAULT 'supplier' NOT NULL AFTER vendor_type;

-- Add indexes for better performance
CREATE INDEX idx_vendor_type ON vendors(vendor_type);
CREATE INDEX idx_vendor_business_model ON vendors(business_model);

-- Update existing vendors to have default values
UPDATE vendors SET vendor_type = 'internal', business_model = 'supplier' WHERE vendor_type IS NULL OR business_model IS NULL;

-- Add comments for documentation
ALTER TABLE vendors MODIFY COLUMN vendor_type ENUM('internal', 'partner') DEFAULT 'internal' NOT NULL COMMENT 'Jenis vendor: internal untuk kebutuhan internal, partner untuk vendor mitra';
ALTER TABLE vendors MODIFY COLUMN business_model ENUM('supplier', 'reseller', 'both') DEFAULT 'supplier' NOT NULL COMMENT 'Model bisnis: supplier untuk pemasok, reseller untuk penjual ulang, both untuk keduanya';
