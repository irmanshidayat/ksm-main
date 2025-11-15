# KSM Main - Deployment Guide

## Overview

Proyek ini menggunakan GitHub Actions untuk deployment otomatis ke server dengan 2 environment:

- **Development**: Branch `dev` → Deploy menggunakan `docker-compose.dev.yml`
- **Production**: Branch `main` → Deploy menggunakan `docker-compose.yml`

## Prerequisites

### Server Requirements

1. **Docker** (version 20.10+)
2. **Docker Compose** (version 2.0+)
3. **SSH Access** configured
4. **rsync** (untuk file transfer)

### GitHub Secrets Setup

**PENTING**: Workflow akan gagal jika secrets tidak diatur dengan benar. Pastikan semua secrets yang diperlukan sudah ditambahkan sebelum menjalankan deployment.

#### Cara Menambahkan Secrets di GitHub

1. Buka repository di GitHub
2. Klik **Settings** → **Secrets and variables** → **Actions**
3. Klik **New repository secret**
4. Masukkan **Name** dan **Value**, lalu klik **Add secret**
5. Ulangi untuk semua secrets yang diperlukan

#### Development Secrets (Wajib)

Tambahkan secrets berikut untuk deployment development:

- **`SSH_HOST_DEV`**: IP atau hostname server development
  - Contoh: `72.61.142.109`
  - **Wajib**: Ya
  
- **`SSH_USER_DEV`**: Username SSH untuk development
  - Contoh: `root`
  - **Wajib**: Ya
  
- **`SSH_KEY_DEV`**: Private SSH key untuk development
  - Format: Full private key dengan header dan footer
  - Contoh format:
    ```
    -----BEGIN OPENSSH PRIVATE KEY-----
    b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
    ...
    -----END OPENSSH PRIVATE KEY-----
    ```
  - **Wajib**: Ya
  
- **`DEPLOY_PATH_DEV`**: Path deployment di server
  - Default: `/opt/ksm-main-dev`
  - **Wajib**: Tidak (opsional)

#### Production Secrets (Wajib)

Tambahkan secrets berikut untuk deployment production:

- **`SSH_HOST_PROD`**: IP atau hostname server production
  - Contoh: `72.61.142.109`
  - **Wajib**: Ya
  
- **`SSH_USER_PROD`**: Username SSH untuk production
  - Contoh: `root`
  - **Wajib**: Ya
  
- **`SSH_KEY_PROD`**: Private SSH key untuk production
  - Format: Full private key dengan header dan footer
  - Contoh format:
    ```
    -----BEGIN OPENSSH PRIVATE KEY-----
    b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
    ...
    -----END OPENSSH PRIVATE KEY-----
    ```
  - **Wajib**: Ya
  
- **`DEPLOY_PATH_PROD`**: Path deployment di server
  - Default: `/opt/ksm-main-prod`
  - **Wajib**: Tidak (opsional).

#### Validasi Secrets

Workflow akan otomatis memvalidasi semua secrets yang diperlukan di awal. Jika ada secret yang tidak terdefinisi, workflow akan menampilkan error dengan daftar secrets yang hilang dan instruksi cara memperbaikinya.

**Catatan Penting**: 
- VPS menggunakan port SSH **22** (port default)
- Semua workflow GitHub Actions sudah dikonfigurasi untuk menggunakan port 22
- Untuk koneksi manual, selalu gunakan: `ssh -p 22 user@host` atau `ssh user@host` (port 22 adalah default)

### Generate SSH Key

Jika belum punya SSH key:

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# Copy public key ke server (gunakan port 22)
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub -p 22 user@server

# Atau manual copy public key
cat ~/.ssh/github_actions_deploy.pub | ssh -p 22 user@server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# Copy private key ke GitHub Secrets
cat ~/.ssh/github_actions_deploy
```

**Catatan**: Semua perintah SSH menggunakan port 22 (default). Flag `-p 22` opsional karena 22 adalah port default SSH.

## Deployment Process

### Automatic Deployment

1. **Development**: Push ke branch `dev` → Otomatis deploy ke development server
2. **Production**: Push ke branch `main` → Otomatis deploy ke production server

### Manual Deployment

Ada 2 cara untuk manual deployment:

#### Cara 1: Menggunakan GitHub Actions (Recommended)

1. Buka GitHub Actions tab
2. Pilih workflow yang sesuai (`Deploy Development` atau `Deploy Production`)
3. Klik "Run workflow"
4. Pilih branch dan klik "Run workflow"

#### Cara 2: Manual Deployment via Script (Windows)

Gunakan script PowerShell untuk copy files ke server:

```powershell
# Dari root project directory
cd "C:\Irman\Coding KSM Main\KSM Grup - dev"

