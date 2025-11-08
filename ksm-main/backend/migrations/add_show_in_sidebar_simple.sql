-- Migration untuk menambahkan kolom show_in_sidebar di tabel menu_permissions
-- Jalankan SQL ini langsung di database MySQL

-- Cek apakah kolom sudah ada, jika belum tambahkan
ALTER TABLE menu_permissions 
ADD COLUMN IF NOT EXISTS show_in_sidebar BOOLEAN DEFAULT TRUE NOT NULL;

-- Update existing records untuk memastikan semua memiliki nilai default
UPDATE menu_permissions 
SET show_in_sidebar = TRUE 
WHERE show_in_sidebar IS NULL;

