-- Migration: Create email_attachments table
-- Created: 2025-01-28
-- Description: Table untuk menyimpan metadata file attachment email

CREATE TABLE IF NOT EXISTS email_attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- File information
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL COMMENT 'Size in bytes',
    mime_type VARCHAR(100) NOT NULL,
    file_extension VARCHAR(10) DEFAULT NULL,
    
    -- Relationship to request pembelian (optional)
    request_pembelian_id INT DEFAULT NULL,
    
    -- User who uploaded the file
    uploaded_by_user_id INT NOT NULL,
    
    -- Email information (optional - for tracking which email this was attached to)
    email_subject VARCHAR(255) DEFAULT NULL,
    email_recipient VARCHAR(255) DEFAULT NULL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active' COMMENT 'active, deleted, expired',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    
    -- Foreign key constraints
    FOREIGN KEY (request_pembelian_id) REFERENCES request_pembelian(id) ON DELETE SET NULL,
    FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_uploaded_by_user (uploaded_by_user_id),
    INDEX idx_request_pembelian (request_pembelian_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_file_extension (file_extension),
    INDEX idx_mime_type (mime_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add comments
ALTER TABLE email_attachments COMMENT = 'Table untuk menyimpan metadata file attachment email';

-- Insert sample data (optional - for testing)
-- INSERT INTO email_attachments (original_filename, stored_filename, file_path, file_size, mime_type, file_extension, uploaded_by_user_id, status) 
-- VALUES ('sample.pdf', 'abc123.pdf', '/uploads/email-attachments/2025/01/abc123.pdf', 1024, 'application/pdf', '.pdf', 1, 'active');