# Jalankan script manual deployment
.\scripts\manual-deploy.ps1

# Atau dengan environment spesifik
.\scripts\manual-deploy.ps1 -Environment dev
.\scripts\manual-deploy.ps1 -Environment prod
```

Script akan otomatis:
- Copy docker-compose file
- Copy infrastructure files
- Copy backend files
- Copy frontend files
- Copy Agent AI files

**Setelah script selesai**, SSH ke server dan jalankan:

```bash
# SSH ke server
ssh root@72.61.142.109

# Masuk ke directory deployment
cd /opt/ksm-main-dev  # atau /opt/ksm-main-prod untuk production

# Stop container yang ada (jika ada)
docker-compose -f docker-compose.yml down || true

# Build Docker images
docker-compose -f docker-compose.yml build --no-cache

# Start services
docker-compose -f docker-compose.yml up -d

# Tunggu beberapa detik untuk services start
sleep 30

# Cek status
docker-compose -f docker-compose.yml ps

# Test health endpoints
curl http://localhost:8002/api/health  # dev: 8002, prod: 8001
curl http://localhost:5002/health    # dev: 5002, prod: 5001
curl http://localhost:3006           # dev: 3006, prod: 3005
```

#### Cara 3: Deployment dengan Script Otomatis (RECOMMENDED)

Script otomatis untuk setup dan deployment update sudah tersedia di folder `scripts/`:

**A. Dari Windows PowerShell (Paling Mudah):**

```powershell
# Dari root project directory
cd "C:\Irman\Coding KSM Main\KSM Grup - dev"

# Setup awal untuk development
.\scripts\deploy-auto.ps1 -Environment dev -Action setup

# Setup awal untuk production
.\scripts\deploy-auto.ps1 -Environment prod -Action setup

# Deployment update untuk development
.\scripts\deploy-auto.ps1 -Environment dev -Action update

# Deployment update untuk production
.\scripts\deploy-auto.ps1 -Environment prod -Action update
```

**B. Dari Server Linux (SSH Manual):**

```bash
# SSH ke server
ssh root@72.61.142.109

# Clone repository (jika belum ada)
cd /opt
git clone https://github.com/irmanshidayat/ksm-main.git ksm-main-dev
cd ksm-main-dev
git checkout dev

# Buat script executable
chmod +x scripts/deploy-setup.sh
chmod +x scripts/deploy-update.sh

# Jalankan setup awal
./scripts/deploy-setup.sh dev
# atau untuk production
./scripts/deploy-setup.sh prod

# Deployment update
./scripts/deploy-update.sh dev
# atau untuk production
./scripts/deploy-update.sh prod
```

**Keuntungan Menggunakan Script:**
- ✅ Otomatis - semua langkah dijalankan secara otomatis
- ✅ Error handling - script akan berhenti jika ada error
- ✅ Verifikasi - memastikan struktur direktori benar sebelum build
- ✅ Health check - otomatis test health endpoints setelah deployment
- ✅ Informasi jelas - output yang mudah dibaca dengan warna
- ✅ Cross-platform - bisa dijalankan dari Windows (PowerShell) atau Linux (Bash)

#### Cara 4: Deployment dengan Git Pull (Manual)

Cara ini lebih efisien karena hanya download perubahan saja. Setup sekali, kemudian cukup `git pull` setiap update.

**Setup Awal (Sekali Saja):**

```bash
# SSH ke server
ssh root@72.61.142.109

# Install Git (jika belum ada)
apt update
apt install -y git

# Clone repository ke directory deployment
cd /opt

# Hapus folder lama jika sudah ada (backup dulu jika perlu)
rm -rf ksm-main-dev

# Clone repository ke folder sementara
git clone https://github.com/irmanshidayat/ksm-main.git ksm-main-dev-temp
cd ksm-main-dev-temp
git checkout dev

# Setup Git config (opsional)
git config --global user.name "Server Deploy"
git config --global user.email "deploy@ksm.local"

