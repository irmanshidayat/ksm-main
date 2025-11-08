-- Migration untuk menambah tabel user_email_domains
-- File: add_user_email_domains.sql

CREATE TABLE IF NOT EXISTS user_email_domains (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    domain_name VARCHAR(100) NOT NULL COMMENT 'Nama domain email (contoh: company.com)',
    smtp_server VARCHAR(255) NOT NULL COMMENT 'Server SMTP (contoh: smtp.company.com)',
    smtp_port INT NOT NULL COMMENT 'Port SMTP (biasanya 587 atau 465)',
    username VARCHAR(255) NOT NULL COMMENT 'Username email (contoh: user@company.com)',
    password VARCHAR(500) NOT NULL COMMENT 'Password email yang dienkripsi',
    from_name VARCHAR(255) NOT NULL COMMENT 'Nama pengirim (contoh: Company Name)',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Status aktif konfigurasi',
    is_default BOOLEAN DEFAULT FALSE COMMENT 'Konfigurasi default untuk user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Tanggal dibuat',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Tanggal diupdate',
    
    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Index untuk performa
    INDEX idx_user_id (user_id),
    INDEX idx_domain_name (domain_name),
    INDEX idx_is_active (is_active),
    INDEX idx_is_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Konfigurasi email domain per user';

-- Insert sample data untuk testing (optional)
-- INSERT INTO user_email_domains (user_id, domain_name, smtp_server, smtp_port, username, password, from_name, is_active, is_default) 
-- VALUES (1, 'ksm.com', 'smtp.gmail.com', 587, 'test@ksm.com', 'encrypted_password_here', 'KSM Company', TRUE, TRUE);
