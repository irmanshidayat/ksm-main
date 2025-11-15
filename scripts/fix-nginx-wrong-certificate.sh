#!/bin/bash
# =============================================================================
# KSM Main - Fix Nginx Wrong Certificate
# =============================================================================
# Script untuk memperbaiki nginx yang menggunakan certificate salah
# Usage: ./fix-nginx-wrong-certificate.sh [dev|prod]
# =============================================================================

set -e

ENVIRONMENT=${1:-dev}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ "$ENVIRONMENT" = "dev" ]; then
    DOMAIN="devreport.ptkiansantang.com"
    DEPLOY_PATH="/opt/ksm-main-dev"
    NGINX_CONTAINER="KSM-nginx-dev"
elif [ "$ENVIRONMENT" = "prod" ]; then
    DOMAIN="report.ptkiansantang.com"
    DEPLOY_PATH="/opt/ksm-main-prod"
    NGINX_CONTAINER="KSM-nginx-prod"
else
    echo -e "${RED}❌ Invalid environment. Use 'dev' or 'prod'${NC}"
    exit 1
fi

echo -e "${BLUE}🔧 KSM Main - Fix Nginx Wrong Certificate${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Domain: ${YELLOW}$DOMAIN${NC}"
echo ""

cd "$DEPLOY_PATH" || {
    echo -e "${RED}❌ Deploy path not found: $DEPLOY_PATH${NC}"
    exit 1
}

SSL_DIR="$DEPLOY_PATH/infrastructure/nginx/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"

# Step 1: Verify certificate file di host
echo -e "${BLUE}📋 Step 1: Verifying certificate file di host...${NC}"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ Certificate files not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Certificate files exist${NC}"

if command -v openssl >/dev/null 2>&1; then
    CERT_SUBJECT=$(openssl x509 -in "$CERT_FILE" -noout -subject 2>/dev/null | sed 's/subject=//' || echo "")
    echo "   Certificate subject: $CERT_SUBJECT"
    
    if ! echo "$CERT_SUBJECT" | grep -q "$DOMAIN"; then
        echo -e "${RED}❌ Certificate TIDAK cocok dengan domain!${NC}"
        echo "   Expected: $DOMAIN"
        echo "   Found: $CERT_SUBJECT"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Certificate di host cocok dengan domain${NC}"
fi

# Step 2: Check certificate di container
echo ""
echo -e "${BLUE}📋 Step 2: Checking certificate di nginx container...${NC}"

if ! docker ps --format "{{.Names}}" | grep -q "^${NGINX_CONTAINER}$"; then
    echo -e "${RED}❌ Nginx container tidak berjalan!${NC}"
    exit 1
fi

CONTAINER_CERT="/etc/nginx/ssl/cert.pem"
CONTAINER_KEY="/etc/nginx/ssl/key.pem"

# Check certificate di container
if docker exec "$NGINX_CONTAINER" test -f "$CONTAINER_CERT" 2>/dev/null; then
    CONTAINER_CERT_SUBJECT=$(docker exec "$NGINX_CONTAINER" openssl x509 -in "$CONTAINER_CERT" -noout -subject 2>/dev/null | sed 's/subject=//' || echo "")
    echo "   Certificate di container: $CONTAINER_CERT_SUBJECT"
    
    if echo "$CONTAINER_CERT_SUBJECT" | grep -q "$DOMAIN"; then
        echo -e "${GREEN}✅ Certificate di container cocok dengan domain${NC}"
    else
        echo -e "${RED}❌ Certificate di container TIDAK cocok dengan domain!${NC}"
        echo "   Expected: $DOMAIN"
        echo "   Found: $CONTAINER_CERT_SUBJECT"
        echo ""
        echo "💡 Masalah: Certificate di container berbeda dengan di host"
    fi
else
    echo -e "${RED}❌ Certificate tidak ditemukan di container!${NC}"
fi

# Step 3: Check semua certificate di container
echo ""
echo -e "${BLUE}📋 Step 3: Checking semua certificate di container...${NC}"

echo "   Mencari semua file certificate di container..."
ALL_CERTS=$(docker exec "$NGINX_CONTAINER" find /etc/nginx -name "*.pem" -o -name "*.crt" 2>/dev/null || echo "")

if [ -n "$ALL_CERTS" ]; then
    echo "   Found certificates:"
    echo "$ALL_CERTS" | while read cert_path; do
        if [ -n "$cert_path" ]; then
            CERT_SUBJECT=$(docker exec "$NGINX_CONTAINER" openssl x509 -in "$cert_path" -noout -subject 2>/dev/null | sed 's/subject=//' || echo "invalid")
            echo "     $cert_path: $CERT_SUBJECT"
        fi
    done
fi

# Step 4: Check nginx config untuk certificate path
echo ""
echo -e "${BLUE}📋 Step 4: Checking nginx configuration...${NC}"

NGINX_SSL_CERT=$(docker exec "$NGINX_CONTAINER" grep -r "ssl_certificate " /etc/nginx/nginx.conf /etc/nginx/conf.d/ 2>/dev/null | grep -v "#" | head -1 | awk '{print $2}' | tr -d ';' || echo "")
NGINX_SSL_KEY=$(docker exec "$NGINX_CONTAINER" grep -r "ssl_certificate_key " /etc/nginx/nginx.conf /etc/nginx/conf.d/ 2>/dev/null | grep -v "#" | head -1 | awk '{print $2}' | tr -d ';' || echo "")

