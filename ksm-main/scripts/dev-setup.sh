#!/bin/bash

# KSM Main Development Setup Script
# Script untuk setup development environment dengan mudah

set -e

echo "🚀 KSM Main Development Setup"
echo "=============================="

# Colors untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function untuk print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_status "Prerequisites check passed!"
}

# Setup environment file
setup_environment() {
    print_header "Setting up environment file..."
    
    if [ ! -f .env ]; then
        if [ -f env.example ]; then
            cp env.example .env
            print_status "Created .env file from env.example"
        else
            print_error "env.example file not found!"
            exit 1
        fi
    else
        print_warning ".env file already exists. Skipping..."
    fi
}

# Create necessary directories
create_directories() {
    print_header "Creating necessary directories..."
    
    mkdir -p logs/backend
    mkdir -p logs/frontend
    mkdir -p logs/mysql
    mkdir -p logs/redis
    mkdir -p logs/nginx
    
    print_status "Directories created successfully!"
}

# Build Docker images
build_images() {
    print_header "Building Docker images..."
    
    # Build all services
    docker-compose build
    
    print_status "Docker images built successfully!"
}

# Start services
start_services() {
    print_header "Starting services..."
    
    # Start all services
    docker-compose up -d
    
    print_status "Services started successfully!"
}

# Wait for services to be ready
wait_for_services() {
    print_header "Waiting for services to be ready..."
    
    # Wait for MySQL
    print_status "Waiting for MySQL..."
    while ! docker-compose exec -T KSM-mysql-dev mysqladmin ping -h localhost --silent; do
        sleep 2
    done
    
    # Wait for Redis
    print_status "Waiting for Redis..."
    while ! docker-compose exec -T KSM-redis-dev redis-cli ping; do
        sleep 2
    done
    
    # Wait for Backend
    print_status "Waiting for Backend..."
    while ! curl -f http://localhost:8000/api/health &> /dev/null; do
        sleep 2
    done
    
    # Wait for Frontend
    print_status "Waiting for Frontend..."
    while ! curl -f http://localhost:3000 &> /dev/null; do
        sleep 2
    done
    
    print_status "All services are ready!"
}

# Show service status
show_status() {
    print_header "Service Status:"
    
    echo ""
    echo "🌐 Web Services:"
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend API:  http://localhost:8000/api"
    echo "  Nginx:        http://localhost"
    echo ""
    echo "🛠️  Development Tools:"
    echo "  phpMyAdmin:   http://localhost:8080"
    echo "  Redis Cmd:    http://localhost:8081"
    echo ""
    echo "📊 Database:"
    echo "  MySQL:        localhost:3306"
    echo "  Redis:        localhost:6379"
    echo ""
    echo "🤖 AI Services:"
    echo "  Agent AI:     http://localhost:5000"
    echo ""
}

# Show useful commands
show_commands() {
    print_header "Useful Commands:"
    
    echo ""
    echo "📋 Docker Commands:"
    echo "  docker-compose ps                    # Show service status"
    echo "  docker-compose logs -f               # Show all logs"
    echo "  docker-compose logs -f KSM-backend-dev  # Show backend logs"
    echo "  docker-compose restart KSM-backend-dev  # Restart backend"
    echo "  docker-compose down                   # Stop all services"
    echo "  docker-compose up -d                  # Start all services"
    echo ""
    echo "🔧 Development Commands:"
    echo "  docker-compose exec KSM-backend-dev bash    # Enter backend container"
    echo "  docker-compose exec KSM-mysql-dev mysql -u root -p  # Enter MySQL"
    echo "  docker-compose exec KSM-redis-dev redis-cli  # Enter Redis"
    echo ""
}

# Main setup function
main() {
    echo ""
    print_header "Starting KSM Main Development Setup..."
    echo ""
    
    # Run setup steps
    check_prerequisites
    setup_environment
    create_directories
    build_images
    start_services
    wait_for_services
    
    echo ""
    print_status "🎉 Setup completed successfully!"
    echo ""
    
    show_status
    show_commands
    
    echo ""
    print_status "Development environment is ready!"
    print_status "You can now start developing with hot reload enabled."
    echo ""
}

# Run main function
main "$@"
