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

Tambahkan secrets berikut di GitHub Repository Settings → Secrets and variables → Actions:

#### Development Secrets

- `SSH_HOST_DEV`: IP atau hostname server development (contoh: `72.61.142.109`) ssh root@72.61.142.109 -p 22
- `SSH_USER_DEV`: Username SSH untuk development (contoh: `root`)
- `SSH_KEY_DEV`: Private SSH key untuk development (full key dengan header/footer)
- `DEPLOY_PATH_DEV`: Path deployment di server (default: `/opt/ksm-main-dev`)

#### Production Secrets

- `SSH_HOST_PROD`: IP atau hostname server production (contoh: `72.61.142.109`)
- `SSH_USER_PROD`: Username SSH untuk production (contoh: `root`)
- `SSH_KEY_PROD`: Private SSH key untuk production (full key dengan header/footer)
- `DEPLOY_PATH_PROD`: Path deployment di server (default: `/opt/ksm-main-prod`)

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

#### Cara 3: Manual Copy Files (Tanpa Script)

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

### SSH Connection Issues

**PENTING**: VPS menggunakan port SSH **22** (port default).

1. **Test SSH connection**
   ```bash
   # Gunakan port 22 (default, flag -p 22 opsional)
   ssh -p 22 -i ~/.ssh/github_actions_deploy user@server
   
   # Atau untuk manual connection (port 22 adalah default)
   ssh root@72.61.142.109
   # atau
   ssh -p 22 root@72.61.142.109
   ```

2. **Check SSH key format**
   - Pastikan private key di GitHub Secrets lengkap dengan header/footer
   - Format: `-----BEGIN OPENSSH PRIVATE KEY----- ... -----END OPENSSH PRIVATE KEY-----`

3. **Check server SSH config**
   ```bash
   # Di server
   sudo nano /etc/ssh/sshd_config
   # Pastikan: 
   #   - Port 22
   #   - PubkeyAuthentication yes
   ```

4. **Troubleshooting Connection Timeout**
   - Pastikan firewall tidak memblokir port 22
   - Test konektivitas: `ping 72.61.142.109`
   - Test port: `telnet 72.61.142.109 22` atau `nc -zv 72.61.142.109 22`

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

