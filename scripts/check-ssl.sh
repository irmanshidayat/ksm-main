#!/bin/bash
# =============================================================================
# KSM Main - SSL Certificate Check & Fix Script
# =============================================================================
# Script untuk check dan fix SSL certificate issues
# Usage: ./check-ssl.sh [dev|prod]
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
    NGINX_CONF="nginx.dev.conf"
    NGINX_CONTAINER="KSM-nginx-dev"
elif [ "$ENVIRONMENT" = "prod" ]; then
    DOMAIN="report.ptkiansantang.com"
    DEPLOY_PATH="/opt/ksm-main-prod"
    NGINX_CONF="nginx.prod.conf"
    NGINX_CONTAINER="KSM-nginx-prod"
else
    echo -e "${RED}❌ Invalid environment. Use 'dev' or 'prod'${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 KSM Main - SSL Certificate Check & Fix${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Domain: ${YELLOW}$DOMAIN${NC}"
echo ""

cd "$DEPLOY_PATH" || {
    echo -e "${RED}❌ Deploy path not found: $DEPLOY_PATH${NC}"
    exit 1
}

# Check 1: SSL certificate files exist
echo -e "${BLUE}📋 Check 1: SSL Certificate Files${NC}"
SSL_DIR="$DEPLOY_PATH/infrastructure/nginx/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ SSL certificate files not found!${NC}"
    echo "   Certificate: $CERT_FILE"
    echo "   Key: $KEY_FILE"
    echo ""
    echo -e "${YELLOW}⚠️  SSL certificate files are missing.${NC}"
    echo "   Run: ./scripts/setup-ssl.sh $ENVIRONMENT your-email@example.com"
    exit 1
else
    echo -e "${GREEN}✅ SSL certificate files exist${NC}"
fi

# Check 2: Certificate validity
echo ""
echo -e "${BLUE}📋 Check 2: Certificate Validity${NC}"
if command -v openssl >/dev/null 2>&1; then
    # Check certificate expiration
    CERT_EXPIRY=$(openssl x509 -in "$CERT_FILE" -noout -enddate 2>/dev/null | cut -d= -f2)
    CERT_SUBJECT=$(openssl x509 -in "$CERT_FILE" -noout -subject 2>/dev/null | sed 's/subject=//')
    CERT_ISSUER=$(openssl x509 -in "$CERT_FILE" -noout -issuer 2>/dev/null | sed 's/issuer=//')
    
    if [ -n "$CERT_EXPIRY" ]; then
        EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$CERT_EXPIRY" +%s 2>/dev/null || echo "0")
        NOW_EPOCH=$(date +%s)
        DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
        
        echo "   Subject: $CERT_SUBJECT"
        echo "   Issuer: $CERT_ISSUER"
        echo "   Expires: $CERT_EXPIRY"
        
        if [ "$DAYS_LEFT" -lt 0 ]; then
            echo -e "${RED}❌ Certificate is EXPIRED!${NC}"
            echo "   Days expired: $(( -DAYS_LEFT ))"
        elif [ "$DAYS_LEFT" -lt 30 ]; then
            echo -e "${YELLOW}⚠️  Certificate expires soon!${NC}"
            echo "   Days left: $DAYS_LEFT"
        else
            echo -e "${GREEN}✅ Certificate is valid${NC}"
            echo "   Days left: $DAYS_LEFT"
        fi
        
        # Check if certificate matches domain
        if echo "$CERT_SUBJECT" | grep -q "$DOMAIN" || echo "$CERT_SUBJECT" | grep -q "CN=$DOMAIN"; then
            echo -e "${GREEN}✅ Certificate matches domain${NC}"
        else
            echo -e "${RED}❌ Certificate does NOT match domain!${NC}"
            echo "   Expected: $DOMAIN"
            echo "   Found: $CERT_SUBJECT"
        fi
    else
        echo -e "${YELLOW}⚠️  Could not read certificate details${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  openssl not available, skipping certificate validation${NC}"
