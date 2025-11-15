#!/bin/bash
# =============================================================================
# KSM Main - Fix SSL Certificate Mismatch
# =============================================================================
# Script untuk memperbaiki masalah certificate mismatch
# Usage: ./fix-ssl-certificate-mismatch.sh [dev|prod]
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

echo -e "${BLUE}🔧 KSM Main - Fix SSL Certificate Mismatch${NC}"
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

# Step 1: Verify certificate file
echo -e "${BLUE}📋 Step 1: Verifying certificate file...${NC}"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ Certificate files not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Certificate files exist${NC}"

# Check certificate subject
if command -v openssl >/dev/null 2>&1; then
    CERT_SUBJECT=$(openssl x509 -in "$CERT_FILE" -noout -subject 2>/dev/null | sed 's/subject=//' || echo "")
    echo "   Certificate subject: $CERT_SUBJECT"
    
    if ! echo "$CERT_SUBJECT" | grep -q "$DOMAIN"; then
        echo -e "${RED}❌ Certificate TIDAK cocok dengan domain!${NC}"
        echo "   Expected: $DOMAIN"
        echo "   Found: $CERT_SUBJECT"
        echo ""
        echo "💡 Solusi: Generate certificate baru untuk domain yang benar"
        echo "   ./scripts/setup-ssl.sh $ENVIRONMENT your-email@example.com"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Certificate cocok dengan domain${NC}"
fi

# Step 2: Check certificate di container
echo ""
echo -e "${BLUE}📋 Step 2: Checking certificate di nginx container...${NC}"

if ! docker ps --format "{{.Names}}" | grep -q "^${NGINX_CONTAINER}$"; then
    echo -e "${RED}❌ Nginx container tidak berjalan!${NC}"
    echo "   Starting nginx container..."
    docker-compose up -d "$NGINX_CONTAINER" 2>/dev/null || true
    sleep 5
fi

CONTAINER_CERT="/etc/nginx/ssl/cert.pem"

# Verify certificate di container
if docker exec "$NGINX_CONTAINER" test -f "$CONTAINER_CERT" 2>/dev/null; then
    CONTAINER_CERT_SUBJECT=$(docker exec "$NGINX_CONTAINER" openssl x509 -in "$CONTAINER_CERT" -noout -subject 2>/dev/null | sed 's/subject=//' || echo "")
    echo "   Certificate di container: $CONTAINER_CERT_SUBJECT"
    
    if [ "$CERT_SUBJECT" != "$CONTAINER_CERT_SUBJECT" ]; then
        echo -e "${YELLOW}⚠️  Certificate di container berbeda dengan di host${NC}"
        echo "   Ini berarti nginx perlu reload certificate"
    else
        echo -e "${GREEN}✅ Certificate di container sama dengan di host${NC}"
    fi
else
    echo -e "${RED}❌ Certificate tidak ditemukan di container!${NC}"
    echo "   Expected: $CONTAINER_CERT"
    echo ""
    echo "💡 Solusi: Restart nginx container untuk mount certificate"
fi

# Step 3: Force reload nginx
echo ""
echo -e "${BLUE}📋 Step 3: Force reload nginx...${NC}"

# Stop nginx container
echo "   Stopping nginx container..."
docker stop "$NGINX_CONTAINER" 2>/dev/null || true
sleep 2

# Start nginx container (akan mount certificate baru)
echo "   Starting nginx container..."
docker start "$NGINX_CONTAINER" 2>/dev/null || docker-compose up -d "$NGINX_CONTAINER" 2>/dev/null || true
sleep 5

# Wait for nginx to be ready
echo "   Waiting for nginx to be ready..."
for i in {1..10}; do
    if docker exec "$NGINX_CONTAINER" nginx -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Nginx is ready${NC}"
        break
    fi
    sleep 1
done

