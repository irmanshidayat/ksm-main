#!/bin/bash
# =============================================================================
# KSM Main - SSL Certificate Chain Fix Script
# =============================================================================
# Script untuk memperbaiki certificate chain yang tidak lengkap
# Usage: ./fix-ssl-chain.sh [dev|prod]
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

echo -e "${BLUE}🔧 KSM Main - SSL Certificate Chain Fix${NC}"
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

# Check current certificate chain
echo -e "${BLUE}📋 Step 1: Checking current certificate chain...${NC}"
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ Certificate files not found!${NC}"
    echo "   Certificate: $CERT_FILE"
    echo "   Key: $KEY_FILE"
    exit 1
fi

CERT_CHAIN_COUNT=$(grep -c "BEGIN CERTIFICATE" "$CERT_FILE" 2>/dev/null || echo "0")
echo "   Current certificate chain count: $CERT_CHAIN_COUNT"

if [ "$CERT_CHAIN_COUNT" -ge 2 ]; then
    echo -e "${GREEN}✅ Certificate chain sudah lengkap!${NC}"
    echo ""
    echo "💡 Certificate chain sudah benar. Masalah mungkin di tempat lain:"
    echo "   1. Nginx belum restart setelah certificate di-update"
    echo "   2. Certificate tidak cocok dengan domain"
    echo "   3. DNS belum pointing dengan benar"
    echo ""
    echo "Coba restart nginx:"
    echo "   docker-compose restart $NGINX_CONTAINER"
    exit 0
fi

echo -e "${YELLOW}⚠️  Certificate chain tidak lengkap (hanya $CERT_CHAIN_COUNT certificate)${NC}"
echo ""

# Step 2: Find Let's Encrypt certificate
echo -e "${BLUE}📋 Step 2: Mencari Let's Encrypt certificate...${NC}"

# Try standard location first
LETSENCRYPT_CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
LETSENCRYPT_KEY="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

if [ -f "$LETSENCRYPT_CERT" ] && [ -f "$LETSENCRYPT_KEY" ]; then
    echo -e "${GREEN}✅ Let's Encrypt certificate found di lokasi standar${NC}"
    echo "   Certificate: $LETSENCRYPT_CERT"
    echo "   Key: $LETSENCRYPT_KEY"
    
    # Check fullchain count
    FULLCHAIN_COUNT=$(grep -c "BEGIN CERTIFICATE" "$LETSENCRYPT_CERT" 2>/dev/null || echo "0")
    echo "   Fullchain contains: $FULLCHAIN_COUNT certificate(s)"
    
    if [ "$FULLCHAIN_COUNT" -ge 2 ]; then
        USE_LETSENCRYPT=true
    else
        echo -e "${YELLOW}⚠️  Let's Encrypt fullchain juga tidak lengkap${NC}"
        USE_LETSENCRYPT=false
    fi
else
    echo -e "${YELLOW}⚠️  Let's Encrypt certificate tidak ditemukan di lokasi standar${NC}"
    echo "   Mencari di lokasi alternatif..."
    
    # Search in alternative locations
    ALTERNATIVE_LOCATIONS=(
        "/etc/letsencrypt/live/*/fullchain.pem"
        "/etc/letsencrypt/archive/*/fullchain*.pem"
        "/root/.acme.sh/$DOMAIN/fullchain.cer"
        "/root/.acme.sh/$DOMAIN/*.cer"
    )
    
    FOUND_CERT=""
    for location in "${ALTERNATIVE_LOCATIONS[@]}"; do
        for cert_file in $location 2>/dev/null; do
            if [ -f "$cert_file" ]; then
                # Check if certificate matches domain
                if openssl x509 -in "$cert_file" -noout -subject 2>/dev/null | grep -q "$DOMAIN"; then
                    FOUND_CERT="$cert_file"
                    echo -e "${GREEN}✅ Certificate ditemukan di: $cert_file${NC}"
                    
                    # Try to find corresponding key
                    CERT_DIR=$(dirname "$cert_file")
                    KEY_CANDIDATES=(
                        "$CERT_DIR/privkey.pem"
                        "$CERT_DIR/../privkey.pem"
                        "/root/.acme.sh/$DOMAIN/$DOMAIN.key"
                        "/root/.acme.sh/$DOMAIN/*.key"
                    )
                    
                    for key_file in "${KEY_CANDIDATES[@]}"; do
                        for key_candidate in $key_file 2>/dev/null; do
                            if [ -f "$key_candidate" ]; then
                                FULLCHAIN_COUNT=$(grep -c "BEGIN CERTIFICATE" "$cert_file" 2>/dev/null || echo "0")
                                if [ "$FULLCHAIN_COUNT" -ge 2 ]; then
                                    LETSENCRYPT_CERT="$cert_file"
                                    LETSENCRYPT_KEY="$key_candidate"
                                    USE_LETSENCRYPT=true
                                    echo -e "${GREEN}✅ Key ditemukan di: $key_candidate${NC}"
                                    break 2
                                fi
                            fi
                        done
                    done
                fi
            fi
        done
    done
    
    if [ -z "$FOUND_CERT" ] || [ "$USE_LETSENCRYPT" != "true" ]; then
        echo -e "${RED}❌ Let's Encrypt certificate tidak ditemukan${NC}"
        echo ""
        echo "💡 Solusi:"
        echo "   1. Generate certificate baru dengan:"
        echo "      ./scripts/setup-ssl.sh $ENVIRONMENT your-email@example.com"
        echo ""
        echo "   2. Atau jika certificate ada di lokasi lain, copy manual:"
        echo "      cp <path-to-fullchain.pem> $CERT_FILE"
        echo "      cp <path-to-privkey.pem> $KEY_FILE"
        exit 1
    fi
