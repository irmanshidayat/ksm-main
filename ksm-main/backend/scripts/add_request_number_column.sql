-- Script untuk menambahkan kolom request_number ke tabel request_pembelian
-- Jalankan script ini jika kolom request_number belum ada di database

USE KSM_main;

-- Cek apakah kolom request_number sudah ada
-- Jika belum ada, tambahkan kolom
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'KSM_main' 
    AND TABLE_NAME = 'request_pembelian' 
    AND COLUMN_NAME = 'request_number'
);

-- Tambahkan kolom jika belum ada
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE request_pembelian ADD COLUMN request_number VARCHAR(50) NULL',
    'SELECT "Column request_number already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Buat index untuk request_number
CREATE INDEX IF NOT EXISTS idx_request_number ON request_pembelian(request_number);

-- Populate request_number dari reference_id jika request_number NULL
UPDATE request_pembelian
SET request_number = reference_id
WHERE request_number IS NULL AND reference_id IS NOT NULL;

-- Generate request_number jika masih NULL (untuk data yang tidak punya keduanya)
UPDATE request_pembelian
SET request_number = CONCAT('PR-', DATE_FORMAT(COALESCE(created_at, NOW()), '%Y%m%d'), '-', LPAD(id, 4, '0'))
WHERE request_number IS NULL;

-- Set NOT NULL setelah semua data di-populate
SET @null_count = (SELECT COUNT(*) FROM request_pembelian WHERE request_number IS NULL);
SET @sql2 = IF(@null_count = 0,
    'ALTER TABLE request_pembelian MODIFY COLUMN request_number VARCHAR(50) NOT NULL',
    'SELECT "Cannot set NOT NULL: there are NULL values" AS message'
);
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

SELECT 'Migration completed successfully' AS result;

