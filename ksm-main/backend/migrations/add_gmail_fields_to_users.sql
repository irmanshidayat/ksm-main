-- Migration: Add Gmail fields to users table
-- Description: Menambah field untuk Gmail OAuth integration
-- Date: 2024-01-XX

-- Add Gmail fields to users table
ALTER TABLE users 
ADD COLUMN gmail_refresh_token TEXT,
ADD COLUMN gmail_access_token TEXT,
ADD COLUMN gmail_token_expires_at DATETIME,
ADD COLUMN gmail_connected BOOLEAN DEFAULT FALSE;

-- Create email_logs table untuk tracking email yang dikirim
CREATE TABLE IF NOT EXISTS email_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    vendor_email VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    status ENUM('sent', 'failed', 'pending') DEFAULT 'pending',
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    message_id VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_vendor_email (vendor_email),
    INDEX idx_status (status),
    INDEX idx_sent_at (sent_at)
);

-- Add index untuk Gmail fields
CREATE INDEX idx_gmail_connected ON users(gmail_connected);
CREATE INDEX idx_gmail_token_expires ON users(gmail_token_expires_at);

-- Update existing users untuk set gmail_connected = FALSE
UPDATE users SET gmail_connected = FALSE WHERE gmail_connected IS NULL;
