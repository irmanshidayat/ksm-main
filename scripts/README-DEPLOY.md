# KSM Main - Deployment Scripts

Script otomatis untuk deployment KSM Main ke server.

## Script yang Tersedia

### 1. `deploy-setup.sh` - Setup Awal
Script untuk setup awal deployment di server.

**Usage:**
```bash
./scripts/deploy-setup.sh [dev|prod]
```

**Fitur:**
- Install Git (jika belum ada)
- Clone repository
- Setup Git config
- Verifikasi struktur direktori
- Buat docker-compose.yml
- Buat logs directory

### 2. `deploy-update.sh` - Deployment Update
Script untuk deployment update setiap kali ada perubahan.

**Usage:**
```bash
./scripts/deploy-update.sh [dev|prod]
```

**Fitur:**
- Pull latest changes dari repository
- Perbaiki struktur direktori jika perlu
- Update docker-compose.yml
- Build Docker images
- Start services
- Health check otomatis

### 3. `deploy-auto.ps1` - PowerShell Wrapper (Windows)
Script PowerShell untuk menjalankan deployment dari Windows.

**Usage:**
```powershell
# Setup awal
.\scripts\deploy-auto.ps1 -Environment dev -Action setup

# Deployment update
.\scripts\deploy-auto.ps1 -Environment dev -Action update
```

**Catatan:** Script ini akan meminta password SSH jika SSH key belum dikonfigurasi.

## Cara Menggunakan

### Opsi 1: Dari Windows PowerShell (Mudah)

```powershell
# Masuk ke root project
cd "C:\Irman\Coding KSM Main\KSM Grup - dev"

# Deployment update untuk development
.\scripts\deploy-auto.ps1 -Environment dev -Action update
```

**Catatan:** Akan meminta password SSH saat pertama kali.

### Opsi 2: Dari Server Linux (SSH Manual)

```bash
# 1. SSH ke server
ssh root@72.61.142.109

# 2. Clone repository (jika belum ada)
cd /opt
git clone https://github.com/irmanshidayat/ksm-main.git ksm-main-dev
cd ksm-main-dev
git checkout dev

# 3. Buat script executable
chmod +x scripts/deploy-setup.sh
chmod +x scripts/deploy-update.sh

# 4. Setup awal (sekali saja)
./scripts/deploy-setup.sh dev

# 5. Deployment update (setiap kali ada perubahan)
./scripts/deploy-update.sh dev
```

### Opsi 3: Quick Deploy (Jika Sudah SSH)

Jika sudah SSH ke server dan directory sudah ada:

```bash
cd /opt/ksm-main-dev
git pull origin dev
chmod +x scripts/deploy-update.sh
./scripts/deploy-update.sh dev
```

## Troubleshooting

### SSH Connection Failed
- Pastikan SSH key sudah dikonfigurasi, atau
- Gunakan opsi 2 (SSH manual) dan jalankan script langsung di server

### Permission Denied
```bash
chmod +x scripts/deploy-setup.sh
chmod +x scripts/deploy-update.sh
```

### Directory Already Exists
Script akan menanyakan apakah ingin menghapus dan clone ulang, atau gunakan:
```bash
rm -rf /opt/ksm-main-dev
# Lalu jalankan setup lagi
```

## Environment Variables

Script menggunakan environment default:
- **Development**: `/opt/ksm-main-dev`, branch `dev`, port `8002/5002/3006`
- **Production**: `/opt/ksm-main-prod`, branch `main`, port `8001/5001/3005`

## Support

Untuk masalah lebih lanjut, lihat dokumentasi lengkap di `.github/DEPLOYMENT.md`