# Buat directory deployment dan pindahkan semua isi repository ke sana
mkdir -p /opt/ksm-main-dev

# Pindahkan semua file dan folder (termasuk hidden files seperti .git)
# Gunakan find untuk menghindari masalah dengan . dan ..
find . -maxdepth 1 -not -name '.' -not -name '..' -exec mv {} /opt/ksm-main-dev/ \;

# Atau alternatif: gunakan rsync untuk memindahkan semua file
# rsync -av --exclude='.' --exclude='..' . /opt/ksm-main-dev/

# Hapus folder temporary
cd /opt
rmdir ksm-main-dev-temp 2>/dev/null || rm -rf ksm-main-dev-temp

# Masuk ke directory deployment
cd /opt/ksm-main-dev

# Verifikasi file docker-compose.dev.yml ada
if [ ! -f "docker-compose.dev.yml" ]; then
    echo "❌ ERROR: docker-compose.dev.yml tidak ditemukan!"
    echo "Struktur direktori saat ini:"
    ls -la
    exit 1
fi

# Copy docker-compose file ke root (untuk kemudahan)
cp docker-compose.dev.yml docker-compose.yml
echo "✅ docker-compose.yml sudah dibuat dari docker-compose.dev.yml"

# Copy Agent AI jika ada (dari parent directory)
if [ -d "/opt/Agent AI" ]; then
    echo "Agent AI folder sudah ada di /opt/"
else
    # Jika Agent AI ada di repository, copy ke /opt
    if [ -d "../Agent AI" ]; then
        cp -r "../Agent AI" /opt/
    fi
fi

# Verifikasi struktur direktori
echo "Verifikasi struktur direktori:"
ls -la
echo ""
echo "Harus ada: backend, frontend-vite, infrastructure, docker-compose.yml, docker-compose.dev.yml"
```

**Alternatif Setup (Clone Langsung - RECOMMENDED):**

Cara ini lebih sederhana dan direkomendasikan. Clone langsung ke target directory:

```bash
# SSH ke server
ssh root@72.61.142.109

# Install Git (jika belum ada)
apt update
apt install -y git

# Clone repository langsung ke target directory
cd /opt
rm -rf ksm-main-dev
git clone https://github.com/irmanshidayat/ksm-main.git ksm-main-dev
cd ksm-main-dev
git checkout dev

# Setup Git config (opsional)
git config --global user.name "Server Deploy"
git config --global user.email "deploy@ksm.local"

# Verifikasi file docker-compose.dev.yml ada
if [ ! -f "docker-compose.dev.yml" ]; then
    echo "❌ ERROR: docker-compose.dev.yml tidak ditemukan!"
    echo "Struktur direktori saat ini:"
    ls -la
    exit 1
fi

# Copy docker-compose file ke root
cp docker-compose.dev.yml docker-compose.yml
echo "✅ docker-compose.yml sudah dibuat"

# Verifikasi struktur direktori
echo ""
echo "📁 Verifikasi struktur direktori:"
ls -la | head -20
echo ""
echo "Harus ada: backend, frontend-vite, infrastructure, docker-compose.yml, docker-compose.dev.yml, .git"
```

**Catatan Penting:**
- Dengan cara ini, struktur direktori sudah benar dari awal
- Folder `.git` akan ada di `/opt/ksm-main-dev/.git` sehingga `git pull` bisa langsung digunakan
- Tidak perlu memindahkan file karena sudah di tempat yang benar

**PENTING - Perbaiki Struktur Direktori yang Salah:**

Jika setelah clone struktur direktori menjadi `/opt/ksm-main-dev/ksm-main-dev/` (ada subdirectory), perbaiki dengan:

```bash
# Masuk ke directory deployment
cd /opt/ksm-main-dev

