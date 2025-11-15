# 🔐 KSM Main - SSL Certificate Fix Guide

## Masalah: NET::ERR_CERT_COMMON_NAME_INVALID

Error ini terjadi ketika SSL certificate tidak valid atau tidak cocok dengan domain.

## Solusi Cepat

### 1. Check SSL Certificate Status

```bash
# SSH ke server
ssh user@vps-ip

# Masuk ke directory deployment
cd /opt/ksm-main-dev

# Check SSL certificate
./scripts/check-ssl.sh dev
```

### 2. Fix SSL Certificate

Jika certificate tidak ada atau tidak valid:

```bash
# Setup SSL certificate dengan Let's Encrypt
./scripts/setup-ssl.sh dev your-email@example.com
```

**Catatan:** Ganti `your-email@example.com` dengan email Anda yang valid.

### 3. Setup Nginx Host Reverse Proxy (jika port 443 digunakan oleh nginx host lain)

Jika port 443 di host sudah digunakan oleh nginx host untuk domain lain (misalnya `jargas.ptkiansantang.com`), setup reverse proxy:

```bash
# SSH ke server
ssh user@vps-ip

# Masuk ke directory deployment
cd /opt/ksm-main-dev

# Setup reverse proxy di nginx host
sudo ./scripts/setup-nginx-host-proxy.sh dev
```

Script ini akan:
- Membuat konfigurasi nginx host untuk `devreport.ptkiansantang.com`
- Setup reverse proxy dari port 443 ke container di port 8445
- Menggunakan SSL certificate yang sudah ada di deployment directory

**Catatan:**
- Container nginx menggunakan port `8445:443` (bukan 443 langsung)
- Nginx host akan reverse proxy ke container di port 8445
- Domain `jargas.ptkiansantang.com` tetap menggunakan port 443 langsung

### 4. Fix Certificate Chain (jika masih error)

Jika certificate sudah ditemukan tapi masih error `NET::ERR_CERT_COMMON_NAME_INVALID`:

```bash
# Copy fullchain dari Let's Encrypt
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/fullchain.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/privkey.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/key.pem

# Restart nginx
cd /opt/ksm-main-dev
docker-compose restart nginx-dev

# Reload nginx host (jika menggunakan reverse proxy)
sudo systemctl reload nginx
```

### 5. Restart Nginx Container

```bash
cd /opt/ksm-main-dev
docker-compose restart nginx-dev

# Jika menggunakan reverse proxy di nginx host, reload juga:
sudo systemctl reload nginx
```

## Troubleshooting

### Certificate tidak ada

**Gejala:** File `cert.pem` atau `key.pem` tidak ditemukan

**Solusi:**
```bash
cd /opt/ksm-main-dev
./scripts/setup-ssl.sh dev your-email@example.com
```

### Certificate tidak cocok dengan domain

**Gejala:** Certificate untuk domain lain (misalnya `report.ptkiansantang.com` bukan `devreport.ptkiansantang.com`)

**Solusi:**
```bash
# Hapus certificate lama
rm -rf /opt/ksm-main-dev/infrastructure/nginx/ssl/*

# Generate certificate baru
./scripts/setup-ssl.sh dev your-email@example.com
```

### Certificate expired

**Gejala:** Certificate sudah expired

**Solusi:**
```bash
# Renew certificate
certbot renew

# Copy certificate baru
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/fullchain.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/privkey.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/key.pem

# Restart nginx
cd /opt/ksm-main-dev
docker-compose restart nginx-dev
```

### Certificate chain tidak lengkap (NET::ERR_CERT_COMMON_NAME_INVALID)

**Gejala:** 
- Browser menampilkan error `NET::ERR_CERT_COMMON_NAME_INVALID`
- SSL certificate sudah ditemukan dan valid
- Domain sudah benar
- Tapi web masih tidak bisa diakses

**Penyebab:**
Certificate chain tidak lengkap. Let's Encrypt memerlukan **fullchain** (certificate + intermediate chain), bukan hanya certificate saja. Jika `cert.pem` hanya berisi 1 certificate, browser tidak bisa memverifikasi chain of trust.

