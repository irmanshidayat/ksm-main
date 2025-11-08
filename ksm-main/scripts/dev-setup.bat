@echo off
REM KSM Main Development Setup Script untuk Windows
REM Script untuk setup development environment dengan mudah

echo 🚀 KSM Main Development Setup
echo ==============================

REM Check prerequisites
echo [SETUP] Checking prerequisites...

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    pause
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

echo [INFO] Prerequisites check passed!

REM Setup environment file
echo [SETUP] Setting up environment file...
if not exist .env (
    if exist env.example (
        copy env.example .env
        echo [INFO] Created .env file from env.example
    ) else (
        echo [ERROR] env.example file not found!
        pause
        exit /b 1
    )
) else (
    echo [WARNING] .env file already exists. Skipping...
)

REM Create necessary directories
echo [SETUP] Creating necessary directories...
if not exist logs\backend mkdir logs\backend
if not exist logs\frontend mkdir logs\frontend
if not exist logs\mysql mkdir logs\mysql
if not exist logs\redis mkdir logs\redis
if not exist logs\nginx mkdir logs\nginx

echo [INFO] Directories created successfully!

REM Build Docker images
echo [SETUP] Building Docker images...
docker-compose build
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Docker images!
    pause
    exit /b 1
)

echo [INFO] Docker images built successfully!

REM Start services
echo [SETUP] Starting services...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services!
    pause
    exit /b 1
)

echo [INFO] Services started successfully!

REM Wait for services to be ready
echo [SETUP] Waiting for services to be ready...

REM Wait for MySQL
echo [INFO] Waiting for MySQL...
:wait_mysql
docker-compose exec -T ksm-mysql-dev mysqladmin ping -h localhost --silent >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_mysql
)

REM Wait for Redis
echo [INFO] Waiting for Redis...
:wait_redis
docker-compose exec -T ksm-redis-dev redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_redis
)

REM Wait for Backend
echo [INFO] Waiting for Backend...
:wait_backend
curl -f http://localhost:8000/api/health >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_backend
)

REM Wait for Frontend
echo [INFO] Waiting for Frontend...
:wait_frontend
curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 >nul
    goto wait_frontend
)

echo [INFO] All services are ready!

REM Show service status
echo.
echo [SETUP] Service Status:
echo.
echo 🌐 Web Services:
echo   Frontend:     http://localhost:3000
echo   Backend API:  http://localhost:8000/api
echo   Nginx:        http://localhost
echo.
echo 🛠️  Development Tools:
echo   phpMyAdmin:   http://localhost:8080
echo   Redis Cmd:    http://localhost:8081
echo.
echo 📊 Database:
echo   MySQL:        localhost:3306
echo   Redis:        localhost:6379
echo.
echo 🤖 AI Services:
echo   Agent AI:     http://localhost:5000
echo.

REM Show useful commands
echo [SETUP] Useful Commands:
echo.
echo 📋 Docker Commands:
echo   docker-compose ps                    # Show service status
echo   docker-compose logs -f               # Show all logs
echo   docker-compose logs -f ksm-backend-dev  # Show backend logs
echo   docker-compose restart ksm-backend-dev  # Restart backend
echo   docker-compose down                   # Stop all services
echo   docker-compose up -d                  # Start all services
echo.
echo 🔧 Development Commands:
echo   docker-compose exec ksm-backend-dev bash    # Enter backend container
echo   docker-compose exec ksm-mysql-dev mysql -u root -p  # Enter MySQL
echo   docker-compose exec ksm-redis-dev redis-cli  # Enter Redis
echo.

echo.
echo [INFO] 🎉 Setup completed successfully!
echo.
echo [INFO] Development environment is ready!
echo [INFO] You can now start developing with hot reload enabled.
echo.
pause
