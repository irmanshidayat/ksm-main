#!/bin/bash
# =============================================================================
# KSM Main - Verify Nginx SSL Certificate
# =============================================================================
# Script untuk verify certificate yang digunakan nginx di container
# Usage: ./verify-nginx-ssl.sh [dev|prod]
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

echo -e "${BLUE}🔍 KSM Main - Verify Nginx SSL Certificate${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Domain: ${YELLOW}$DOMAIN${NC}"
echo ""

cd "$DEPLOY_PATH" || {
    echo -e "${RED}❌ Deploy path not found: $DEPLOY_PATH${NC}"
    exit 1
}

# Check 1: Certificate file di host
echo -e "${BLUE}📋 Check 1: Certificate file di host${NC}"
SSL_DIR="$DEPLOY_PATH/infrastructure/nginx/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ Certificate files not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Certificate files exist${NC}"
echo "   Certificate: $CERT_FILE"
echo "   Key: $KEY_FILE"

if command -v openssl >/dev/null 2>&1; then
    echo ""
    echo "   Certificate details (from file):"
    openssl x509 -in "$CERT_FILE" -noout -subject -issuer -dates 2>/dev/null || true
    echo ""
    echo "   Subject Alternative Names (SAN):"
    openssl x509 -in "$CERT_FILE" -noout -text 2>/dev/null | grep -A 1 "Subject Alternative Name" || echo "   No SAN found"
fi

# Check 2: Certificate di nginx container
echo ""
echo -e "${BLUE}📋 Check 2: Certificate di nginx container${NC}"

if ! docker ps --format "{{.Names}}" | grep -q "^${NGINX_CONTAINER}$"; then
    echo -e "${RED}❌ Nginx container tidak berjalan!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Nginx container is running${NC}"

# Check certificate di container
CONTAINER_CERT="/etc/nginx/ssl/cert.pem"
CONTAINER_KEY="/etc/nginx/ssl/key.pem"

if docker exec "$NGINX_CONTAINER" test -f "$CONTAINER_CERT" 2>/dev/null; then
    echo -e "${GREEN}✅ Certificate file exists di container${NC}"
    echo "   Container path: $CONTAINER_CERT"
    
    echo ""
    echo "   Certificate details (from container):"
    docker exec "$NGINX_CONTAINER" openssl x509 -in "$CONTAINER_CERT" -noout -subject -issuer -dates 2>/dev/null || true
    
    echo ""
    echo "   Subject Alternative Names (SAN) from container:"
    docker exec "$NGINX_CONTAINER" openssl x509 -in "$CONTAINER_CERT" -noout -text 2>/dev/null | grep -A 1 "Subject Alternative Name" || echo "   No SAN found"
    
    # Compare certificates
    echo ""
    echo -e "${BLUE}📋 Check 3: Comparing certificates${NC}"
    
    HOST_CERT_HASH=$(openssl x509 -in "$CERT_FILE" -noout -fingerprint -sha256 2>/dev/null | cut -d= -f2 || echo "")
    CONTAINER_CERT_HASH=$(docker exec "$NGINX_CONTAINER" openssl x509 -in "$CONTAINER_CERT" -noout -fingerprint -sha256 2>/dev/null | cut -d= -f2 || echo "")
    
    if [ -n "$HOST_CERT_HASH" ] && [ -n "$CONTAINER_CERT_HASH" ]; then
        if [ "$HOST_CERT_HASH" = "$CONTAINER_CERT_HASH" ]; then
            echo -e "${GREEN}✅ Certificates match (host dan container menggunakan certificate yang sama)${NC}"
        else
            echo -e "${RED}❌ Certificates TIDAK match!${NC}"
            echo "   Host certificate hash: $HOST_CERT_HASH"
            echo "   Container certificate hash: $CONTAINER_CERT_HASH"
            echo ""
            echo "   💡 Solusi: Restart nginx container untuk reload certificate"
        fi
    fi
else
    echo -e "${RED}❌ Certificate file tidak ditemukan di container!${NC}"
    echo "   Expected: $CONTAINER_CERT"
fi

# Check 4: Test SSL connection dari container
echo ""
echo -e "${BLUE}📋 Check 4: Test SSL connection dari container${NC}"

