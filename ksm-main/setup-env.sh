#!/bin/bash
# KSM Main Environment Setup Script
# Script ini membantu setup environment files untuk semua service

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KSM Main Environment Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$SCRIPT_DIR"

# Function to setup env file
setup_env_file() {
    local service_name=$1
    local env_path=$2
    local env_example_path=$3
    
    echo -e "${YELLOW}Setting up ${service_name}...${NC}"
    
    if [ ! -f "$env_example_path" ]; then
        echo -e "${RED}❌ env.example not found at: ${env_example_path}${NC}"
        return 1
    fi
    
    if [ -f "$env_path" ]; then
        echo -e "${YELLOW}⚠️  .env already exists at: ${env_path}${NC}"
        read -p "Backup existing .env and create new? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            backup_path="${env_path}.backup.$(date +%Y%m%d_%H%M%S)"
            cp "$env_path" "$backup_path"
            echo -e "${GREEN}✅ Backed up to: ${backup_path}${NC}"
        else
            echo -e "${YELLOW}⏭️  Skipping ${service_name}${NC}"
            return 0
        fi
    fi
    
    cp "$env_example_path" "$env_path"
    echo -e "${GREEN}✅ Created .env for ${service_name}${NC}"
    echo ""
}

# Setup root level env (for docker-compose)
echo -e "${YELLOW}Setting up root level .env...${NC}"
setup_env_file "Root" "${ROOT_DIR}/.env" "${ROOT_DIR}/env.example"

# Setup backend env
echo -e "${YELLOW}Setting up backend .env...${NC}"
setup_env_file "Backend" "${ROOT_DIR}/backend/.env" "${ROOT_DIR}/backend/env.example"

# Setup frontend env
echo -e "${YELLOW}Setting up frontend .env...${NC}"
setup_env_file "Frontend" "${ROOT_DIR}/frontend/.env" "${ROOT_DIR}/frontend/env.example"

# Setup Agent AI env
AGENT_AI_DIR="${ROOT_DIR}/../Agent AI"
if [ -d "$AGENT_AI_DIR" ]; then
    echo -e "${YELLOW}Setting up Agent AI .env...${NC}"
    setup_env_file "Agent AI" "${AGENT_AI_DIR}/.env" "${AGENT_AI_DIR}/env.example"
else
    echo -e "${YELLOW}⚠️  Agent AI directory not found, skipping...${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Environment setup completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review and update .env files with your configuration"
echo "2. For Docker: Run 'docker-compose up -d'"
echo "3. For Local: Start services individually"
echo ""
echo -e "${YELLOW}Note:${NC} Applications will auto-detect Docker or Local environment"
echo "You can override by setting RUN_MODE=docker or RUN_MODE=local in .env"