# Reload nginx config
echo "   Reloading nginx config..."
if docker exec "$NGINX_CONTAINER" nginx -t >/dev/null 2>&1; then
    docker exec "$NGINX_CONTAINER" nginx -s reload 2>/dev/null && \
        echo -e "${GREEN}✅ Nginx config reloaded${NC}" || {
        echo -e "${YELLOW}⚠️  Reload failed, restarting container...${NC}"
        docker restart "$NGINX_CONTAINER" 2>/dev/null || true
        sleep 5
    }
else
    echo -e "${YELLOW}⚠️  Nginx config test failed${NC}"
    docker exec "$NGINX_CONTAINER" nginx -t 2>&1 || true
    echo "   Restarting container..."
    docker restart "$NGINX_CONTAINER" 2>/dev/null || true
    sleep 5
fi

# Step 4: Verify SSL connection
echo ""
echo -e "${BLUE}📋 Step 4: Verifying SSL connection...${NC}"

# Test dengan openssl dari container
if docker exec "$NGINX_CONTAINER" command -v openssl >/dev/null 2>&1; then
    echo "Testing SSL connection dari container..."
    SSL_OUTPUT=$(echo | docker exec -i "$NGINX_CONTAINER" openssl s_client -connect localhost:443 -servername "$DOMAIN" 2>&1 || true)
    
    if echo "$SSL_OUTPUT" | grep -q "Verify return code: 0"; then
        echo -e "${GREEN}✅ SSL connection successful!${NC}"
        echo "   Verify return code: 0 (ok)"
    else
        VERIFY_CODE=$(echo "$SSL_OUTPUT" | grep "Verify return code" | cut -d: -f2 | tr -d ' ' || echo "unknown")
        echo -e "${YELLOW}⚠️  SSL connection warning${NC}"
        echo "   Verify return code: $VERIFY_CODE"
        
        # Check certificate subject from connection
        CERT_SUBJECT_CONN=$(echo "$SSL_OUTPUT" | grep -A 1 "subject=" | head -2 | tail -1 | sed 's/^[[:space:]]*//' || echo "")
        if [ -n "$CERT_SUBJECT_CONN" ]; then
            echo "   Certificate subject: $CERT_SUBJECT_CONN"
            if echo "$CERT_SUBJECT_CONN" | grep -q "$DOMAIN"; then
                echo -e "${GREEN}✅ Certificate cocok dengan domain${NC}"
            fi
        fi
    fi
fi

# Test dengan curl dari host
if command -v curl >/dev/null 2>&1; then
    echo ""
    echo "Testing SSL connection dari host dengan curl..."
    CURL_OUTPUT=$(curl -vI "https://$DOMAIN" 2>&1 || true)
    
    if echo "$CURL_OUTPUT" | grep -q "SSL: no alternative certificate subject name matches"; then
        echo -e "${RED}❌ SSL certificate mismatch masih terjadi!${NC}"
        echo ""
        echo "💡 Kemungkinan penyebab:"
        echo "   1. Certificate di file berbeda dengan yang digunakan nginx"
        echo "   2. Nginx cache certificate lama"
        echo "   3. Certificate tidak di-mount dengan benar ke container"
        echo ""
        echo "💡 Solusi tambahan:"
        echo "   1. Check certificate yang digunakan nginx:"
        echo "      docker exec $NGINX_CONTAINER openssl s_client -connect localhost:443 -servername $DOMAIN"
        echo ""
        echo "   2. Restart semua container:"
        echo "      docker-compose restart"
        echo ""
        echo "   3. Check nginx logs:"
        echo "      docker logs $NGINX_CONTAINER --tail 50"
    elif echo "$CURL_OUTPUT" | grep -q "HTTP/"; then
        HTTP_CODE=$(echo "$CURL_OUTPUT" | grep -i "HTTP/" | head -1 | awk '{print $2}' || echo "")
        if [ -n "$HTTP_CODE" ]; then
            echo -e "${GREEN}✅ SSL connection successful!${NC}"
            echo "   HTTP Status: $HTTP_CODE"
        fi
    fi
fi

echo ""
echo -e "${GREEN}✅ SSL certificate fix completed!${NC}"
echo ""
echo "💡 Test SSL connection:"
echo "   curl -I https://$DOMAIN"
echo "   openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"

