-- KSM Main Database Initialization Script untuk Development
-- Script ini akan dijalankan saat container MySQL pertama kali dibuat

-- =============================================================================
-- DATABASE CREATION
-- =============================================================================

-- Buat database KSM_main jika belum ada
CREATE DATABASE IF NOT EXISTS KSM_main CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Buat database agent_ai jika belum ada
CREATE DATABASE IF NOT EXISTS agent_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Buat database test jika belum ada
CREATE DATABASE IF NOT EXISTS KSM_main_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- =============================================================================
-- USER CREATION DAN PERMISSIONS
-- =============================================================================

-- Buat user untuk development
CREATE USER IF NOT EXISTS 'KSM_dev'@'%' IDENTIFIED BY 'KSM_dev_password';
CREATE USER IF NOT EXISTS 'KSM_test'@'%' IDENTIFIED BY 'KSM_test_password';

-- Grant permissions untuk KSM_main database
GRANT ALL PRIVILEGES ON KSM_main.* TO 'KSM_dev'@'%';
GRANT ALL PRIVILEGES ON KSM_main.* TO 'root'@'%';

-- Grant permissions untuk agent_ai database
GRANT ALL PRIVILEGES ON agent_ai.* TO 'KSM_dev'@'%';
GRANT ALL PRIVILEGES ON agent_ai.* TO 'root'@'%';

-- Grant permissions untuk test database
GRANT ALL PRIVILEGES ON KSM_main_test.* TO 'KSM_test'@'%';
GRANT ALL PRIVILEGES ON KSM_main_test.* TO 'KSM_dev'@'%';

-- Grant permissions untuk root user
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

-- Flush privileges
FLUSH PRIVILEGES;

-- =============================================================================
-- KSM_MAIN DATABASE TABLES
-- =============================================================================

USE KSM_main;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role ENUM('admin', 'user', 'vendor') DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Knowledge Base table
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    tags TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- RAG Documents table
CREATE TABLE IF NOT EXISTS rag_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT,
    content TEXT,
    metadata JSON,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Request Pembelian table
CREATE TABLE IF NOT EXISTS request_pembelian (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
    requested_by INT,
    approved_by INT,
    total_amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (requested_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- Stok Barang table
CREATE TABLE IF NOT EXISTS stok_barang (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama_barang VARCHAR(200) NOT NULL,
    kategori VARCHAR(100),
    jumlah INT DEFAULT 0,
    satuan VARCHAR(20),
    harga_satuan DECIMAL(15,2),
    supplier VARCHAR(100),
    lokasi VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =============================================================================
-- AGENT_AI DATABASE TABLES
-- =============================================================================

USE agent_ai;

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    model VARCHAR(100),
    system_prompt TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Usage Logs table
CREATE TABLE IF NOT EXISTS usage_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id INT,
    user_id INT,
    request_text TEXT,
    response_text TEXT,
    tokens_used INT,
    response_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- =============================================================================
-- SAMPLE DATA UNTUK DEVELOPMENT
-- =============================================================================

USE KSM_main;

-- Insert sample users
INSERT IGNORE INTO users (username, email, password_hash, full_name, role) VALUES
('admin', 'admin@KSM.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4.8.2', 'Administrator', 'admin'),
('user1', 'user1@KSM.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4.8.2', 'User One', 'user'),
('vendor1', 'vendor1@KSM.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/4.8.2', 'Vendor One', 'vendor');

-- Insert sample company
INSERT IGNORE INTO companies (name, description, address, phone, email) VALUES
('KSM Grup', 'Perusahaan teknologi dan konsultasi', 'Jakarta, Indonesia', '+62-21-12345678', 'info@KSM.com');

-- Insert sample knowledge base
INSERT IGNORE INTO knowledge_base (title, content, category, tags, created_by) VALUES
('Cara Menggunakan Sistem', 'Panduan lengkap penggunaan sistem KSM', 'Panduan', 'sistem,panduan,user', 1),
('Kebijakan Perusahaan', 'Kebijakan dan aturan perusahaan', 'Kebijakan', 'kebijakan,aturan', 1);

-- Insert sample stok barang
INSERT IGNORE INTO stok_barang (nama_barang, kategori, jumlah, satuan, harga_satuan, supplier, lokasi) VALUES
('Laptop Dell', 'Elektronik', 10, 'unit', 15000000, 'Dell Indonesia', 'Gudang A'),
('Mouse Wireless', 'Aksesoris', 50, 'unit', 150000, 'Logitech', 'Gudang B'),
('Keyboard Mechanical', 'Aksesoris', 25, 'unit', 500000, 'Corsair', 'Gudang B');

-- =============================================================================
-- INDEXES UNTUK PERFORMANCE
-- =============================================================================

-- Indexes untuk users table
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Indexes untuk knowledge_base table
CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_base_created_by ON knowledge_base(created_by);

-- Indexes untuk request_pembelian table
CREATE INDEX idx_request_pembelian_status ON request_pembelian(status);
CREATE INDEX idx_request_pembelian_requested_by ON request_pembelian(requested_by);

-- Indexes untuk stok_barang table
CREATE INDEX idx_stok_barang_kategori ON stok_barang(kategori);
CREATE INDEX idx_stok_barang_supplier ON stok_barang(supplier);

-- =============================================================================
-- DEVELOPMENT SETTINGS
-- =============================================================================

-- Set MySQL untuk development
SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';
SET GLOBAL max_connections = 200;
-- Note: innodb_buffer_pool_size, query_cache_size, dan query_cache_type harus di-set di my.cnf
-- query_cache sudah deprecated di MySQL 8.0

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

SELECT 'KSM Main Database Initialization Completed Successfully!' as message;
