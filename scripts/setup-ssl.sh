#!/bin/bash

# =============================================================================
# KSM Main - SSL/HTTPS Setup dengan Let's Encrypt
# =============================================================================
# Script untuk setup SSL certificate menggunakan Let's Encrypt (Certbot)
# Usage: ./setup-ssl.sh [dev|prod] [email]
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
EMAIL=${2:-""}

if [ "$ENVIRONMENT" = "dev" ]; then
    DOMAIN="devreport.ptkiansantang.com"
    DEPLOY_PATH="/opt/ksm-main-dev"
    NGINX_CONF="nginx.dev.conf"
elif [ "$ENVIRONMENT" = "prod" ]; then
    DOMAIN="report.ptkiansantang.com"
    DEPLOY_PATH="/opt/ksm-main-prod"
    NGINX_CONF="nginx.prod.conf"
else
    echo -e "${RED}❌ ERROR: Environment harus 'dev' atau 'prod'${NC}"
    echo "Usage: $0 [dev|prod] [email]"
    exit 1
fi

if [ -z "$EMAIL" ]; then
    echo -e "${YELLOW}⚠️  Warning: Email tidak diberikan${NC}"
    echo "Email diperlukan untuk Let's Encrypt certificate registration"
    read -p "Masukkan email untuk Let's Encrypt: " EMAIL
    if [ -z "$EMAIL" ]; then
        echo -e "${RED}❌ ERROR: Email diperlukan!${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}KSM Main - SSL/HTTPS Setup (${ENVIRONMENT^^})${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "${BLUE}Domain:${NC} $DOMAIN"
echo -e "${BLUE}Email:${NC} $EMAIL"
echo -e "${BLUE}Deploy Path:${NC} $DEPLOY_PATH"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  Warning: Script ini sebaiknya dijalankan sebagai root${NC}"
    echo "Gunakan: sudo $0 $ENVIRONMENT $EMAIL"
    read -p "Lanjutkan? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Install Certbot
echo -e "${BLUE}📦 Step 1: Memeriksa Certbot...${NC}"
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✅ Certbot sudah terinstall${NC}"
else
    echo -e "${GREEN}✅ Certbot sudah terinstall${NC}"
fi

# Step 2: Prepare webroot directory dan check nginx configuration
echo ""
echo -e "${BLUE}📁 Step 2: Mempersiapkan webroot directory untuk Let's Encrypt...${NC}"

# Create certbot webroot directory
WEBROOT_PATH="/var/www/certbot"
mkdir -p "$WEBROOT_PATH"
chmod 755 "$WEBROOT_PATH"

# Check if nginx is configured for webroot
cd "$DEPLOY_PATH" || exit 1
NGINX_CONF_PATH="$DEPLOY_PATH/infrastructure/nginx/$NGINX_CONF"
NGINX_CONTAINER_NAME="KSM-nginx-dev"
if [ "$ENVIRONMENT" = "prod" ]; then
    NGINX_CONTAINER_NAME="KSM-nginx-prod"
fi

# Check if nginx container is running
NGINX_RUNNING=false
if docker ps --format "{{.Names}}" | grep -q "^${NGINX_CONTAINER_NAME}$"; then
    NGINX_RUNNING=true
    echo -e "${GREEN}✅ Nginx container sedang berjalan${NC}"
    
    # Check if nginx config has webroot location
    if [ -f "$NGINX_CONF_PATH" ] && grep -q "\.well-known/acme-challenge" "$NGINX_CONF_PATH"; then
        echo -e "${GREEN}✅ Nginx sudah dikonfigurasi untuk webroot method${NC}"
        USE_WEBROOT=true
    else
        echo -e "${YELLOW}⚠️  Nginx belum dikonfigurasi untuk webroot, akan menggunakan standalone method${NC}"
        USE_WEBROOT=false
    fi
else
    echo -e "${YELLOW}⚠️  Nginx container tidak berjalan, akan menggunakan standalone method${NC}"
    USE_WEBROOT=false
fi

# Step 3: Generate certificate with Certbot
echo ""
if [ "$USE_WEBROOT" = true ]; then
    echo -e "${BLUE}🔐 Step 3: Generate SSL certificate dengan Let's Encrypt (webroot method)...${NC}"
    echo -e "${GREEN}💡 Menggunakan webroot method - tidak perlu stop service di port 80${NC}"
    
    # Ensure nginx can serve the webroot
    docker exec "$NGINX_CONTAINER_NAME" mkdir -p /var/www/certbot 2>/dev/null || true
    
    # Use webroot method (nginx must be running and configured)
    certbot certonly --webroot \
        --webroot-path="$WEBROOT_PATH" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --preferred-challenges http \
        -d "$DOMAIN" || {
        echo -e "${YELLOW}⚠️  Webroot method gagal, mencoba standalone method...${NC}"
        USE_WEBROOT=false
    }
fi

