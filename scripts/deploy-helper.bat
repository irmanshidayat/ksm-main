@echo off
REM =============================================================================
REM KSM Main - Deployment Helper Script (Windows)
REM =============================================================================
REM 
REM Script helper untuk maintenance dan troubleshooting deployment
REM 
REM Usage:
REM   scripts\deploy-helper.bat [command] [environment]
REM 
REM Commands:
REM   - status: Check status semua services
REM   - logs: Show logs dari services
REM   - restart: Restart semua services
REM   - stop: Stop semua services
REM   - cleanup: Cleanup Docker resources
REM   - health: Check health semua services
REM 
REM Environment:
REM   - dev: Development environment
REM   - prod: Production environment
REM =============================================================================

setlocal enabledelayedexpansion

set COMMAND=%1
set ENVIRONMENT=%2

if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

if "%ENVIRONMENT%"=="dev" (
    set COMPOSE_FILE=docker-compose.dev.yml
    set DEPLOY_PATH=%DEPLOY_PATH_DEV%
    if "%DEPLOY_PATH%"=="" set DEPLOY_PATH=C:\opt\ksm-main-dev
    set BACKEND_PORT=8002
    set AGENT_PORT=5002
    set FRONTEND_PORT=3006
) else if "%ENVIRONMENT%"=="prod" (
    set COMPOSE_FILE=docker-compose.yml
    set DEPLOY_PATH=%DEPLOY_PATH_PROD%
    if "%DEPLOY_PATH%"=="" set DEPLOY_PATH=C:\opt\ksm-main-prod
    set BACKEND_PORT=8001
    set AGENT_PORT=5001
    set FRONTEND_PORT=3005
) else (
    echo ❌ Invalid environment. Use 'dev' or 'prod'
    exit /b 1
)

if "%COMMAND%"=="" set COMMAND=status

cd /d "%DEPLOY_PATH%"

if "%COMMAND%"=="status" (
    echo 📊 Checking status of services (%ENVIRONMENT%)...
    docker-compose -f %COMPOSE_FILE% ps
    goto :end
)

if "%COMMAND%"=="logs" (
    set SERVICE=%3
    if "%SERVICE%"=="" (
        echo 📋 Showing logs from all services (%ENVIRONMENT%)...
        docker-compose -f %COMPOSE_FILE% logs --tail=100 -f
    ) else (
        echo 📋 Showing logs from %SERVICE% (%ENVIRONMENT%)...
        docker-compose -f %COMPOSE_FILE% logs --tail=100 -f %SERVICE%
    )
    goto :end
)

if "%COMMAND%"=="restart" (
    set SERVICE=%3
    if "%SERVICE%"=="" (
        echo 🔄 Restarting all services (%ENVIRONMENT%)...
        docker-compose -f %COMPOSE_FILE% restart
    ) else (
        echo 🔄 Restarting %SERVICE% (%ENVIRONMENT%)...
        docker-compose -f %COMPOSE_FILE% restart %SERVICE%
    )
    goto :end
)

if "%COMMAND%"=="stop" (
    echo 🛑 Stopping all services (%ENVIRONMENT%)...
    docker-compose -f %COMPOSE_FILE% down
    goto :end
)

if "%COMMAND%"=="health" (
    echo 🏥 Checking health of services (%ENVIRONMENT%)...
    docker-compose -f %COMPOSE_FILE% ps --filter "health=healthy"
    echo.
    echo Testing health endpoints...
    echo Backend: http://localhost:%BACKEND_PORT%/api/health
    curl -f http://localhost:%BACKEND_PORT%/api/health && echo  ✅ || echo  ❌
    echo Agent AI: http://localhost:%AGENT_PORT%/health
    curl -f http://localhost:%AGENT_PORT%/health && echo  ✅ || echo  ❌
    echo Frontend: http://localhost:%FRONTEND_PORT%
    curl -f http://localhost:%FRONTEND_PORT% && echo  ✅ || echo  ❌
    goto :end
)

if "%COMMAND%"=="build" (
    echo 🔨 Building Docker images (%ENVIRONMENT%)...
    docker-compose -f %COMPOSE_FILE% build --no-cache
    goto :end
)

if "%COMMAND%"=="up" (
    echo 🚀 Starting all services (%ENVIRONMENT%)...
    docker-compose -f %COMPOSE_FILE% up -d
    goto :end
)

echo ❌ Unknown command: %COMMAND%
echo.
echo Usage: %0 [command] [environment]
echo.
echo Commands:
echo   status    - Check status of services
echo   logs      - Show logs (optionally specify service name)
echo   restart   - Restart services (optionally specify service name)
echo   stop      - Stop all services
echo   health    - Check health of services
echo   build     - Build Docker images
echo   up        - Start all services
echo.
echo Environment:
echo   dev       - Development (default)
echo   prod      - Production
echo.
echo Examples:
echo   %0 status dev
echo   %0 logs prod ksm-backend-prod
echo   %0 restart dev
exit /b 1

:end
endlocal