# Test dengan openssl dari container
if docker exec "$NGINX_CONTAINER" command -v openssl >/dev/null 2>&1; then
    echo "Testing SSL connection dengan openssl..."
    SSL_OUTPUT=$(echo | docker exec -i "$NGINX_CONTAINER" openssl s_client -connect localhost:443 -servername "$DOMAIN" 2>&1 || true)
    
    if echo "$SSL_OUTPUT" | grep -q "Verify return code: 0"; then
        echo -e "${GREEN}✅ SSL connection successful (Verify return code: 0)${NC}"
    else
        VERIFY_CODE=$(echo "$SSL_OUTPUT" | grep "Verify return code" | cut -d: -f2 | tr -d ' ' || echo "unknown")
        echo -e "${RED}❌ SSL connection failed!${NC}"
        echo "   Verify return code: $VERIFY_CODE"
        
        # Extract certificate subject from connection
        CERT_SUBJECT=$(echo "$SSL_OUTPUT" | grep -A 1 "subject=" | head -2 | tail -1 || echo "")
        if [ -n "$CERT_SUBJECT" ]; then
            echo "   Certificate subject from connection: $CERT_SUBJECT"
        fi
    fi
    
    # Check certificate subject from connection
    CERT_SUBJECT_CONN=$(echo "$SSL_OUTPUT" | grep -A 1 "subject=" | head -2 | tail -1 | sed 's/^[[:space:]]*//' || echo "")
    if [ -n "$CERT_SUBJECT_CONN" ]; then
        echo ""
        echo "   Certificate yang digunakan oleh nginx:"
        echo "   $CERT_SUBJECT_CONN"
        
        if echo "$CERT_SUBJECT_CONN" | grep -q "$DOMAIN"; then
            echo -e "${GREEN}✅ Certificate cocok dengan domain${NC}"
        else
            echo -e "${RED}❌ Certificate TIDAK cocok dengan domain!${NC}"
            echo "   Expected domain: $DOMAIN"
        fi
    fi
fi

# Check 5: Nginx config
echo ""
echo -e "${BLUE}📋 Check 5: Nginx SSL configuration${NC}"

if docker exec "$NGINX_CONTAINER" nginx -t >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
    
    # Extract SSL certificate path from nginx config
    NGINX_SSL_CERT=$(docker exec "$NGINX_CONTAINER" grep -r "ssl_certificate " /etc/nginx/nginx.conf /etc/nginx/conf.d/ 2>/dev/null | grep -v "#" | head -1 | awk '{print $2}' | tr -d ';' || echo "")
    NGINX_SSL_KEY=$(docker exec "$NGINX_CONTAINER" grep -r "ssl_certificate_key " /etc/nginx/nginx.conf /etc/nginx/conf.d/ 2>/dev/null | grep -v "#" | head -1 | awk '{print $2}' | tr -d ';' || echo "")
    
    if [ -n "$NGINX_SSL_CERT" ]; then
        echo "   SSL certificate path in nginx config: $NGINX_SSL_CERT"
        if [ "$NGINX_SSL_CERT" = "$CONTAINER_CERT" ]; then
            echo -e "${GREEN}✅ Nginx config menggunakan certificate path yang benar${NC}"
        else
            echo -e "${YELLOW}⚠️  Nginx config menggunakan certificate path yang berbeda${NC}"
            echo "   Expected: $CONTAINER_CERT"
            echo "   Found: $NGINX_SSL_CERT"
        fi
    fi
    
    if [ -n "$NGINX_SSL_KEY" ]; then
        echo "   SSL key path in nginx config: $NGINX_SSL_KEY"
    fi
else
    echo -e "${RED}❌ Nginx configuration has errors!${NC}"
    docker exec "$NGINX_CONTAINER" nginx -t 2>&1 || true
fi

# Summary and recommendations
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Summary & Recommendations${NC}"
echo ""

# Check if nginx needs restart
if [ "$HOST_CERT_HASH" != "$CONTAINER_CERT_HASH" ] && [ -n "$HOST_CERT_HASH" ] && [ -n "$CONTAINER_CERT_HASH" ]; then
    echo -e "${YELLOW}⚠️  Certificate di host berbeda dengan di container${NC}"
    echo ""
    echo "💡 Solusi: Restart nginx container"
    echo "   docker-compose restart $NGINX_CONTAINER"
    echo ""
    echo "   Atau reload nginx config:"
    echo "   docker exec $NGINX_CONTAINER nginx -s reload"
fi

echo ""
echo -e "${GREEN}✅ Verification completed!${NC}"

