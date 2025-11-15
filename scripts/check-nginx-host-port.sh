#!/bin/bash
# =============================================================================
# KSM Main - Check Nginx on Host Port 443
# =============================================================================
# Script untuk check apakah ada nginx lain yang berjalan di port 443
# Usage: ./check-nginx-host-port.sh
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Checking Nginx on Host Port 443${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check 1: What's listening on port 443
echo -e "${BLUE}📋 Check 1: What's listening on port 443?${NC}"

if command -v lsof >/dev/null 2>&1; then
    PORT_443_PROCESS=$(lsof -i :443 2>/dev/null || echo "")
    if [ -n "$PORT_443_PROCESS" ]; then
        echo "$PORT_443_PROCESS"
        echo ""
        PID=$(echo "$PORT_443_PROCESS" | awk 'NR==2 {print $2}' || echo "")
        if [ -n "$PID" ]; then
            PROCESS_NAME=$(ps -p "$PID" -o comm= 2>/dev/null || echo "")
            echo "   Process: $PROCESS_NAME (PID: $PID)"
        fi
    else
        echo -e "${GREEN}✅ Port 443 is free${NC}"
    fi
elif command -v ss >/dev/null 2>&1; then
    PORT_443_PROCESS=$(ss -tlnp | grep ":443 " || echo "")
    if [ -n "$PORT_443_PROCESS" ]; then
        echo "$PORT_443_PROCESS"
    else
        echo -e "${GREEN}✅ Port 443 is free${NC}"
    fi
elif command -v netstat >/dev/null 2>&1; then
    PORT_443_PROCESS=$(netstat -tlnp 2>/dev/null | grep ":443 " || echo "")
    if [ -n "$PORT_443_PROCESS" ]; then
        echo "$PORT_443_PROCESS"
    else
        echo -e "${GREEN}✅ Port 443 is free${NC}"
    fi
fi

# Check 2: Check if nginx is running on host
echo ""
echo -e "${BLUE}📋 Check 2: Is nginx running on host?${NC}"

if systemctl is-active --quiet nginx 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Nginx service is running on host!${NC}"
    echo ""
    echo "   Status:"
    systemctl status nginx --no-pager -l 2>/dev/null | head -10 || true
    echo ""
    echo "   This might be using port 443 with certificate for jargas.ptkiansantang.com"
elif pgrep -x nginx >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Nginx process is running on host!${NC}"
    echo ""
    echo "   Processes:"
    ps aux | grep nginx | grep -v grep || true
else
    echo -e "${GREEN}✅ Nginx is not running on host${NC}"
fi

# Check 3: Check nginx config on host
echo ""
echo -e "${BLUE}📋 Check 3: Nginx config on host${NC}"

NGINX_CONF_LOCATIONS=(
    "/etc/nginx/nginx.conf"
    "/etc/nginx/conf.d/"
    "/etc/nginx/sites-enabled/"
    "/usr/local/nginx/conf/nginx.conf"
)

FOUND_NGINX_CONF=false
for location in "${NGINX_CONF_LOCATIONS[@]}"; do
    if [ -f "$location" ] || [ -d "$location" ]; then
        echo "   Found: $location"
        FOUND_NGINX_CONF=true
        
        # Check for SSL certificate config
        if [ -f "$location" ]; then
            SSL_CERT=$(grep -r "ssl_certificate " "$location" 2>/dev/null | grep -v "#" | head -1 || echo "")
            if [ -n "$SSL_CERT" ]; then
                echo "   SSL certificate config: $SSL_CERT"
            fi
        elif [ -d "$location" ]; then
            SSL_CERT=$(grep -r "ssl_certificate " "$location"/* 2>/dev/null | grep -v "#" | head -1 || echo "")
            if [ -n "$SSL_CERT" ]; then
                echo "   SSL certificate config: $SSL_CERT"
            fi
        fi
    fi
done

if [ "$FOUND_NGINX_CONF" = "false" ]; then
    echo -e "${GREEN}✅ No nginx config found on host${NC}"
fi

# Check 4: Test SSL connection to port 443
echo ""
echo -e "${BLUE}📋 Check 4: Test SSL connection to port 443${NC}"

if command -v openssl >/dev/null 2>&1; then
    echo "Testing SSL connection to localhost:443..."
    SSL_OUTPUT=$(echo | openssl s_client -connect localhost:443 -servername devreport.ptkiansantang.com 2>&1 || true)
    
    if echo "$SSL_OUTPUT" | grep -q "subject="; then
        CERT_SUBJECT=$(echo "$SSL_OUTPUT" | grep -A 1 "subject=" | head -2 | tail -1 | sed 's/^[[:space:]]*//' || echo "")
        echo "   Certificate subject: $CERT_SUBJECT"
        
        if echo "$CERT_SUBJECT" | grep -q "jargas.ptkiansantang.com"; then
            echo -e "${RED}❌ Port 443 is using certificate for jargas.ptkiansantang.com!${NC}"
            echo ""
            echo "💡 This is the problem! There's another nginx/service using port 443"
            echo "   with certificate for jargas.ptkiansantang.com"
        elif echo "$CERT_SUBJECT" | grep -q "devreport.ptkiansantang.com"; then
            echo -e "${GREEN}✅ Port 443 is using correct certificate${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Could not connect to port 443${NC}"
    fi
fi

# Check 5: Check Docker container port mapping
echo ""
echo -e "${BLUE}📋 Check 5: Docker container port mapping${NC}"

if docker ps --format "{{.Names}}\t{{.Ports}}" | grep -q "nginx"; then
    echo "   Nginx containers and their port mappings:"
    docker ps --format "{{.Names}}\t{{.Ports}}" | grep nginx | while read line; do
        echo "   $line"
    done
    echo ""
    echo "💡 Note: If nginx container uses 8444:443, it's only accessible on port 8444"
    echo "   Port 443 on host might be used by another service"
else
    echo -e "${YELLOW}⚠️  No nginx containers found${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Summary${NC}"
echo ""

if systemctl is-active --quiet nginx 2>/dev/null || pgrep -x nginx >/dev/null 2>&1; then
    echo -e "${RED}❌ PROBLEM FOUND: Nginx is running on host!${NC}"
    echo ""
    echo "💡 Solution:"
    echo "   1. Stop nginx on host:"
    echo "      sudo systemctl stop nginx"
    echo "      # OR"
    echo "      sudo service nginx stop"
    echo ""
    echo "   2. Disable nginx on host (optional):"
    echo "      sudo systemctl disable nginx"
    echo ""
    echo "   3. Or configure host nginx to proxy to Docker container on port 8444"
    echo ""
    echo "   4. Or change Docker port mapping to use port 443 directly:"
    echo "      Change '8444:443' to '443:443' in docker-compose.dev.yml"
    echo "      (Requires root or proper permissions)"
else
    echo -e "${GREEN}✅ No nginx running on host${NC}"
    echo ""
    echo "💡 If port 443 is still using wrong certificate, check:"
    echo "   1. Other web servers (Apache, Caddy, etc.)"
    echo "   2. Other Docker containers using port 443"
    echo "   3. Reverse proxy services"
fi

echo ""
echo -e "${GREEN}✅ Check completed!${NC}"

