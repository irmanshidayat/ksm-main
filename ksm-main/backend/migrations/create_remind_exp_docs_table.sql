-- Migration untuk membuat tabel remind_exp_docs
-- Tanggal: 2024-01-XX
-- Deskripsi: Tabel untuk menyimpan data dokumen yang akan expired dengan fitur reminder

CREATE TABLE IF NOT EXISTS remind_exp_docs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL COMMENT 'Nama dokumen/sertifikasi',
    document_number VARCHAR(100) NULL COMMENT 'Nomor dokumen',
    document_type VARCHAR(100) NULL COMMENT 'Jenis dokumen (Sertifikat, Izin, dll)',
    issuer VARCHAR(255) NULL COMMENT 'Penerbit dokumen',
    expiry_date DATE NOT NULL COMMENT 'Tanggal expired',
    reminder_days_before INT DEFAULT 30 COMMENT 'Berapa hari sebelum expired untuk reminder',
    status ENUM('active', 'expired', 'inactive') DEFAULT 'active' COMMENT 'Status dokumen',
    description TEXT NULL COMMENT 'Deskripsi tambahan',
    file_path VARCHAR(500) NULL COMMENT 'Path file dokumen jika ada',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Tanggal dibuat',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Tanggal diupdate',
    
    -- Index untuk optimasi query
    INDEX idx_expiry_date (expiry_date),
    INDEX idx_status (status),
    INDEX idx_document_type (document_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabel untuk reminder dokumen yang akan expired';

-- Insert data contoh (opsional)
INSERT INTO remind_exp_docs (document_name, document_number, document_type, issuer, expiry_date, reminder_days_before, description) VALUES
('Sertifikat ISO 9001:2015', 'ISO-2024-001', 'Sertifikat ISO', 'Bureau Veritas', DATE_ADD(CURDATE(), INTERVAL 6 MONTH), 30, 'Sertifikat ISO 9001:2015 untuk sistem manajemen mutu'),
('Izin Usaha', 'IU-2024-001', 'Izin Usaha', 'Dinas Perindustrian', DATE_ADD(CURDATE(), INTERVAL 3 MONTH), 30, 'Izin usaha untuk operasional perusahaan'),
('Sertifikat Halal', 'HAL-2024-001', 'Sertifikat Halal', 'MUI', DATE_ADD(CURDATE(), INTERVAL 1 YEAR), 30, 'Sertifikat halal untuk produk makanan');
