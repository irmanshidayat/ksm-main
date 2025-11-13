# 📘 Tutorial Docker KSM Main - Versi Sederhana

## 🚀 Quick Start

### 1. Persiapan File .env

```powershell
# Masuk ke direktori ksm-main
cd "C:\Irman\Coding KSM Main\KSM Grup - dev\ksm-main"

# Copy env.example ke .env
copy env.example .env
```

**Edit file `.env` dan pastikan:**
```env
DB_PASSWORD=admin123
DATABASE_URL=mysql+pymysql://root:admin123@mysql-prod:3306/KSM_main
```

**⚠️ PENTING:** 
- Pastikan hanya ada **satu baris** `DB_PASSWORD=admin123` (hapus duplikat)
- Jangan gunakan format dengan `-` di awal baris (itu untuk komentar YAML, bukan .env)
- Semua baris yang dimulai dengan `-` harus diubah menjadi komentar dengan `#`

### 2. Generate SSL Certificate (Jika Belum Ada)

```powershell
# Buat direktori ssl
mkdir infrastructure\nginx\ssl -Force

# Generate self-signed certificate menggunakan Docker
docker run --rm -v "${PWD}/infrastructure/nginx/ssl:/ssl" alpine/openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /ssl/key.pem -out /ssl/cert.pem -subj "/C=ID/ST=Jakarta/L=Jakarta/O=KSM/CN=report.ptkiansatang.com"
```

### 3. Jalankan Docker

```powershell
# Build dan start semua services
docker-compose up -d --build

# Cek status
docker-compose ps
```

**Waktu build pertama kali:** 10-30 menit

---

## ✅ Verifikasi

### Cek Status Containers

```powershell
docker-compose ps
```

Semua container harus **Up** dan **healthy**:
- ✅ KSM-mysql-prod (healthy)
- ✅ KSM-redis-prod (healthy)
- ✅ KSM-backend-prod (healthy)
- ✅ KSM-frontend-prod (healthy)
- ✅ KSM-nginx-prod (healthy)
- ✅ KSM-agent-ai-prod (running - mungkin unhealthy karena LLM service, tapi tetap berfungsi)

### Test Health Checks

```powershell
# Backend
curl http://localhost:8001/api/health

# Agent AI
curl http://localhost:5001/health

# Frontend
curl http://localhost:3002
```

---

## 🌐 Akses Aplikasi

- **Frontend:** http://localhost:3002
- **Backend API:** http://localhost:8001/api
- **Agent AI:** http://localhost:5001
- **Nginx:** http://localhost:8082
- **Grafana:** http://localhost:3003 (username: admin)

---

## 🔧 Troubleshooting Umum

### 1. Port Sudah Digunakan

**Error:** `Bind for 0.0.0.0:8082 failed: port is already allocated`

**Solusi:**
```powershell
# Cek port yang digunakan
netstat -ano | findstr :8082

# Stop container yang menggunakan port
docker stop [container-name]
docker rm [container-name]

# Atau restart service
docker-compose restart nginx-prod
```

### 2. Backend Stop Sendiri

**Penyebab:**
- Module `psutil` missing
- Password database tidak sesuai
- Format `.env` file tidak valid

**Solusi:**

**a. Pastikan `psutil` ada di requirements.txt:**
```txt
psutil>=5.9.0
```

**b. Rebuild backend:**
```powershell
docker-compose build --no-cache ksm-backend-prod
docker-compose up -d ksm-backend-prod
```

**c. Pastikan password database sesuai:**
- MySQL container: `admin123`
- File `.env`: `DB_PASSWORD=admin123`
- Docker-compose.yml: sudah include `DB_PASSWORD=${DB_PASSWORD}`

**d. Perbaiki format .env:**
```powershell
# Hapus semua baris yang dimulai dengan `-` (kecuali yang sudah ada `#`)
# Ubah menjadi komentar dengan menambahkan `#` di depan
```

### 3. Database Connection Error

**Error:** `Access denied for user 'root'@'172.21.0.x' (using password: YES)`

**Solusi:**

**a. Pastikan password di .env sesuai:**
```env
DB_PASSWORD=admin123
```

**b. Pastikan docker-compose.yml sudah include:**
```yaml
environment:
  - DB_HOST=mysql-prod
  - DB_PORT=3306
  - DB_NAME=KSM_main
  - DB_USER=root
  - DB_PASSWORD=${DB_PASSWORD}
  - DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@mysql-prod:3306/KSM_main
```

**c. Recreate container:**
```powershell
docker-compose stop ksm-backend-prod
docker-compose rm -f ksm-backend-prod
docker-compose up -d ksm-backend-prod
```

### 4. Nginx Error: "add_header directive is not allowed here"

**Solusi:**
Hapus `add_header` dari dalam blok `if` di `nginx.prod.conf`:

```nginx
# SEBELUM (SALAH):
if ($request_method = 'OPTIONS') {
    add_header Access-Control-Allow-Origin "...";
    return 204;
}