if [ -n "$NGINX_SSL_CERT" ]; then
    echo "   SSL certificate path in nginx config: $NGINX_SSL_CERT"
    if [ "$NGINX_SSL_CERT" = "$CONTAINER_CERT" ]; then
        echo -e "${GREEN}✅ Nginx config menggunakan certificate path yang benar${NC}"
    else
        echo -e "${YELLOW}⚠️  Nginx config menggunakan certificate path yang berbeda${NC}"
    fi
fi

# Step 5: Force remount certificate
echo ""
echo -e "${BLUE}📋 Step 5: Force remount certificate...${NC}"

# Stop nginx
echo "   Stopping nginx container..."
docker stop "$NGINX_CONTAINER" 2>/dev/null || true
sleep 2

# Verify certificate file masih ada dan benar
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ Certificate files tidak ditemukan setelah stop container!${NC}"
    exit 1
fi

# Check certificate sekali lagi
CERT_SUBJECT_CHECK=$(openssl x509 -in "$CERT_FILE" -noout -subject 2>/dev/null | sed 's/subject=//' || echo "")
if ! echo "$CERT_SUBJECT_CHECK" | grep -q "$DOMAIN"; then
    echo -e "${RED}❌ Certificate file TIDAK cocok dengan domain!${NC}"
    echo "   Certificate subject: $CERT_SUBJECT_CHECK"
    echo "   Expected domain: $DOMAIN"
    exit 1
fi

# Start nginx (akan mount certificate baru)
echo "   Starting nginx container..."
docker start "$NGINX_CONTAINER" 2>/dev/null || docker-compose up -d "$NGINX_CONTAINER" 2>/dev/null || true
sleep 5

# Verify certificate di container setelah start
echo "   Verifying certificate di container setelah start..."
if docker exec "$NGINX_CONTAINER" test -f "$CONTAINER_CERT" 2>/dev/null; then
    NEW_CONTAINER_CERT_SUBJECT=$(docker exec "$NGINX_CONTAINER" openssl x509 -in "$CONTAINER_CERT" -noout -subject 2>/dev/null | sed 's/subject=//' || echo "")
    echo "   Certificate di container: $NEW_CONTAINER_CERT_SUBJECT"
    
    if echo "$NEW_CONTAINER_CERT_SUBJECT" | grep -q "$DOMAIN"; then
        echo -e "${GREEN}✅ Certificate di container sekarang cocok dengan domain!${NC}"
    else
        echo -e "${RED}❌ Certificate di container masih TIDAK cocok!${NC}"
        echo "   Expected: $DOMAIN"
        echo "   Found: $NEW_CONTAINER_CERT_SUBJECT"
        echo ""
        echo "💡 Kemungkinan masalah:"
        echo "   1. Volume mount tidak bekerja dengan benar"
        echo "   2. Ada certificate lain yang di-mount"
        echo "   3. Docker volume cache"
        echo ""
        echo "💡 Solusi:"
        echo "   1. Check docker-compose.yml untuk volume mount"
        echo "   2. Remove dan recreate nginx container:"
        echo "      docker-compose stop nginx-dev"
        echo "      docker-compose rm -f nginx-dev"
        echo "      docker-compose up -d nginx-dev"
    fi
fi

# Step 6: Reload nginx
echo ""
echo -e "${BLUE}📋 Step 6: Reloading nginx...${NC}"

if docker exec "$NGINX_CONTAINER" nginx -t >/dev/null 2>&1; then
    docker exec "$NGINX_CONTAINER" nginx -s reload 2>/dev/null && \
        echo -e "${GREEN}✅ Nginx reloaded${NC}" || {
        echo -e "${YELLOW}⚠️  Reload failed, restarting...${NC}"
        docker restart "$NGINX_CONTAINER" 2>/dev/null || true
        sleep 5
    }
else
    echo -e "${YELLOW}⚠️  Nginx config test failed${NC}"
    docker exec "$NGINX_CONTAINER" nginx -t 2>&1 || true
fi

# Step 7: Test SSL connection
echo ""
echo -e "${BLUE}📋 Step 7: Testing SSL connection...${NC}"

# Test dengan openssl
if command -v openssl >/dev/null 2>&1; then
    echo "Testing dengan openssl..."
    SSL_OUTPUT=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>&1 || true)
    
    CERT_SUBJECT_CONN=$(echo "$SSL_OUTPUT" | grep -A 1 "subject=" | head -2 | tail -1 | sed 's/^[[:space:]]*//' || echo "")
    if [ -n "$CERT_SUBJECT_CONN" ]; then
        echo "   Certificate yang digunakan nginx: $CERT_SUBJECT_CONN"
        if echo "$CERT_SUBJECT_CONN" | grep -q "$DOMAIN"; then
            echo -e "${GREEN}✅ Certificate sekarang cocok dengan domain!${NC}"
        else
            echo -e "${RED}❌ Certificate masih TIDAK cocok!${NC}"
            echo "   Expected: $DOMAIN"
            echo "   Found: $CERT_SUBJECT_CONN"
        fi
    fi
fi

echo ""
echo -e "${GREEN}✅ Fix completed!${NC}"
echo ""
echo "💡 Test SSL connection:"
echo "   curl -I https://$DOMAIN"
echo "   openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"