# Jika ada subdirectory ksm-main-dev, pindahkan semua isinya ke parent
if [ -d "ksm-main-dev" ]; then
    echo "⚠️  Memperbaiki struktur direktori yang salah..."
    
    # Masuk ke subdirectory
    cd ksm-main-dev
    
    # Pindahkan semua file dan folder menggunakan find (lebih aman)
    find . -maxdepth 1 -not -name '.' -not -name '..' -exec mv {} .. \;
    
    # Kembali ke parent directory
    cd ..
    
    # Hapus subdirectory kosong
    rmdir ksm-main-dev 2>/dev/null || rm -rf ksm-main-dev
    
    # Verifikasi struktur
    echo "✅ Struktur direktori sudah diperbaiki"
    echo "📁 Verifikasi struktur:"
    ls -la | head -20
    echo ""
    echo "Harus ada: backend, frontend-vite, infrastructure, docker-compose.dev.yml, .git"
    
    # Verifikasi file penting ada
    if [ ! -f "docker-compose.dev.yml" ]; then
        echo "❌ ERROR: docker-compose.dev.yml masih tidak ditemukan!"
        exit 1
    fi
    
    # Copy docker-compose file jika belum ada
    if [ ! -f "docker-compose.yml" ]; then
        cp docker-compose.dev.yml docker-compose.yml
        echo "✅ docker-compose.yml sudah dibuat"
    fi
fi
```

**Deployment Setiap Update:**

```bash
# SSH ke server
ssh root@72.61.142.109

# Masuk ke directory deployment
cd /opt/ksm-main-dev

# Pull latest changes dari repository
git pull origin dev

# Perbaiki struktur direktori jika ada subdirectory (lihat bagian "PENTING" di atas)
# Ini penting jika struktur direktori menjadi salah setelah clone
if [ -d "ksm-main-dev" ]; then
    echo "⚠️  Memperbaiki struktur direktori yang salah..."
    # Masuk ke subdirectory
    cd ksm-main-dev
    # Pindahkan semua file dan folder menggunakan find (lebih aman)
    find . -maxdepth 1 -not -name '.' -not -name '..' -exec mv {} .. \;
    # Kembali ke parent directory
    cd ..
    # Hapus subdirectory kosong
    rmdir ksm-main-dev 2>/dev/null || rm -rf ksm-main-dev
    echo "✅ Struktur direktori sudah diperbaiki"
fi

# Update docker-compose.yml dari docker-compose.dev.yml
if [ -f "docker-compose.dev.yml" ]; then
    cp docker-compose.dev.yml docker-compose.yml
    echo "✅ docker-compose.yml sudah diupdate"
fi

# Verifikasi struktur direktori sebelum build
echo ""
echo "📁 Verifikasi struktur direktori:"
ls -la | grep -E "(backend|frontend-vite|infrastructure|docker-compose)"
echo ""

# Pastikan semua folder yang diperlukan ada
if [ ! -d "backend" ] || [ ! -d "frontend-vite" ] || [ ! -d "infrastructure" ]; then
    echo "❌ ERROR: Folder backend, frontend-vite, atau infrastructure tidak ditemukan!"
    echo "Pastikan struktur direktori benar sebelum melanjutkan."
    exit 1
fi

# Stop container yang ada
echo "🛑 Menghentikan container yang ada..."
docker-compose -f docker-compose.yml down || true

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.yml build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.yml up -d

# Tunggu beberapa detik untuk services start
echo "⏳ Menunggu services start (30 detik)..."
sleep 30

# Cek status
echo ""
echo "📊 Status container:"
docker-compose -f docker-compose.yml ps

# Test health endpoints
echo ""
echo "🏥 Testing health endpoints..."
echo "Backend:"
curl -s http://localhost:8002/api/health || echo "❌ Backend tidak merespon"
echo ""
echo "Agent AI:"
curl -s http://localhost:5002/health || echo "❌ Agent AI tidak merespon"
echo ""
echo "Frontend:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:3006 || echo "❌ Frontend tidak merespon"
```

**Keuntungan Menggunakan Git Pull:**
- ✅ Lebih cepat - hanya download perubahan
- ✅ Otomatis - tidak perlu copy manual
- ✅ Version control - bisa rollback jika perlu
- ✅ Clean - tidak ada file cache yang tidak perlu
- ✅ Mudah - cukup `git pull` saja

**Catatan:**
- Untuk production, clone ke `/opt/ksm-main-prod` dan checkout branch `main`
- Pastikan file `.env` tidak di-commit, simpan terpisah di server
- Jika repository private, setup SSH key atau gunakan Personal Access Token

#### Cara 4: Manual Copy Files (Tanpa Script)

Jika script tidak bisa digunakan, copy files secara manual:

**Dari PowerShell Windows (root project):**

```powershell
# 1. Copy docker-compose file
scp -P 22 ksm-main/docker-compose.dev.yml root@72.61.142.109:/opt/ksm-main-dev/docker-compose.yml

