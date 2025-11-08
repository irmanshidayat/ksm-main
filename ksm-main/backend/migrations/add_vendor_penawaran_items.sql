-- Migration: Add vendor_penawaran_items table
-- Created: 2024-12-19
-- Description: Create table for storing detailed vendor quotation items

CREATE TABLE IF NOT EXISTS `vendor_penawaran_items` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    `vendor_penawaran_id` INT(11) NOT NULL,
    `nama_barang` VARCHAR(255) NOT NULL,
    `quantity` INT(11) NOT NULL,
    `harga_satuan` DECIMAL(15,2) NOT NULL,
    `harga_total` DECIMAL(15,2) NOT NULL,
    `spesifikasi` TEXT NULL,
    `kategori` VARCHAR(100) NULL,
    `satuan` VARCHAR(50) NULL,
    `merek` VARCHAR(100) NULL,
    `garansi` VARCHAR(100) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_vendor_penawaran_item_penawaran` (`vendor_penawaran_id`),
    INDEX `idx_vendor_penawaran_item_nama` (`nama_barang`),
    INDEX `idx_vendor_penawaran_item_kategori` (`kategori`),
    INDEX `idx_vendor_penawaran_item_merek` (`merek`),
    INDEX `idx_vendor_penawaran_item_created` (`created_at`),
    CONSTRAINT `fk_vendor_penawaran_items_penawaran` 
        FOREIGN KEY (`vendor_penawaran_id`) 
        REFERENCES `vendor_penawaran` (`id`) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add comment to table
ALTER TABLE `vendor_penawaran_items` 
COMMENT = 'Table untuk menyimpan detail item dalam penawaran vendor';