fi

# Step 3: Copy certificates
if [ "$USE_LETSENCRYPT" = "true" ]; then
    echo ""
    echo -e "${BLUE}📋 Step 3: Copy certificates ke deployment directory...${NC}"
    
    # Backup old certificates
    if [ -f "$CERT_FILE" ]; then
        BACKUP_FILE="${CERT_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CERT_FILE" "$BACKUP_FILE"
        echo "   Backup certificate lama: $BACKUP_FILE"
    fi
    
    if [ -f "$KEY_FILE" ]; then
        BACKUP_KEY="${KEY_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$KEY_FILE" "$BACKUP_KEY"
        echo "   Backup key lama: $BACKUP_KEY"
    fi
    
    # Copy new certificates
    cp "$LETSENCRYPT_CERT" "$CERT_FILE"
    cp "$LETSENCRYPT_KEY" "$KEY_FILE"
    
    # Set permissions
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"
    
    echo -e "${GREEN}✅ Certificates sudah di-copy${NC}"
    
    # Verify new certificate chain
    NEW_CHAIN_COUNT=$(grep -c "BEGIN CERTIFICATE" "$CERT_FILE" 2>/dev/null || echo "0")
    echo "   New certificate chain count: $NEW_CHAIN_COUNT"
    
    if [ "$NEW_CHAIN_COUNT" -ge 2 ]; then
        echo -e "${GREEN}✅ Certificate chain sekarang lengkap!${NC}"
    else
        echo -e "${YELLOW}⚠️  Certificate chain masih tidak lengkap${NC}"
    fi
fi

# Step 4: Restart nginx
echo ""
echo -e "${BLUE}📋 Step 4: Restart nginx container...${NC}"

if docker ps --format "{{.Names}}" | grep -q "^${NGINX_CONTAINER}$"; then
    # Test nginx config first
    if docker exec "$NGINX_CONTAINER" nginx -t >/dev/null 2>&1; then
        echo "   Testing nginx config..."
        docker exec "$NGINX_CONTAINER" nginx -t
        echo ""
        echo "   Reloading nginx..."
        docker exec "$NGINX_CONTAINER" nginx -s reload && \
            echo -e "${GREEN}✅ Nginx config reloaded${NC}" || {
            echo -e "${YELLOW}⚠️  Reload failed, restarting container...${NC}"
            docker-compose restart "$NGINX_CONTAINER" 2>/dev/null || \
                docker restart "$NGINX_CONTAINER"
            sleep 5
            echo -e "${GREEN}✅ Nginx container restarted${NC}"
        }
    else
        echo -e "${YELLOW}⚠️  Nginx config test failed, restarting container...${NC}"
        docker exec "$NGINX_CONTAINER" nginx -t || true
        docker-compose restart "$NGINX_CONTAINER" 2>/dev/null || \
            docker restart "$NGINX_CONTAINER"
        sleep 5
        echo -e "${GREEN}✅ Nginx container restarted${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Nginx container tidak berjalan${NC}"
    echo "   Starting nginx container..."
    docker-compose up -d "$NGINX_CONTAINER" 2>/dev/null || true
    sleep 5
    echo -e "${GREEN}✅ Nginx container started${NC}"
fi

# Step 5: Verify
echo ""
echo -e "${BLUE}📋 Step 5: Verifikasi SSL...${NC}"

if command -v openssl >/dev/null 2>&1; then
    CERT_SUBJECT=$(openssl x509 -in "$CERT_FILE" -noout -subject 2>/dev/null | sed 's/subject=//' || echo "")
    if echo "$CERT_SUBJECT" | grep -q "$DOMAIN"; then
        echo -e "${GREEN}✅ Certificate matches domain${NC}"
    else
        echo -e "${YELLOW}⚠️  Certificate does NOT match domain${NC}"
        echo "   Subject: $CERT_SUBJECT"
    fi
fi

echo ""
echo -e "${GREEN}✅ SSL certificate chain fix completed!${NC}"
echo ""
echo "💡 Test SSL connection:"
echo "   curl -I https://$DOMAIN"
echo "   openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"
echo ""
echo "   Atau buka di browser: https://$DOMAIN"