# 2. Buat directory infrastructure
ssh root@72.61.142.109 "mkdir -p /opt/ksm-main-dev/infrastructure"

# 3. Copy infrastructure files
scp -P 22 -r ksm-main/infrastructure/* root@72.61.142.109:/opt/ksm-main-dev/infrastructure/

# 4. Copy backend files
scp -P 22 -r ksm-main/backend root@72.61.142.109:/opt/ksm-main-dev/

# 5. Copy frontend files
scp -P 22 -r ksm-main/frontend-vite root@72.61.142.109:/opt/ksm-main-dev/

# 6. Copy Agent AI files
scp -P 22 -r "Agent AI" root@72.61.142.109:/opt/
```

**Catatan Penting:**
- `scp` akan copy semua file termasuk cache (__pycache__, node_modules, dll)
- Setelah copy, cleanup cache files di server jika diperlukan
- Untuk production, ganti `docker-compose.dev.yml` dengan `docker-compose.yml` dan path `/opt/ksm-main-dev` dengan `/opt/ksm-main-prod`

**Cleanup cache files di server (opsional):**

```bash
# Di server, setelah copy files
cd /opt/ksm-main-dev

# Hapus Python cache
find backend -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find backend -name "*.pyc" -delete

# Hapus node_modules (akan diinstall ulang saat build)
rm -rf frontend-vite/node_modules
```

## Server Setup

### Initial Server Setup

1. **Install Docker & Docker Compose**

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Create Deployment Directory**

```bash
# Development
sudo mkdir -p /opt/ksm-main-dev
sudo chown -R $USER:$USER /opt/ksm-main-dev

# Production
sudo mkdir -p /opt/ksm-main-prod
sudo chown -R $USER:$USER /opt/ksm-main-prod
```

3. **Setup Environment File**

```bash
# Development
cd /opt/ksm-main-dev
cp env.dev.example .env
# Edit .env sesuai kebutuhan

# Production
cd /opt/ksm-main-prod
cp env.example .env
# Edit .env sesuai kebutuhan
```

4. **Create Logs Directory**

```bash
# Development
mkdir -p /opt/ksm-main-dev/logs/{mysql-dev,nginx-dev,redis-dev}

# Production
mkdir -p /opt/ksm-main-prod/logs/{mysql,nginx,redis}
```

## Helper Scripts

Gunakan helper scripts untuk maintenance:

### Linux/Mac

```bash
# Check status
./scripts/deploy-helper.sh status dev

# View logs
./scripts/deploy-helper.sh logs dev
./scripts/deploy-helper.sh logs dev ksm-backend-dev

# Restart services
./scripts/deploy-helper.sh restart dev

# Health check
./scripts/deploy-helper.sh health dev

# Stop services
./scripts/deploy-helper.sh stop dev

# Build images
./scripts/deploy-helper.sh build dev
```

### Windows

```powershell
# Check status
.\scripts\deploy-helper.bat status dev

# View logs
.\scripts\deploy-helper.bat logs dev
.\scripts\deploy-helper.bat logs dev ksm-backend-dev

# Restart services
.\scripts\deploy-helper.bat restart dev

# Health check
.\scripts\deploy-helper.bat health dev

# Test SSH connection (dengan port 22)
.\scripts\ssh-test.ps1
.\scripts\ssh-test.ps1 72.61.142.109 root

# Manual deployment
.\scripts\manual-deploy.ps1
.\scripts\manual-deploy.ps1 -Environment dev
.\scripts\manual-deploy.ps1 -Environment prod
```

## Troubleshooting

### Deployment Failed

1. **Check GitHub Actions logs**
   - Buka Actions tab di GitHub
   - Lihat log dari failed workflow
   - Cari error message

2. **Check server logs**
   ```bash
   cd /opt/ksm-main-dev  # atau /opt/ksm-main-prod
   docker-compose -f docker-compose.yml logs --tail=100
   ```

3. **Check service status**
   ```bash
   docker-compose -f docker-compose.yml ps
   ```

### Services Not Starting

1. **Check Docker resources**
   ```bash
   docker system df
   docker ps -a
   ```

2. **Check disk space**
   ```bash
   df -h
   ```

3. **Check Docker logs**
   ```bash
   docker-compose -f docker-compose.yml logs [service-name]
   ```

### Docker Build Error: "unable to prepare context: path not found"

Error ini terjadi ketika Docker tidak bisa menemukan folder `backend` atau `frontend-vite` di lokasi yang diharapkan oleh `docker-compose.yml`.

**Gejala:**
```
unable to prepare context: path "/opt/ksm-main-dev/backend" not found
unable to prepare context: path "/opt/ksm-main-dev/frontend-vite" not found
```

**Penyebab:**
- Struktur direktori tidak sesuai dengan yang diharapkan docker-compose.yml
- Folder `backend` dan `frontend-vite` ada di subdirectory (misalnya `/opt/ksm-main-dev/ksm-main-dev/`)
- File-file belum di-copy ke root deployment directory

**Solusi:**

1. **Cek struktur direktori saat ini:**
   ```bash
   cd /opt/ksm-main-dev
   ls -la
   # Periksa apakah ada folder backend, frontend-vite di root
   ```

2. **Jika ada subdirectory, perbaiki struktur:**
   ```bash
   cd /opt/ksm-main-dev
   
   # Jika ada subdirectory ksm-main-dev, pindahkan isinya
   if [ -d "ksm-main-dev" ]; then
       echo "⚠️  Memperbaiki struktur direktori..."
       # Masuk ke subdirectory
       cd ksm-main-dev
       # Pindahkan semua file dan folder menggunakan find (lebih aman)
       find . -maxdepth 1 -not -name '.' -not -name '..' -exec mv {} .. \;
       # Kembali ke parent directory
       cd ..
       # Hapus subdirectory kosong
       rmdir ksm-main-dev 2>/dev/null || rm -rf ksm-main-dev
       echo "✅ Struktur direktori sudah diperbaiki"
   fi
   
   # Verifikasi file docker-compose.dev.yml ada
   if [ ! -f "docker-compose.dev.yml" ]; then
       echo "❌ ERROR: docker-compose.dev.yml tidak ditemukan!"
       echo "Struktur direktori saat ini:"
       ls -la
       exit 1
   fi
   
   # Copy docker-compose file jika belum ada
   if [ ! -f "docker-compose.yml" ]; then
       cp docker-compose.dev.yml docker-compose.yml
       echo "✅ docker-compose.yml sudah dibuat"
   fi
   
   # Verifikasi struktur
   echo "📁 Verifikasi struktur direktori:"
   ls -la | head -20
   echo ""
   echo "Harus ada: backend, frontend-vite, infrastructure, docker-compose.yml, docker-compose.dev.yml"
   ```

3. **Jika struktur sudah benar tapi masih error, cek docker-compose.yml:**
   ```bash
   cd /opt/ksm-main-dev
   cat docker-compose.yml | grep -A 3 "context:"
   # Pastikan context paths benar: ./backend dan ./frontend-vite
   ```

4. **Setelah perbaikan, rebuild:**
   ```bash
   docker-compose -f docker-compose.yml down || true
   docker-compose -f docker-compose.yml build --no-cache
   docker-compose -f docker-compose.yml up -d
   ```

### SSH Connection Issues

**PENTING**: VPS menggunakan port SSH **22** (port default).

#### Error: "Permission denied (publickey,password)"

Error ini terjadi ketika SSH authentication gagal. Berikut langkah-langkah untuk memperbaikinya:

**1. Pastikan SSH Key Sudah Di-Generate**

```bash
# Generate SSH key pair (jika belum ada)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# Jangan set passphrase (tekan Enter kosong) untuk GitHub Actions
```

**2. Copy Public Key ke Server**

**Cara Otomatis (Recommended):**
```bash
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub -p 22 root@72.61.142.109
```

**Cara Manual (jika ssh-copy-id tidak tersedia):**
```bash
# Copy public key ke server
cat ~/.ssh/github_actions_deploy.pub | ssh -p 22 root@72.61.142.109 \
  "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

**3. Test SSH Connection Manual**

```bash
# Test dengan SSH key
ssh -p 22 -i ~/.ssh/github_actions_deploy root@72.61.142.109

# Jika berhasil, Anda akan masuk ke server tanpa password
# Jika masih gagal, lanjut ke step berikutnya
```

**4. Copy Private Key ke GitHub Secrets**

```bash
# Tampilkan private key
cat ~/.ssh/github_actions_deploy

# Copy SEMUA output termasuk header dan footer:
# -----BEGIN OPENSSH PRIVATE KEY-----
# ...
# -----END OPENSSH PRIVATE KEY-----
```

**PENTING**: 
- Copy **SEMUA** isi file, termasuk header `-----BEGIN OPENSSH PRIVATE KEY-----` dan footer `-----END OPENSSH PRIVATE KEY-----`
- Jangan ada spasi atau karakter tambahan di awal/akhir
- Pastikan tidak ada line break yang hilang

**5. Verify Server SSH Configuration**

SSH ke server dan periksa konfigurasi:

```bash
# SSH ke server (gunakan password jika masih belum bisa key-based)
ssh root@72.61.142.109

# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Pastikan setting berikut ada dan tidak di-comment:
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication yes  # Bisa di-set no setelah key-based auth bekerja

# Restart SSH service
sudo systemctl restart sshd

# Verifikasi authorized_keys file
cat ~/.ssh/authorized_keys
# Harus ada public key yang sesuai dengan private key Anda
```

**6. Verify File Permissions di Server**

```bash
# Di server, pastikan permission benar:
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Verify ownership
ls -la ~/.ssh/
# Harus owned by user yang digunakan (root atau user lain)
```

**7. Test Connection dari GitHub Actions**

Setelah semua setup selesai, workflow akan otomatis test SSH connection. Jika masih gagal, cek log GitHub Actions untuk detail error.

#### Troubleshooting Lainnya

**Connection Timeout:**
```bash
# Test konektivitas
ping 72.61.142.109

# Test port SSH
telnet 72.61.142.109 22
# atau
nc -zv 72.61.142.109 22

# Pastikan firewall tidak memblokir port 22
```

**SSH Key Format Error:**
- Pastikan private key di GitHub Secrets lengkap dengan header/footer
- Format: `-----BEGIN OPENSSH PRIVATE KEY----- ... -----END OPENSSH PRIVATE KEY-----`
- Tidak ada spasi tambahan di awal/akhir
- Semua line break harus ada

**Key Mismatch:**
- Pastikan public key di server (`~/.ssh/authorized_keys`) match dengan private key di GitHub Secrets
- Generate ulang key pair jika perlu dan copy public key ke server lagi

## SSL/HTTPS Setup dengan Let's Encrypt

Proyek ini menggunakan Let's Encrypt untuk SSL/HTTPS certificates. Setup otomatis sudah tersedia untuk production dan development.

### Prerequisites

1. **Domain sudah pointing ke server IP**
   - Production: `report.ptkiansantang.com` → Server IP
   - Development: `devreport.ptkiansantang.com` → Server IP

2. **Port 80 dan 443 terbuka di firewall**
   - Let's Encrypt memerlukan akses ke port 80 untuk validation
   - Port 443 untuk HTTPS

3. **SSH access ke server** sudah dikonfigurasi

### Setup SSL Certificate

#### Cara 1: Menggunakan Script Otomatis (Recommended)

**Dari Windows PowerShell:**

```powershell
# Setup SSL untuk development
.\scripts\setup-ssl.ps1 -Environment dev -Email "your-email@example.com"

# Setup SSL untuk production
.\scripts\setup-ssl.ps1 -Environment prod -Email "your-email@example.com"
```

**Dari Server Linux (SSH):**

```bash
# SSH ke server
ssh root@72.61.142.109

# Masuk ke directory deployment
cd /opt/ksm-main-dev  # atau /opt/ksm-main-prod untuk production

# Buat script executable
chmod +x scripts/setup-ssl.sh

# Jalankan setup SSL
./scripts/setup-ssl.sh dev your-email@example.com
# atau untuk production
./scripts/setup-ssl.sh prod your-email@example.com
```

#### Cara 2: Manual Setup dengan Certbot

```bash
# SSH ke server
ssh root@72.61.142.109

# Install Certbot
apt update
apt install -y certbot python3-certbot-nginx

# Generate certificate untuk development
certbot certonly --standalone \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d devreport.ptkiansantang.com

# Generate certificate untuk production
certbot certonly --standalone \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d report.ptkiansantang.com

# Copy certificates ke deployment directory
# Development
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/fullchain.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/privkey.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/key.pem

# Production
cp /etc/letsencrypt/live/report.ptkiansantang.com/fullchain.pem /opt/ksm-main-prod/infrastructure/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/report.ptkiansantang.com/privkey.pem /opt/ksm-main-prod/infrastructure/nginx/ssl/key.pem

# Set permissions
chmod 644 /opt/ksm-main-*/infrastructure/nginx/ssl/cert.pem
chmod 600 /opt/ksm-main-*/infrastructure/nginx/ssl/key.pem