fi

# Check 3: Nginx container status
echo ""
echo -e "${BLUE}📋 Check 3: Nginx Container Status${NC}"
if docker ps --format "{{.Names}}" | grep -q "^${NGINX_CONTAINER}$"; then
    echo -e "${GREEN}✅ Nginx container is running${NC}"
    
    # Check nginx config
    if docker exec "$NGINX_CONTAINER" nginx -t 2>&1 | grep -q "successful"; then
        echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
    else
        echo -e "${RED}❌ Nginx configuration has errors!${NC}"
        docker exec "$NGINX_CONTAINER" nginx -t 2>&1 || true
    fi
else
    echo -e "${RED}❌ Nginx container is not running!${NC}"
    echo "   Container: $NGINX_CONTAINER"
fi

# Check 4: SSL connection test
echo ""
echo -e "${BLUE}📋 Check 4: SSL Connection Test${NC}"
if command -v curl >/dev/null 2>&1; then
    echo "Testing SSL connection to $DOMAIN..."
    
    # Test with curl (ignore certificate errors for testing)
    HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "https://$DOMAIN" 2>&1 || echo "000")
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        echo -e "${GREEN}✅ SSL connection successful (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${YELLOW}⚠️  SSL connection returned HTTP $HTTP_CODE${NC}"
    fi
    
    # Test certificate with openssl
    if command -v openssl >/dev/null 2>&1; then
        echo "Testing certificate with openssl..."
        SSL_TEST=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>&1 | grep -E "(Verify return code|subject=|issuer=)" || echo "")
        if echo "$SSL_TEST" | grep -q "Verify return code: 0"; then
            echo -e "${GREEN}✅ Certificate verification successful${NC}"
        else
            echo -e "${RED}❌ Certificate verification failed!${NC}"
            echo "$SSL_TEST"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  curl not available, skipping connection test${NC}"
fi

# Check 5: DNS resolution
echo ""
echo -e "${BLUE}📋 Check 5: DNS Resolution${NC}"
if command -v nslookup >/dev/null 2>&1; then
    DNS_RESULT=$(nslookup "$DOMAIN" 2>&1 | grep -A 2 "Name:" || echo "")
    if [ -n "$DNS_RESULT" ]; then
        echo -e "${GREEN}✅ DNS resolution successful${NC}"
        echo "$DNS_RESULT"
    else
        echo -e "${YELLOW}⚠️  DNS resolution failed or incomplete${NC}"
    fi
elif command -v dig >/dev/null 2>&1; then
    DNS_RESULT=$(dig +short "$DOMAIN" 2>&1 | head -1 || echo "")
    if [ -n "$DNS_RESULT" ] && [ "$DNS_RESULT" != ";; connection timed out" ]; then
        echo -e "${GREEN}✅ DNS resolution successful${NC}"
        echo "   IP: $DNS_RESULT"
    else
        echo -e "${YELLOW}⚠️  DNS resolution failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  DNS tools not available${NC}"
fi

# Summary and recommendations
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Summary${NC}"
echo ""

# Check if Let's Encrypt certificate exists
LETSENCRYPT_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
if [ -f "$LETSENCRYPT_CERT" ]; then
    echo -e "${GREEN}✅ Let's Encrypt certificate found${NC}"
    echo "   Location: $LETSENCRYPT_CERT"
    echo ""
    echo "💡 Recommendation:"
    echo "   If certificate is invalid or expired, run:"
    echo "   ./scripts/setup-ssl.sh $ENVIRONMENT your-email@example.com"
else
    echo -e "${YELLOW}⚠️  Let's Encrypt certificate not found${NC}"
    echo ""
    echo "💡 Recommendation:"
    echo "   Setup SSL certificate with:"
    echo "   ./scripts/setup-ssl.sh $ENVIRONMENT your-email@example.com"
fi

echo ""
echo -e "${GREEN}✅ SSL check completed!${NC}"