# SESUDAH (BENAR):
if ($request_method = 'OPTIONS') {
    return 204;
}
```

Header CORS sudah di-set di luar blok `if` dengan `always`, jadi akan tetap berlaku.

### 5. SSL Certificate Tidak Ditemukan

**Error:** `cannot load certificate "/etc/nginx/ssl/cert.pem"`

**Solusi:**
Generate certificate (lihat langkah 2 di Quick Start)

### 6. Container Unhealthy

**Cek logs:**
```powershell
docker logs KSM-backend-prod --tail 50
docker logs KSM-agent-ai-prod --tail 50
```

**Restart service:**
```powershell
docker-compose restart [service-name]
```

Kesimpulan
Rebuild: perubahan kode, Dockerfile, dependencies, file baru
Restart: perubahan env vars, volumes, ports, konfigurasi runtime
Untuk perubahan docker-entrypoint.sh dan Dockerfile.production yang baru dilakukan, perlu rebuild.

---

## 📚 Perintah Penting

### Start/Stop Services

```powershell
# Start semua
docker-compose up -d

# Stop semua
docker-compose stop

# Restart service tertentu
docker-compose restart ksm-backend-prod

# Stop dan remove
docker-compose down
```

### View Logs

```powershell
# Semua services
docker-compose logs -f

# Service tertentu
docker-compose logs -f ksm-backend-prod
docker logs KSM-backend-prod --tail 50
```

### Rebuild Service

```powershell
# Rebuild dan restart
docker-compose up -d --build ksm-backend-prod

# Rebuild tanpa cache
docker-compose build --no-cache ksm-backend-prod
docker-compose up -d ksm-backend-prod
```

### Cek Environment Variables

```powershell
# Cek di container
docker exec KSM-backend-prod env | findstr DB_
docker exec KSM-mysql-prod env | findstr MYSQL_ROOT_PASSWORD
```

---

## ⚙️ Konfigurasi Penting

### File .env

**Format yang BENAR:**
```env
DB_PASSWORD=admin123
DATABASE_URL=mysql+pymysql://root:admin123@mysql-prod:3306/KSM_main
```

**Format yang SALAH:**
```env
   - DB_PASSWORD=admin123    # ❌ Jangan gunakan `-` di awal
DB_PASSWORD=                 # ❌ Jangan kosong
```

### docker-compose.yml

**Backend harus include:**
```yaml
environment:
  - DB_HOST=mysql-prod
  - DB_PORT=3306
  - DB_NAME=KSM_main
  - DB_USER=root
  - DB_PASSWORD=${DB_PASSWORD}
  - DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@mysql-prod:3306/KSM_main
```

**⚠️ PENTING:** Gunakan `mysql+pymysql://` bukan `mysql://` untuk PyMySQL driver.

### requirements.txt (Backend)

**Pastikan ada:**
```txt
psutil>=5.9.0
PyMySQL==1.1.1
SQLAlchemy==2.0.25
```

---

## 🔍 Checklist Sebelum Deploy

- [ ] File `.env` sudah dikonfigurasi dengan benar
- [ ] `DB_PASSWORD=admin123` (hanya satu baris, tidak duplikat)
- [ ] Format `.env` valid (tidak ada baris dengan `-` di awal)
- [ ] SSL certificate sudah ada di `infrastructure/nginx/ssl/`
- [ ] `psutil` sudah ada di `backend/requirements.txt`
- [ ] `DATABASE_URL` menggunakan `mysql+pymysql://`
- [ ] Docker-compose.yml sudah include semua environment variables yang diperlukan
- [ ] Semua containers berjalan dan healthy

---

## 🚨 Quick Fix Commands

```powershell
# Fix .env format (hapus baris dengan `-`)
$lines = Get-Content .env; $newLines = @(); foreach ($line in $lines) { if ($line -match '^-' -and $line -notmatch '^#') { $newLines += "# $line" } else { $newLines += $line } }; $newLines | Set-Content .env

# Fix DB_PASSWORD (pastikan hanya satu dengan nilai admin123)
$content = Get-Content .env; $newContent = @(); $dbPasswordSet = $false; foreach ($line in $content) { if ($line -match '^DB_PASSWORD=' -and $line -notmatch '^#') { if (-not $dbPasswordSet) { $newContent += 'DB_PASSWORD=admin123'; $dbPasswordSet = $true } } else { $newContent += $line } }; $newContent | Set-Content .env

# Recreate backend dengan environment baru
docker-compose stop ksm-backend-prod && docker-compose rm -f ksm-backend-prod && docker-compose up -d ksm-backend-prod

# Cek semua status
docker-compose ps
```

---

## 📝 Catatan Penting

1. **Development vs Production:**
   - Development: Gunakan XAMPP lokal, tidak perlu Docker
   - Production: Gunakan Docker dengan semua services

2. **Port yang Digunakan:**
   - 3308: MySQL (external)
   - 6380: Redis (external)
   - 5001: Agent AI
   - 8001: Backend
   - 3002: Frontend
   - 8082: Nginx HTTP
   - 8443: Nginx HTTPS

3. **Auto-Detection:**
   - Aplikasi otomatis detect Docker environment
   - Tidak perlu set `RUN_MODE` manual

4. **Password Default:**
   - MySQL: `admin123`
   - Pastikan semua service menggunakan password yang sama

---

**Selamat! Docker setup sudah selesai! 🎉**
