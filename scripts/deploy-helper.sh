#!/bin/bash
# =============================================================================
# KSM Main - Deployment Helper Script
# =============================================================================
# 
# Script helper untuk maintenance dan troubleshooting deployment
# 
# Usage:
#   ./scripts/deploy-helper.sh [command] [environment]
# 
# Commands:
#   - status: Check status semua services
#   - logs: Show logs dari services
#   - restart: Restart semua services
#   - stop: Stop semua services
#   - cleanup: Cleanup Docker resources
#   - health: Check health semua services
# 
# Environment:
#   - dev: Development environment
#   - prod: Production environment
# =============================================================================

set -e

ENVIRONMENT=${2:-dev}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "dev" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
    DEPLOY_PATH=${DEPLOY_PATH_DEV:-/opt/ksm-main-dev}
elif [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker-compose.yml"
    DEPLOY_PATH=${DEPLOY_PATH_PROD:-/opt/ksm-main-prod}
else
    echo "❌ Invalid environment. Use 'dev' or 'prod'"
    exit 1
fi

COMMAND=${1:-status}

case $COMMAND in
    status)
        echo "📊 Checking status of services ($ENVIRONMENT)..."
        cd "$DEPLOY_PATH"
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    
    logs)
        SERVICE=${3:-""}
        if [ -z "$SERVICE" ]; then
            echo "📋 Showing logs from all services ($ENVIRONMENT)..."
            cd "$DEPLOY_PATH"
            docker-compose -f "$COMPOSE_FILE" logs --tail=100 -f
        else
            echo "📋 Showing logs from $SERVICE ($ENVIRONMENT)..."
            cd "$DEPLOY_PATH"
            docker-compose -f "$COMPOSE_FILE" logs --tail=100 -f "$SERVICE"
        fi
        ;;
    
    restart)
        SERVICE=${3:-""}
        if [ -z "$SERVICE" ]; then
            echo "🔄 Restarting all services ($ENVIRONMENT)..."
            cd "$DEPLOY_PATH"
            docker-compose -f "$COMPOSE_FILE" restart
        else
            echo "🔄 Restarting $SERVICE ($ENVIRONMENT)..."
            cd "$DEPLOY_PATH"
            docker-compose -f "$COMPOSE_FILE" restart "$SERVICE"
        fi
        ;;
    
    stop)
        echo "🛑 Stopping all services ($ENVIRONMENT)..."
        cd "$DEPLOY_PATH"
        docker-compose -f "$COMPOSE_FILE" down
        ;;
    
    cleanup)
        echo "🧹 Cleaning up Docker resources ($ENVIRONMENT)..."
        cd "$DEPLOY_PATH"
        
        # Stop services
        docker-compose -f "$COMPOSE_FILE" down
        
        # Remove unused images
        docker image prune -f
        
        # Remove unused volumes (be careful!)
        read -p "⚠️  Remove unused volumes? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker volume prune -f
        fi
        
        # Remove unused networks
        docker network prune -f
        ;;
    
    health)
        echo "🏥 Checking health of services ($ENVIRONMENT)..."
        cd "$DEPLOY_PATH"
        
        # Check container health
        docker-compose -f "$COMPOSE_FILE" ps --filter "health=healthy"
        
        # Test endpoints
        echo ""
        echo "Testing health endpoints..."
        
        if [ "$ENVIRONMENT" = "dev" ]; then
            BACKEND_PORT=8002
            AGENT_PORT=5002
            FRONTEND_PORT=3006
        else
            BACKEND_PORT=8001
            AGENT_PORT=5001
            FRONTEND_PORT=3005
        fi
        
        echo "Backend: http://localhost:$BACKEND_PORT/api/health"
        curl -f http://localhost:$BACKEND_PORT/api/health && echo " ✅" || echo " ❌"
        
        echo "Agent AI: http://localhost:$AGENT_PORT/health"
        curl -f http://localhost:$AGENT_PORT/health && echo " ✅" || echo " ❌"
        
        echo "Frontend: http://localhost:$FRONTEND_PORT"
        curl -f http://localhost:$FRONTEND_PORT && echo " ✅" || echo " ❌"
        ;;
    
    build)
        echo "🔨 Building Docker images ($ENVIRONMENT)..."
        cd "$DEPLOY_PATH"
        docker-compose -f "$COMPOSE_FILE" build --no-cache
        ;;
    
    up)
        echo "🚀 Starting all services ($ENVIRONMENT)..."
        cd "$DEPLOY_PATH"
        docker-compose -f "$COMPOSE_FILE" up -d
        ;;
    
    *)
        echo "❌ Unknown command: $COMMAND"
        echo ""
        echo "Usage: $0 [command] [environment]"
        echo ""
        echo "Commands:"
        echo "  status    - Check status of services"
        echo "  logs      - Show logs (optionally specify service name)"
        echo "  restart   - Restart services (optionally specify service name)"
        echo "  stop      - Stop all services"
        echo "  cleanup   - Cleanup Docker resources"
        echo "  health    - Check health of services"
        echo "  build     - Build Docker images"
        echo "  up        - Start all services"
        echo ""
        echo "Environment:"
        echo "  dev       - Development (default)"
        echo "  prod      - Production"
        echo ""
        echo "Examples:"
        echo "  $0 status dev"
        echo "  $0 logs prod ksm-backend-prod"
        echo "  $0 restart dev"
        exit 1
        ;;
esac

