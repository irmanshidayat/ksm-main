#!/bin/bash
# =============================================================================
# KSM Main - Port Debug Script
# =============================================================================
# 
# Script untuk debug dan fix port conflicts di VPS
# 
# Usage:
#   ./scripts/debug-ports.sh [environment]
# 
# Environment:
#   - dev: Development environment (default)
#   - prod: Production environment
# =============================================================================

set -e

ENVIRONMENT=${1:-dev}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 KSM Main - Port Debug Script${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo ""

# Set ports based on environment
if [ "$ENVIRONMENT" = "dev" ]; then
    PORTS=(8002 3310 6381 6333 6334 5002 3006 8084 8444 9092 3007 8085)
    COMPOSE_FILE="docker-compose.dev.yml"
    DEPLOY_PATH="/opt/ksm-main-dev"
elif [ "$ENVIRONMENT" = "prod" ]; then
    PORTS=(8001 3309 6380 6333 6334 5001 3005 8082 8443 9091 3003 8083)
    COMPOSE_FILE="docker-compose.yml"
    DEPLOY_PATH="/opt/ksm-main-prod"
else
    echo -e "${RED}❌ Invalid environment. Use 'dev' or 'prod'${NC}"
    exit 1
fi

# Function to find process using a port
find_port_process() {
    local PORT=$1
    local PID=""
    local PROCESS=""
    
    # Method 1: lsof
    if command -v lsof >/dev/null 2>&1; then
        PID=$(lsof -ti:$PORT 2>/dev/null || echo "")
        if [ -n "$PID" ]; then
            PROCESS=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
            echo "$PID|$PROCESS"
            return
        fi
    fi
    
    # Method 2: ss
    if command -v ss >/dev/null 2>&1; then
        PID=$(ss -tlnp | grep ":$PORT " | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2 | head -1 | grep -oE '[0-9]+' || echo "")
        if [ -n "$PID" ]; then
            PROCESS=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
            echo "$PID|$PROCESS"
            return
        fi
    fi
    
    # Method 3: netstat
    if command -v netstat >/dev/null 2>&1; then
        PID=$(netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1 | head -1 || echo "")
        if [ -n "$PID" ] && [ "$PID" != "-" ]; then
            PROCESS=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
            echo "$PID|$PROCESS"
            return
        fi
    fi
    
    echo ""
}

# Function to kill process using a port
kill_port() {
    local PORT=$1
    local FORCE=${2:-false}
    
    echo -e "  ${YELLOW}🔍 Checking port $PORT...${NC}"
    
    local RESULT=$(find_port_process $PORT)
    if [ -n "$RESULT" ]; then
        local PID=$(echo $RESULT | cut -d'|' -f1)
        local PROCESS=$(echo $RESULT | cut -d'|' -f2)
        
        echo -e "  ${RED}⚠️  Port $PORT is in use by PID $PID ($PROCESS)${NC}"
        
        if [ "$FORCE" = "true" ]; then
            echo -e "  ${YELLOW}🔪 Killing process $PID...${NC}"
            kill -9 $PID 2>/dev/null || true
            sleep 2
            
            # Verify
            if [ -n "$(find_port_process $PORT)" ]; then
                echo -e "  ${YELLOW}⚠️  Process still running, trying pkill...${NC}"
                pkill -9 -f ":$PORT" || true
                sleep 2
            fi
            
            if [ -z "$(find_port_process $PORT)" ]; then
                echo -e "  ${GREEN}✅ Port $PORT freed${NC}"
            else
                echo -e "  ${RED}❌ Failed to free port $PORT${NC}"
            fi
        fi
    else
        echo -e "  ${GREEN}✅ Port $PORT is free${NC}"
    fi
}

# Function to cleanup Docker resources
cleanup_docker() {
    echo -e "${BLUE}🧹 Cleaning up Docker resources...${NC}"
    
    cd "$DEPLOY_PATH" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Deploy path not found: $DEPLOY_PATH${NC}"
        return
    }
    
    # Stop and remove containers
    echo "  🛑 Stopping containers..."
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    
    # Remove dangling containers
    echo "  🗑️  Removing dangling containers..."
    docker ps -a --filter "name=KSM-" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
    
    # Remove dangling networks
    echo "  🗑️  Removing dangling networks..."
    docker network ls --filter "name=KSM-" --format "{{.ID}}" | xargs -r docker network rm 2>/dev/null || true
    
    # Prune unused networks
    echo "  🧹 Pruning unused networks..."
    docker network prune -f 2>/dev/null || true
    
    echo -e "${GREEN}✅ Docker cleanup completed${NC}"
}

# Main menu
echo -e "${BLUE}Select action:${NC}"
echo "  1) Check port status (read-only)"
echo "  2) Check and kill processes using ports"
echo "  3) Cleanup Docker resources"
echo "  4) Full cleanup (ports + Docker)"
echo "  5) Check Docker container status"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}📊 Port Status Check${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        for PORT in "${PORTS[@]}"; do
            RESULT=$(find_port_process $PORT)
            if [ -n "$RESULT" ]; then
                PID=$(echo $RESULT | cut -d'|' -f1)
                PROCESS=$(echo $RESULT | cut -d'|' -f2)
                echo -e "Port ${YELLOW}$PORT${NC}: ${RED}IN USE${NC} by PID $PID ($PROCESS)"
            else
                echo -e "Port ${YELLOW}$PORT${NC}: ${GREEN}FREE${NC}"
            fi
        done
        ;;
    2)
        echo ""
        echo -e "${BLUE}🔪 Kill Processes Using Ports${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        for PORT in "${PORTS[@]}"; do
            kill_port $PORT true
        done
        echo ""
        echo -e "${GREEN}✅ Port cleanup completed${NC}"
        ;;
    3)
        cleanup_docker
        ;;
    4)
        echo ""
        echo -e "${BLUE}🧹 Full Cleanup${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        for PORT in "${PORTS[@]}"; do
            kill_port $PORT true
        done
        echo ""
        cleanup_docker
        echo ""
        echo -e "${GREEN}✅ Full cleanup completed${NC}"
        ;;
    5)
        echo ""
        echo -e "${BLUE}📊 Docker Container Status${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        cd "$DEPLOY_PATH" 2>/dev/null || {
            echo -e "${YELLOW}⚠️  Deploy path not found: $DEPLOY_PATH${NC}"
            exit 1
        }
        docker-compose -f "$COMPOSE_FILE" ps
        echo ""
        echo -e "${BLUE}📋 Recent Logs (last 20 lines)${NC}"
        docker-compose -f "$COMPOSE_FILE" logs --tail=20
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Done!${NC}"