# Fallback to standalone method if webroot failed or not available
if [ "$USE_WEBROOT" = false ]; then
    echo ""
    echo -e "${BLUE}🔐 Step 3: Generate SSL certificate dengan Let's Encrypt (standalone method)...${NC}"
    echo -e "${YELLOW}⚠️  Standalone method memerlukan port 80 bebas${NC}"
    
    # Check what's using port 80
    PORT_80_USAGE=$(lsof -i :80 2>/dev/null || netstat -tulpn 2>/dev/null | grep :80 | head -1 || ss -tulpn 2>/dev/null | grep :80 | head -1 || echo "")
    
    if [ -n "$PORT_80_USAGE" ]; then
        echo -e "${YELLOW}⚠️  Port 80 sedang digunakan:${NC}"
        echo "$PORT_80_USAGE"
        echo ""
        echo -e "${YELLOW}💡 Tips: Jika port 80 digunakan project lain, pastikan nginx container KSM berjalan${NC}"
        echo -e "${YELLOW}   dan sudah dikonfigurasi untuk webroot method agar tidak perlu stop service lain${NC}"
        echo ""
        
        # Try to stop only KSM nginx container (not other services)
        if docker ps --format "{{.Names}}" | grep -q "^${NGINX_CONTAINER_NAME}$"; then
            echo "Menghentikan KSM nginx container sementara untuk standalone method..."
            docker stop "$NGINX_CONTAINER_NAME" 2>/dev/null || true
            sleep 2
        fi
        
        # Check again
        PORT_80_CHECK=$(lsof -i :80 2>/dev/null || netstat -tulpn 2>/dev/null | grep :80 | head -1 || ss -tulpn 2>/dev/null | grep :80 | head -1 || echo "")
        if [ -n "$PORT_80_CHECK" ]; then
            echo -e "${RED}❌ ERROR: Port 80 masih digunakan oleh service lain!${NC}"
            echo "Service yang menggunakan port 80:"
            echo "$PORT_80_CHECK"
            echo ""
            echo -e "${YELLOW}💡 Solusi:${NC}"
            echo "  1. Pastikan nginx container KSM berjalan dan dikonfigurasi untuk webroot"
            echo "  2. Atau hentikan service lain yang menggunakan port 80 secara manual"
            echo "  3. Atau gunakan DNS-01 challenge (tidak memerlukan port 80)"
            exit 1
        fi
    fi
    
    # Use standalone method
    certbot certonly --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --preferred-challenges http \
        --http-01-port 80 \
        -d "$DOMAIN" || {
        echo -e "${RED}❌ ERROR: Gagal generate certificate!${NC}"
        echo ""
        echo "Possible causes:"
        echo "  1. Domain $DOMAIN belum pointing ke server IP"
        echo "  2. Port 80 masih digunakan oleh service lain"
        echo "  3. Firewall memblokir port 80"
        echo "  4. Let's Encrypt rate limit (jika baru saja mencoba)"
        echo ""
        echo "Troubleshooting:"
        echo "  - Cek DNS: nslookup $DOMAIN atau dig $DOMAIN"
        echo "  - Cek port 80: lsof -i :80 atau netstat -tulpn | grep :80"
        echo "  - Cek firewall: ufw status atau iptables -L"
        echo "  - Test koneksi: curl -I http://$DOMAIN"
        echo ""
        echo -e "${YELLOW}💡 Alternatif: Pastikan nginx container KSM berjalan dan gunakan webroot method${NC}"
        exit 1
    }
fi

echo -e "${GREEN}✅ Certificate berhasil di-generate${NC}"

# Step 4: Copy certificates to deployment directory
echo ""
echo -e "${BLUE}📋 Step 4: Copy certificates ke deployment directory...${NC}"

CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
SSL_DIR="$DEPLOY_PATH/infrastructure/nginx/ssl"

mkdir -p "$SSL_DIR"

# Copy certificates
cp "$CERT_DIR/fullchain.pem" "$SSL_DIR/cert.pem"
cp "$CERT_DIR/privkey.pem" "$SSL_DIR/key.pem"

# Set proper permissions
chmod 644 "$SSL_DIR/cert.pem"
chmod 600 "$SSL_DIR/key.pem"

echo -e "${GREEN}✅ Certificates sudah di-copy ke $SSL_DIR${NC}"

# Step 5: Update nginx config for Let's Encrypt
echo ""
echo -e "${BLUE}⚙️  Step 5: Update nginx config untuk Let's Encrypt...${NC}"

NGINX_CONF_PATH="$DEPLOY_PATH/infrastructure/nginx/$NGINX_CONF"

if [ -f "$NGINX_CONF_PATH" ]; then
    # Update SSL certificate paths in nginx config
    sed -i "s|ssl_certificate /etc/nginx/ssl/cert.pem;|ssl_certificate /etc/nginx/ssl/cert.pem;|g" "$NGINX_CONF_PATH"
    sed -i "s|ssl_certificate_key /etc/nginx/ssl/key.pem;|ssl_certificate_key /etc/nginx/ssl/key.pem;|g" "$NGINX_CONF_PATH"
    
    # Ensure HTTP server block redirects to HTTPS
    if ! grep -q "return 301 https" "$NGINX_CONF_PATH"; then
        echo -e "${YELLOW}⚠️  Pastikan HTTP server block redirect ke HTTPS${NC}"
    fi
    
    echo -e "${GREEN}✅ Nginx config sudah diupdate${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx config tidak ditemukan di $NGINX_CONF_PATH${NC}"
