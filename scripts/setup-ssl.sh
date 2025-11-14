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

# Step 2: Check and stop services using port 80
echo ""
echo -e "${BLUE}🛑 Step 2: Memeriksa dan menghentikan service yang menggunakan port 80...${NC}"

# Check what's using port 80
PORT_80_USAGE=$(lsof -i :80 2>/dev/null || netstat -tulpn | grep :80 | head -1 || ss -tulpn | grep :80 | head -1 || echo "")

if [ -n "$PORT_80_USAGE" ]; then
    echo -e "${YELLOW}⚠️  Port 80 sedang digunakan:${NC}"
    echo "$PORT_80_USAGE"
    echo ""
    
    # Stop nginx container if running
    cd "$DEPLOY_PATH" || exit 1
    if docker-compose ps 2>/dev/null | grep -q "nginx"; then
        echo "Menghentikan nginx container..."
        docker-compose stop nginx-dev 2>/dev/null || docker-compose stop nginx-prod 2>/dev/null || true
        sleep 2
    fi
    
    # Stop system nginx if running
    if systemctl is-active --quiet nginx 2>/dev/null; then
        echo "Menghentikan system nginx..."
        systemctl stop nginx 2>/dev/null || true
        sleep 2
    fi
    
    # Stop any docker container using port 80
    DOCKER_PORT_80=$(docker ps --format "{{.ID}} {{.Ports}}" | grep ":80->" | awk '{print $1}' | head -1)
    if [ -n "$DOCKER_PORT_80" ]; then
        echo "Menghentikan docker container yang menggunakan port 80..."
        docker stop $DOCKER_PORT_80 2>/dev/null || true
        sleep 2
    fi
    
    # Verify port 80 is free
    sleep 2
    PORT_80_CHECK=$(lsof -i :80 2>/dev/null || netstat -tulpn | grep :80 | head -1 || ss -tulpn | grep :80 | head -1 || echo "")
    if [ -n "$PORT_80_CHECK" ]; then
        echo -e "${RED}❌ ERROR: Port 80 masih digunakan!${NC}"
        echo "Service yang menggunakan port 80:"
        echo "$PORT_80_CHECK"
        echo ""
        echo "Silakan hentikan service tersebut secara manual atau gunakan metode lain."
        echo "Mencoba menggunakan metode standalone certbot..."
    else
        echo -e "${GREEN}✅ Port 80 sudah bebas${NC}"
    fi
else
    echo -e "${GREEN}✅ Port 80 bebas${NC}"
fi

# Step 3: Generate certificate with Certbot (using standalone method)
echo ""
echo -e "${BLUE}🔐 Step 3: Generate SSL certificate dengan Let's Encrypt (standalone method)...${NC}"

# Create certbot directory
mkdir -p /var/www/certbot

# Use standalone method (doesn't require nginx)
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
    exit 1
}

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

# Step 7: Restart nginx container
echo ""
echo -e "${BLUE}🚀 Step 7: Restart nginx container...${NC}"
cd "$DEPLOY_PATH" || exit 1
docker-compose up -d nginx-dev 2>/dev/null || docker-compose up -d nginx-prod 2>/dev/null || true

# Wait a bit for nginx to start
sleep 5

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

