-- Migration: Create vendor_orders table
-- Created: 2025-01-17
-- Description: Create table for tracking vendor purchase orders with status management

CREATE TABLE IF NOT EXISTS `vendor_orders` (
    `id` INT(11) NOT NULL AUTO_INCREMENT,
    
    -- Order Identification
    `order_number` VARCHAR(50) NOT NULL UNIQUE,
    `vendor_penawaran_item_id` INT(11) NOT NULL,
    `vendor_id` INT(11) NOT NULL,
    `request_id` INT(11) NOT NULL,
    `reference_id` VARCHAR(50) NOT NULL,
    
    -- Order Details (denormalized for performance)
    `item_name` VARCHAR(255) NOT NULL,
    `ordered_quantity` INT(11) NOT NULL,
    `unit_price` DECIMAL(15,2) NOT NULL,
    `total_price` DECIMAL(15,2) NOT NULL,
    `specifications` TEXT NULL,
    
    -- Status Tracking
    `status` ENUM(
        'pending_confirmation', 
        'confirmed', 
        'processing', 
        'shipped', 
        'delivered', 
        'completed', 
        'cancelled'
    ) NOT NULL DEFAULT 'pending_confirmation',
    
    -- Confirmation Tracking
    `confirmed_at` DATETIME NULL,
    `confirmed_by_vendor` BOOLEAN DEFAULT FALSE,
    
    -- Processing Tracking
    `processing_started_at` DATETIME NULL,
    `shipped_at` DATETIME NULL,
    `delivered_at` DATETIME NULL,
    `completed_at` DATETIME NULL,
    
    -- Delivery Information
    `tracking_number` VARCHAR(100) NULL,
    `estimated_delivery_date` DATETIME NULL,
    `actual_delivery_date` DATETIME NULL,
    `delivery_notes` TEXT NULL,
    
    -- Notes
    `vendor_notes` TEXT NULL,
    `admin_notes` TEXT NULL,
    
    -- Audit Trail
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `created_by_user_id` INT(11) NOT NULL,
    
    PRIMARY KEY (`id`),
    
    -- Foreign Key Constraints
    CONSTRAINT `fk_vendor_orders_penawaran_item` 
        FOREIGN KEY (`vendor_penawaran_item_id`) 
        REFERENCES `vendor_penawaran_items` (`id`) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    CONSTRAINT `fk_vendor_orders_vendor` 
        FOREIGN KEY (`vendor_id`) 
        REFERENCES `vendors` (`id`) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    CONSTRAINT `fk_vendor_orders_request` 
        FOREIGN KEY (`request_id`) 
        REFERENCES `request_pembelian` (`id`) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    CONSTRAINT `fk_vendor_orders_created_by` 
        FOREIGN KEY (`created_by_user_id`) 
        REFERENCES `users` (`id`) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    -- Indexes for Performance
    INDEX `idx_vendor_orders_order_number` (`order_number`),
    INDEX `idx_vendor_orders_vendor` (`vendor_id`),
    INDEX `idx_vendor_orders_request` (`request_id`),
    INDEX `idx_vendor_orders_reference` (`reference_id`),
    INDEX `idx_vendor_orders_status` (`status`),
    INDEX `idx_vendor_orders_penawaran_item` (`vendor_penawaran_item_id`),
    INDEX `idx_vendor_orders_created` (`created_at`),
    INDEX `idx_vendor_orders_updated` (`updated_at`),
    INDEX `idx_vendor_orders_confirmed` (`confirmed_at`),
    INDEX `idx_vendor_orders_delivery` (`estimated_delivery_date`),
    
    -- Composite Indexes
    INDEX `idx_vendor_orders_vendor_status` (`vendor_id`, `status`),
    INDEX `idx_vendor_orders_request_status` (`request_id`, `status`),
    INDEX `idx_vendor_orders_created_by_status` (`created_by_user_id`, `status`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add comment to table
ALTER TABLE `vendor_orders` 
COMMENT = 'Table untuk tracking pesanan vendor dengan status management lengkap';

-- Create trigger untuk auto-generate order_number
DELIMITER $$

CREATE TRIGGER `tr_vendor_orders_order_number` 
BEFORE INSERT ON `vendor_orders`
FOR EACH ROW
BEGIN
    IF NEW.order_number IS NULL OR NEW.order_number = '' THEN
        SET NEW.order_number = CONCAT('ORD-', DATE_FORMAT(NOW(), '%Y%m%d'), '-', LPAD(LAST_INSERT_ID() + 1, 6, '0'));
    END IF;
END$$

DELIMITER ;

-- Insert sample data untuk testing (optional - bisa dihapus di production)
-- INSERT INTO `vendor_orders` (
--     `vendor_penawaran_item_id`, `vendor_id`, `request_id`, `reference_id`,
--     `item_name`, `ordered_quantity`, `unit_price`, `total_price`,
--     `status`, `created_by_user_id`
-- ) VALUES (
--     1, 1, 1, 'REQ-20250117-001',
--     'Sample Item', 10, 100000.00, 1000000.00,
--     'pending_confirmation', 1
-- );