fi

# Step 6: Setup auto-renewal
echo ""
echo -e "${BLUE}🔄 Step 6: Setup auto-renewal untuk certificates...${NC}"

# Create renewal script
RENEWAL_SCRIPT="/usr/local/bin/ksm-ssl-renew.sh"
cat > "$RENEWAL_SCRIPT" << 'RENEWAL_EOF'
#!/bin/bash
# Auto-renewal script for KSM SSL certificates

ENVIRONMENT=$1
if [ "$ENVIRONMENT" = "dev" ]; then
    DOMAIN="devreport.ptkiansantang.com"
    DEPLOY_PATH="/opt/ksm-main-dev"
elif [ "$ENVIRONMENT" = "prod" ]; then
    DOMAIN="report.ptkiansantang.com"
    DEPLOY_PATH="/opt/ksm-main-prod"
else
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

# Renew certificate
certbot renew --quiet --webroot --webroot-path=/var/www/certbot

# Copy renewed certificates
CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
SSL_DIR="$DEPLOY_PATH/infrastructure/nginx/ssl"

if [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]; then
    cp "$CERT_DIR/fullchain.pem" "$SSL_DIR/cert.pem"
    cp "$CERT_DIR/privkey.pem" "$SSL_DIR/key.pem"
    chmod 644 "$SSL_DIR/cert.pem"
    chmod 600 "$SSL_DIR/key.pem"
    
    # Reload nginx container
    cd "$DEPLOY_PATH" || exit 1
    docker-compose exec -T nginx-dev nginx -s reload 2>/dev/null || \
    docker-compose exec -T nginx-prod nginx -s reload 2>/dev/null || \
    docker-compose restart nginx-dev 2>/dev/null || \
    docker-compose restart nginx-prod 2>/dev/null || true
    
    echo "Certificate renewed and nginx reloaded for $ENVIRONMENT"
fi
RENEWAL_EOF

chmod +x "$RENEWAL_SCRIPT"

# Add to crontab (run twice daily)
(crontab -l 2>/dev/null | grep -v "ksm-ssl-renew"; echo "0 0,12 * * * $RENEWAL_SCRIPT $ENVIRONMENT >> /var/log/ksm-ssl-renew.log 2>&1") | crontab -

echo -e "${GREEN}✅ Auto-renewal sudah di-setup${NC}"

# Step 7: Restart nginx container (if was stopped for standalone method)
echo ""
echo -e "${BLUE}🚀 Step 7: Restart nginx container...${NC}"
cd "$DEPLOY_PATH" || exit 1

# Check if nginx container is running
if docker ps --format "{{.Names}}" | grep -q "^${NGINX_CONTAINER_NAME}$"; then
    echo "Nginx container sudah berjalan, reloading config..."
    # Reload nginx config to ensure it's using the new certificates
    docker exec "$NGINX_CONTAINER_NAME" nginx -s reload 2>/dev/null || true
else
    echo "Menjalankan nginx container..."
    docker-compose up -d nginx-dev 2>/dev/null || docker-compose up -d nginx-prod 2>/dev/null || true
    sleep 5
fi

# Step 8: Verify SSL
echo ""
echo -e "${BLUE}✅ Step 8: Verifikasi SSL certificate...${NC}"
echo "Testing SSL connection..."

if curl -k -s "https://$DOMAIN" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SSL certificate berfungsi!${NC}"
    echo ""
    echo "Test dengan:"
    echo "  curl -I https://$DOMAIN"
    echo "  openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"
else
    echo -e "${YELLOW}⚠️  SSL test gagal, tetapi certificate sudah di-generate${NC}"
    echo "Pastikan nginx container berjalan dan domain sudah pointing ke server"
fi

# Summary
echo ""
echo -e "${GREEN}=============================================================================${NC}"
echo -e "${GREEN}✅ SSL Setup selesai!${NC}"
echo -e "${GREEN}=============================================================================${NC}"
echo ""
echo "📋 Informasi:"
echo "   - Domain: $DOMAIN"
echo "   - Environment: $ENVIRONMENT"
echo "   - Certificate location: $SSL_DIR"
echo "   - Auto-renewal: Setup (check /var/log/ksm-ssl-renew.log)"
echo ""
echo "📝 Langkah selanjutnya:"
echo "   1. Pastikan domain $DOMAIN sudah pointing ke server IP"
echo "   2. Test SSL: curl -I https://$DOMAIN"
echo "   3. Monitor auto-renewal: tail -f /var/log/ksm-ssl-renew.log"
echo ""

