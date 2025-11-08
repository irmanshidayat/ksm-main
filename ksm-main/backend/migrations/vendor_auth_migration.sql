-- Migration untuk Vendor Authentication System
-- Menambahkan integrasi vendor dengan user account

-- 1. Tambahkan kolom vendor_id ke tabel users
ALTER TABLE users ADD COLUMN vendor_id INT;
ALTER TABLE users ADD FOREIGN KEY (vendor_id) REFERENCES vendors(id);

-- 2. Tambahkan kolom user_id ke tabel vendors
ALTER TABLE vendors ADD COLUMN user_id INT;
ALTER TABLE vendors ADD FOREIGN KEY (user_id) REFERENCES users(id);

-- 3. Tambahkan kolom upload_status ke tabel vendor_penawaran
ALTER TABLE vendor_penawaran ADD COLUMN upload_status ENUM('draft', 'uploaded', 'under_review', 'approved', 'rejected') DEFAULT 'draft';
ALTER TABLE vendor_penawaran ADD COLUMN upload_count INT DEFAULT 0;
ALTER TABLE vendor_penawaran ADD COLUMN last_upload_at DATETIME;

-- 4. Buat tabel vendor_questions untuk sistem pertanyaan/clarification
CREATE TABLE vendor_questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vendor_id INT NOT NULL,
    request_id INT NOT NULL,
    question TEXT NOT NULL,
    category ENUM('technical', 'commercial', 'timeline', 'other') DEFAULT 'other',
    status ENUM('pending', 'answered', 'closed') DEFAULT 'pending',
    answer TEXT,
    answered_by INT,
    answered_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    FOREIGN KEY (request_id) REFERENCES request_pembelian(id) ON DELETE CASCADE,
    FOREIGN KEY (answered_by) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_vendor_questions_vendor (vendor_id),
    INDEX idx_vendor_questions_request (request_id),
    INDEX idx_vendor_questions_status (status),
    INDEX idx_vendor_questions_category (category),
    INDEX idx_vendor_questions_created (created_at)
);

-- 5. Buat tabel vendor_templates untuk sistem template download
CREATE TABLE vendor_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    file_type ENUM('excel', 'pdf', 'word') NOT NULL,
    category ENUM('proposal', 'company_profile', 'technical_spec', 'cover_letter', 'checklist') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    download_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_vendor_templates_type (file_type),
    INDEX idx_vendor_templates_category (category),
    INDEX idx_vendor_templates_active (is_active)
);

-- 6. Buat tabel vendor_notifications untuk sistem notifikasi
CREATE TABLE vendor_notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vendor_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('deadline_warning', 'status_update', 'new_request', 'system') NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    related_request_id INT,
    related_penawaran_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME,
    
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
    FOREIGN KEY (related_request_id) REFERENCES request_pembelian(id) ON DELETE CASCADE,
    FOREIGN KEY (related_penawaran_id) REFERENCES vendor_penawaran(id) ON DELETE CASCADE,
    
    INDEX idx_vendor_notifications_vendor (vendor_id),
    INDEX idx_vendor_notifications_type (type),
    INDEX idx_vendor_notifications_read (is_read),
    INDEX idx_vendor_notifications_created (created_at)
);

-- 7. Insert default templates
INSERT INTO vendor_templates (name, description, file_path, file_type, category) VALUES
('Template Proposal Excel', 'Template untuk breakdown harga dan spesifikasi teknis', '/templates/proposal_template.xlsx', 'excel', 'proposal'),
('Company Profile Template', 'Template untuk company profile', '/templates/company_profile.pdf', 'pdf', 'company_profile'),
('Technical Specification Template', 'Template untuk spesifikasi teknis', '/templates/technical_spec.docx', 'word', 'technical_spec'),
('Cover Letter Template', 'Template untuk surat penawaran', '/templates/cover_letter.docx', 'word', 'cover_letter'),
('Requirements Checklist', 'Checklist persyaratan penawaran', '/templates/requirements_checklist.pdf', 'pdf', 'checklist');

-- 8. Update existing vendors yang sudah ada untuk membuat user account
-- (Ini akan dijalankan oleh service, bukan langsung di migration)

-- 9. Add file_hash column to vendor_penawaran_files table
ALTER TABLE vendor_penawaran_files ADD COLUMN file_hash VARCHAR(64);

-- 10. Create vendor_notifications table
CREATE TABLE vendor_notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vendor_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('deadline_warning', 'status_update', 'new_request', 'system', 'other') NOT NULL,
    related_request_id INT,
    related_penawaran_id INT,
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id),
    FOREIGN KEY (related_request_id) REFERENCES request_pembelian(id),
    FOREIGN KEY (related_penawaran_id) REFERENCES vendor_penawaran(id),
    INDEX idx_vendor_notification_vendor (vendor_id),
    INDEX idx_vendor_notification_type (type),
    INDEX idx_vendor_notification_read (is_read),
    INDEX idx_vendor_notification_created (created_at)
);
