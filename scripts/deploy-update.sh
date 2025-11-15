#!/bin/bash

# =============================================================================
# KSM Main - Deployment Update Script
# =============================================================================
# Script untuk deployment update (setiap kali ada perubahan)
# Usage: ./deploy-update.sh [dev|prod]
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

if [ "$ENVIRONMENT" = "dev" ]; then
    DEPLOY_PATH="/opt/ksm-main-dev"
    BRANCH="dev"
    COMPOSE_FILE="docker-compose.dev.yml"
    BACKEND_PORT="8002"
    AGENT_PORT="5002"
    FRONTEND_PORT="3006"
elif [ "$ENVIRONMENT" = "prod" ]; then
    DEPLOY_PATH="/opt/ksm-main-prod"
    BRANCH="main"
    COMPOSE_FILE="docker-compose.yml"
    BACKEND_PORT="8001"
    AGENT_PORT="5001"
    FRONTEND_PORT="3005"
else
    echo -e "${RED}❌ ERROR: Environment harus 'dev' atau 'prod'${NC}"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}KSM Main - Deployment Update (${ENVIRONMENT^^})${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# Check if deploy path exists
if [ ! -d "$DEPLOY_PATH" ]; then
    echo -e "${RED}❌ ERROR: Directory $DEPLOY_PATH tidak ditemukan!${NC}"
    echo "Jalankan setup terlebih dahulu: ./scripts/deploy-setup.sh $ENVIRONMENT"
    exit 1
fi

# Change to deploy directory
cd "$DEPLOY_PATH"

# Step 1: Pull latest changes
echo -e "${BLUE}📥 Step 1: Pull latest changes dari repository...${NC}"
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ ERROR: Directory ini bukan git repository!${NC}"
    echo "Jalankan setup terlebih dahulu: ./scripts/deploy-setup.sh $ENVIRONMENT"
    exit 1
fi

git pull origin "$BRANCH"
echo -e "${GREEN}✅ Repository sudah diupdate${NC}"

# Step 2: Fix directory structure if needed
echo ""
echo -e "${BLUE}🔧 Step 2: Memeriksa struktur direktori...${NC}"
if [ -d "ksm-main-dev" ] || [ -d "ksm-main-prod" ]; then
    echo -e "${YELLOW}⚠️  Memperbaiki struktur direktori yang salah...${NC}"
    
    SUBDIR=""
    if [ -d "ksm-main-dev" ]; then
        SUBDIR="ksm-main-dev"
    elif [ -d "ksm-main-prod" ]; then
        SUBDIR="ksm-main-prod"
    fi
    
    if [ -n "$SUBDIR" ]; then
        cd "$SUBDIR"
        # Move all files using find (safer than mv *)
        find . -maxdepth 1 -not -name '.' -not -name '..' -exec mv {} .. \;
        cd ..
        rmdir "$SUBDIR" 2>/dev/null || rm -rf "$SUBDIR"
        echo -e "${GREEN}✅ Struktur direktori sudah diperbaiki${NC}"
    fi
else
    echo -e "${GREEN}✅ Struktur direktori sudah benar${NC}"
fi

# Step 3: Update docker-compose.yml
echo ""
echo -e "${BLUE}📋 Step 3: Update docker-compose.yml...${NC}"
if [ "$ENVIRONMENT" = "dev" ] && [ -f "docker-compose.dev.yml" ]; then
    cp docker-compose.dev.yml docker-compose.yml
    echo -e "${GREEN}✅ docker-compose.yml sudah diupdate${NC}"
elif [ "$ENVIRONMENT" = "prod" ] && [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}✅ docker-compose.yml sudah ada${NC}"
else
    echo -e "${RED}❌ ERROR: File docker-compose tidak ditemukan!${NC}"
    exit 1
fi

# Step 4: Verify directory structure
echo ""
echo -e "${BLUE}📁 Step 4: Verifikasi struktur direktori...${NC}"
echo "Struktur direktori:"
ls -la | grep -E "(backend|frontend-vite|infrastructure|docker-compose)" || true
echo ""

# Check required folders
REQUIRED_FOLDERS=("backend" "frontend-vite" "infrastructure")
MISSING_FOLDERS=()

for folder in "${REQUIRED_FOLDERS[@]}"; do
    if [ ! -d "$folder" ]; then
        MISSING_FOLDERS+=("$folder")
    fi
done

if [ ${#MISSING_FOLDERS[@]} -gt 0 ]; then
    echo -e "${RED}❌ ERROR: Folder berikut tidak ditemukan: ${MISSING_FOLDERS[*]}${NC}"
    echo "Pastikan struktur direktori benar sebelum melanjutkan."
    exit 1
fi

echo -e "${GREEN}✅ Semua folder yang diperlukan ditemukan${NC}"

# Step 5: Stop existing containers
echo ""
echo -e "${BLUE}🛑 Step 5: Menghentikan container yang ada...${NC}"
docker-compose -f docker-compose.yml down || true
echo -e "${GREEN}✅ Container sudah dihentikan${NC}"

# Step 6: Build Docker images
echo ""
echo -e "${BLUE}🔨 Step 6: Building Docker images...${NC}"
docker-compose -f docker-compose.yml build --no-cache
echo -e "${GREEN}✅ Docker images sudah dibuild${NC}"

# Step 7: Start services
echo ""
echo -e "${BLUE}🚀 Step 7: Starting services...${NC}"
docker-compose -f docker-compose.yml up -d
echo -e "${GREEN}✅ Services sudah dimulai${NC}"

# Step 8: Wait for services to start
echo ""
echo -e "${BLUE}⏳ Step 8: Menunggu services start (30 detik)...${NC}"
sleep 30

# Step 9: Check status
echo ""
echo -e "${BLUE}📊 Step 9: Status container:${NC}"
docker-compose -f docker-compose.yml ps

# Step 10: Health check
echo ""
echo -e "${BLUE}🏥 Step 10: Testing health endpoints...${NC}"

# Backend health check
echo -n "Backend (port $BACKEND_PORT): "
if curl -s -f "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⚠️  Tidak merespon (mungkin masih starting)${NC}"
fi

# Agent AI health check
echo -n "Agent AI (port $AGENT_PORT): "
if curl -s -f "http://localhost:$AGENT_PORT/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⚠️  Tidak merespon (mungkin masih starting)${NC}"
fi

# Frontend health check
echo -n "Frontend (port $FRONTEND_PORT): "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$FRONTEND_PORT" || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}✅ OK (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${YELLOW}⚠️  HTTP $HTTP_CODE (mungkin masih starting)${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}=============================================================================${NC}"
echo -e "${GREEN}✅ Deployment selesai!${NC}"
echo -e "${GREEN}=============================================================================${NC}"
echo ""
echo "📋 Informasi:"
echo "   - Environment: $ENVIRONMENT"
echo "   - Deploy Path: $DEPLOY_PATH"
echo "   - Branch: $BRANCH"
echo ""
echo "📝 Perintah berguna:"
echo "   - View logs: docker-compose -f docker-compose.yml logs -f"
echo "   - View status: docker-compose -f docker-compose.yml ps"
echo "   - Restart: docker-compose -f docker-compose.yml restart"
echo "   - Stop: docker-compose -f docker-compose.yml down"
echo ""