**Solusi Cepat:**
```bash
# SSH ke server
ssh user@vps-ip

# Masuk ke directory deployment
cd /opt/ksm-main-dev

# Check certificate chain
./scripts/check-ssl.sh dev

# Jika certificate chain tidak lengkap, perbaiki:
# 1. Copy fullchain dari Let's Encrypt
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/fullchain.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/devreport.ptkiansantang.com/privkey.pem /opt/ksm-main-dev/infrastructure/nginx/ssl/key.pem

# 2. Set permissions
chmod 644 /opt/ksm-main-dev/infrastructure/nginx/ssl/cert.pem
chmod 600 /opt/ksm-main-dev/infrastructure/nginx/ssl/key.pem

# 3. Restart nginx container
docker-compose restart nginx-dev

# 4. Verify
./scripts/check-ssl.sh dev
```

**Verifikasi Certificate Chain:**
```bash
# Check berapa banyak certificate di file
grep -c "BEGIN CERTIFICATE" /opt/ksm-main-dev/infrastructure/nginx/ssl/cert.pem

# Harusnya minimal 2 (certificate + intermediate)
# Jika hanya 1, berarti chain tidak lengkap
```

**Catatan Penting:**
- Pastikan menggunakan `fullchain.pem` bukan `cert.pem` dari Let's Encrypt
- Fullchain berisi: domain certificate + intermediate certificate(s)
- Browser memerlukan fullchain untuk memverifikasi chain of trust

### Domain belum pointing ke server

**Gejala:** Let's Encrypt tidak bisa verify domain

**Solusi:**
1. Pastikan DNS A record untuk `devreport.ptkiansantang.com` sudah pointing ke IP server
2. Test dengan: `nslookup devreport.ptkiansantang.com` atau `dig devreport.ptkiansantang.com`
3. Tunggu beberapa menit untuk DNS propagation
4. Coba setup SSL lagi

### Port 80 digunakan project lain

**Gejala:** Port 80 sudah digunakan oleh project lain, script setup SSL gagal

**Solusi (Webroot Method - Recommended):**
Script `setup-ssl.sh` sekarang otomatis menggunakan **webroot method** yang tidak perlu stop service di port 80.

1. **Pastikan nginx container KSM berjalan:**
   ```bash
   cd /opt/ksm-main-dev
   docker-compose up -d nginx-dev
   ```

2. **Pastikan nginx sudah dikonfigurasi untuk webroot:**
   - Nginx config sudah include location `/.well-known/acme-challenge/` (sudah ada di `nginx.dev.conf`)
   - Jika belum, pastikan ada di config:
     ```nginx
     location /.well-known/acme-challenge/ {
         root /var/www/certbot;
     }
     ```

3. **Jalankan setup SSL:**
   ```bash
   ./scripts/setup-ssl.sh dev your-email@example.com
   ```
   
   Script akan otomatis:
   - Deteksi apakah nginx berjalan dan dikonfigurasi untuk webroot
   - Gunakan webroot method (tidak perlu stop service lain)
   - Fallback ke standalone method jika webroot tidak tersedia

**Keuntungan Webroot Method:**
- ✅ Tidak perlu stop service di port 80
- ✅ Tidak mengganggu project lain
- ✅ Nginx container tetap berjalan selama proses
- ✅ Lebih aman dan stabil

**Jika Webroot Method Gagal:**
Script akan otomatis fallback ke standalone method, yang memerlukan port 80 bebas. Dalam kasus ini:
1. Hentikan sementara service lain yang menggunakan port 80
2. Atau gunakan DNS-01 challenge (tidak memerlukan port 80)

### Port 80 blocked oleh firewall

**Gejala:** Let's Encrypt tidak bisa verify domain karena port 80 tidak accessible dari internet

**Solusi:**
1. Pastikan port 80 terbuka di firewall
2. Check: `ufw status` atau `iptables -L`
3. Buka port 80: `ufw allow 80/tcp`

## Verifikasi

Setelah fix, verifikasi dengan:

```bash
# Test SSL connection
curl -I https://devreport.ptkiansantang.com

# Check certificate details
openssl s_client -connect devreport.ptkiansantang.com:443 -servername devreport.ptkiansantang.com
```

Atau buka di browser: `https://devreport.ptkiansantang.com`

## Auto-Renewal

Certificate akan auto-renew setiap 12 jam melalui cron job. Check status:

```bash
# Check cron job
crontab -l | grep ksm-ssl-renew

# Check renewal log
tail -f /var/log/ksm-ssl-renew.log
```

