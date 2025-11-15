#!/bin/bash

# =============================================================================
# KSM Main - Deployment Setup Script (Initial Setup)
# =============================================================================
# Script untuk setup awal deployment di server
# Usage: ./deploy-setup.sh [dev|prod]
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
REPO_URL="https://github.com/irmanshidayat/ksm-main.git"

if [ "$ENVIRONMENT" = "dev" ]; then
    DEPLOY_PATH="/opt/ksm-main-dev"
    BRANCH="dev"
    COMPOSE_FILE="docker-compose.dev.yml"
elif [ "$ENVIRONMENT" = "prod" ]; then
    DEPLOY_PATH="/opt/ksm-main-prod"
    BRANCH="main"
    COMPOSE_FILE="docker-compose.yml"
else
    echo -e "${RED}❌ ERROR: Environment harus 'dev' atau 'prod'${NC}"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}KSM Main - Deployment Setup (${ENVIRONMENT^^})${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  Warning: Script ini sebaiknya dijalankan sebagai root${NC}"
    echo "Gunakan: sudo $0 $ENVIRONMENT"
    read -p "Lanjutkan? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Install Git
echo -e "${BLUE}📦 Step 1: Memeriksa Git...${NC}"
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    apt update
    apt install -y git
else
    echo -e "${GREEN}✅ Git sudah terinstall${NC}"
fi

# Step 2: Clone repository
echo ""
echo -e "${BLUE}📥 Step 2: Clone repository...${NC}"
cd /opt

if [ -d "$DEPLOY_PATH" ]; then
    echo -e "${YELLOW}⚠️  Directory $DEPLOY_PATH sudah ada${NC}"
    read -p "Hapus dan clone ulang? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Menghapus directory lama..."
        rm -rf "$DEPLOY_PATH"
    else
        echo -e "${RED}❌ Setup dibatalkan${NC}"
        exit 1
    fi
fi

echo "Cloning repository ke $DEPLOY_PATH..."
git clone "$REPO_URL" "$DEPLOY_PATH"
cd "$DEPLOY_PATH"
git checkout "$BRANCH"

# Step 3: Setup Git config
echo ""
echo -e "${BLUE}⚙️  Step 3: Setup Git config...${NC}"
git config --global user.name "Server Deploy" || true
git config --global user.email "deploy@ksm.local" || true
echo -e "${GREEN}✅ Git config sudah diset${NC}"

# Step 4: Verifikasi file docker-compose
echo ""
echo -e "${BLUE}🔍 Step 4: Verifikasi file...${NC}"
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ ERROR: $COMPOSE_FILE tidak ditemukan!${NC}"
    echo "Struktur direktori saat ini:"
    ls -la
    exit 1
fi
echo -e "${GREEN}✅ $COMPOSE_FILE ditemukan${NC}"

# Step 5: Copy docker-compose file
echo ""
echo -e "${BLUE}📋 Step 5: Setup docker-compose.yml...${NC}"
if [ "$ENVIRONMENT" = "dev" ]; then
    cp docker-compose.dev.yml docker-compose.yml
    echo -e "${GREEN}✅ docker-compose.yml sudah dibuat dari docker-compose.dev.yml${NC}"
else
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}❌ ERROR: docker-compose.yml tidak ditemukan untuk production!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ docker-compose.yml sudah ada${NC}"
fi

# Step 6: Verifikasi struktur direktori
echo ""
echo -e "${BLUE}📁 Step 6: Verifikasi struktur direktori...${NC}"
echo "Struktur direktori:"
ls -la | head -20
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
    exit 1
fi

echo -e "${GREEN}✅ Semua folder yang diperlukan ditemukan${NC}"
echo "Folder yang ditemukan: backend, frontend-vite, infrastructure"

# Step 7: Create logs directory
echo ""
echo -e "${BLUE}📝 Step 7: Membuat directory logs...${NC}"
if [ "$ENVIRONMENT" = "dev" ]; then
    mkdir -p logs/{mysql-dev,nginx-dev,redis-dev,qdrant-dev}
    echo -e "${GREEN}✅ Logs directory untuk development sudah dibuat${NC}"
else
    mkdir -p logs/{mysql,nginx,redis,qdrant}
    echo -e "${GREEN}✅ Logs directory untuk production sudah dibuat${NC}"
fi

# Step 8: Summary
echo ""
echo -e "${GREEN}=============================================================================${NC}"
echo -e "${GREEN}✅ Setup selesai!${NC}"
echo -e "${GREEN}=============================================================================${NC}"
echo ""
echo "📋 Informasi:"
echo "   - Environment: $ENVIRONMENT"
echo "   - Deploy Path: $DEPLOY_PATH"
echo "   - Branch: $BRANCH"
echo "   - Compose File: docker-compose.yml"
echo ""
echo "📝 Langkah selanjutnya:"
echo "   1. Setup file .env di $DEPLOY_PATH"
echo "   2. Jalankan: cd $DEPLOY_PATH && docker-compose -f docker-compose.yml build --no-cache"
echo "   3. Jalankan: docker-compose -f docker-compose.yml up -d"
echo ""
echo "   Atau gunakan script: ./scripts/deploy-update.sh $ENVIRONMENT"
echo ""