# Restart nginx container
cd /opt/ksm-main-dev  # atau /opt/ksm-main-prod
docker-compose restart nginx-dev  # atau nginx-prod
```

### Auto-Renewal

Script setup SSL otomatis mengatur auto-renewal untuk certificates. Certificates akan diperbarui otomatis setiap 12 jam melalui cron job.

**Manual Renewal (jika diperlukan):**

```bash
# SSH ke server
ssh root@72.61.142.109

# Renew certificate
certbot renew

# Copy renewed certificates
# Development
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/fullchain.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/privkey.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/key.pem

# Production
cp /etc/letsencrypt/live/report.ptkiansantang.com/fullchain.pem /opt/ksm-main-prod/infrastructure/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/report.ptkiansantang.com/privkey.pem /opt/ksm-main-prod/infrastructure/nginx/ssl/key.pem

# Reload nginx
cd /opt/ksm-main-dev  # atau /opt/ksm-main-prod
docker-compose exec nginx-dev nginx -s reload  # atau nginx-prod
```

**Cek Status Auto-Renewal:**

```bash
# Cek cron job
crontab -l | grep ksm-ssl-renew

# Cek log renewal
tail -f /var/log/ksm-ssl-renew.log
```

### Verifikasi SSL

Setelah setup SSL, verifikasi dengan:

```bash
# Test SSL connection
curl -I https://devreport.ptkiansantang.com  # development
curl -I https://report.ptkiansantang.com      # production

# Test SSL certificate details
openssl s_client -connect devreport.ptkiansantang.com:443 -servername devreport.ptkiansantang.com
openssl s_client -connect report.ptkiansantang.com:443 -servername report.ptkiansantang.com

# Test dari browser
# Buka: https://devreport.ptkiansantang.com atau https://report.ptkiansantang.com
```

### Troubleshooting SSL

**Error: "Domain not pointing to server"**
- Pastikan DNS A record sudah pointing ke server IP
- Test dengan: `nslookup devreport.ptkiansantang.com` atau `dig devreport.ptkiansantang.com`

**Error: "Port 80 blocked"**
- Pastikan port 80 terbuka di firewall
- Test dengan: `telnet your-server-ip 80`

**Error: "Certificate not found"**
- Pastikan certificates sudah di-copy ke `/opt/ksm-main-{env}/infrastructure/nginx/ssl/`
- Cek dengan: `ls -la /opt/ksm-main-dev/infrastructure/nginx/ssl/`

**Error: "Nginx SSL configuration error"**
- Pastikan nginx config sudah di-update untuk menggunakan Let's Encrypt certificates
- Test nginx config: `docker-compose exec nginx-dev nginx -t`

**Certificate Expired**
- Auto-renewal seharusnya memperbarui otomatis
- Manual renewal: `certbot renew --force-renewal`

## Monitoring

### Health Checks

Setiap service memiliki health check endpoint:

- **Backend**: `http://localhost:8001/api/health` (prod) atau `http://localhost:8002/api/health` (dev)
- **Agent AI**: `http://localhost:5001/health` (prod) atau `http://localhost:5002/health` (dev)
- **Frontend**: `http://localhost:3005` (prod) atau `http://localhost:3006` (dev)

### Logs Location

- **Application logs**: `/opt/ksm-main-{env}/logs/`
- **Docker logs**: `docker-compose logs [service-name]`
- **System logs**: `/var/log/`

## Rollback

Jika deployment gagal, rollback ke versi sebelumnya:

```bash
cd /opt/ksm-main-prod  # atau dev
git checkout [previous-commit-hash]
docker-compose -f docker-compose.yml up -d --build
```

## Best Practices

1. **Always test di development** sebelum deploy ke production
2. **Monitor deployment** setelah push ke branch
3. **Keep .env files secure** - jangan commit ke repository
4. **Regular backups** database dan volumes
5. **Monitor disk space** - cleanup old images regularly
6. **Use health checks** untuk verify deployment success

## Support

Jika ada masalah dengan deployment:

1. Check GitHub Actions logs
2. Check server logs menggunakan helper scripts
3. Verify server resources (disk, memory, CPU)
4. Check network connectivity
5. Verify environment variables di .env file

