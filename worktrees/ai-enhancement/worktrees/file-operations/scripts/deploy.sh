#!/bin/bash

# OrdnungsHub Production Deployment Script
set -e  # Exit on any error

echo "🚀 Starting OrdnungsHub Production Deployment..."
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_ENV=${1:-production}
PROJECT_NAME="ordnungshub"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if required environment files exist
    if [ ! -f ".env.${DEPLOY_ENV}" ]; then
        log_error "Environment file .env.${DEPLOY_ENV} not found"
        exit 1
    fi
    
    if [ ! -f ".env.secrets" ]; then
        log_error "Secrets file .env.secrets not found"
        log_warn "Please copy .env.secrets.example to .env.secrets and fill in the values"
        exit 1
    fi
    
    log_info "✅ All requirements satisfied"
}

backup_data() {
    if [ -d "data" ] || [ -d "uploads" ]; then
        log_info "Creating backup of existing data..."
        mkdir -p "$BACKUP_DIR"
        
        if [ -d "data" ]; then
            cp -r data "$BACKUP_DIR/"
            log_info "✅ Database backup created"
        fi
        
        if [ -d "uploads" ]; then
            cp -r uploads "$BACKUP_DIR/"
            log_info "✅ Uploads backup created"
        fi
        
        log_info "✅ Backup completed: $BACKUP_DIR"
    else
        log_info "No existing data to backup"
    fi
}

run_tests() {
    log_info "Running tests before deployment..."
    
    if [ -f "./quick_test.sh" ]; then
        ./quick_test.sh
        if [ $? -eq 0 ]; then
            log_info "✅ Tests passed"
        else
            log_error "Tests failed. Aborting deployment."
            exit 1
        fi
    else
        log_warn "Test script not found, skipping tests"
    fi
}

build_and_deploy() {
    log_info "Building and deploying containers..."
    
    # Copy environment files
    cp ".env.${DEPLOY_ENV}" .env
    
    # Build and start containers
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        DOCKER_COMPOSE_CMD="docker compose"
    fi
    
    # Pull latest images and build
    $DOCKER_COMPOSE_CMD pull
    $DOCKER_COMPOSE_CMD build --no-cache
    
    # Start services
    $DOCKER_COMPOSE_CMD up -d
    
    log_info "✅ Containers deployed"
}

wait_for_services() {
    log_info "Waiting for services to start..."
    
    # Wait for backend to be healthy
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_info "✅ Backend is healthy"
            break
        fi
        
        attempt=$((attempt + 1))
        echo "Waiting for backend... ($attempt/$max_attempts)"
        sleep 10
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Backend failed to start within expected time"
        $DOCKER_COMPOSE_CMD logs ordnungshub-backend
        exit 1
    fi
}

initialize_database() {
    log_info "Initializing database..."
    
    # Run database migrations/seeding if needed
    if command -v docker-compose &> /dev/null; then
        docker-compose exec -T ordnungshub-backend python -c "
from src.backend.database.database import init_db
from src.backend.database.seed import seed_database
init_db()
seed_database()
print('Database initialized successfully')
"
    else
        docker compose exec -T ordnungshub-backend python -c "
from src.backend.database.database import init_db
from src.backend.database.seed import seed_database
init_db()
seed_database()
print('Database initialized successfully')
"
    fi
    
    log_info "✅ Database initialized"
}

show_status() {
    log_info "Deployment Status:"
    echo "=================="
    
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
    
    echo ""
    echo "🌐 Application URLs:"
    echo "   Backend API: http://localhost:8000"
    echo "   Health Check: http://localhost:8000/health"
    echo "   API Docs: http://localhost:8000/docs"
    
    if docker ps | grep -q grafana; then
        echo "   Monitoring: http://localhost:3001 (admin/admin)"
    fi
    
    echo ""
    echo "📊 Useful Commands:"
    echo "   View logs: docker-compose logs -f ordnungshub-backend"
    echo "   Stop all: docker-compose down"
    echo "   Restart: docker-compose restart ordnungshub-backend"
    echo "   Shell: docker-compose exec ordnungshub-backend bash"
}

# Main deployment flow
main() {
    echo "Environment: $DEPLOY_ENV"
    echo "Project: $PROJECT_NAME"
    echo ""
    
    check_requirements
    
    if [ "$DEPLOY_ENV" = "production" ]; then
        backup_data
        run_tests
    fi
    
    build_and_deploy
    wait_for_services
    initialize_database
    
    log_info "🎉 Deployment completed successfully!"
    echo ""
    show_status
}

# Handle script arguments
case "$1" in
    "production"|"staging"|"development")
        main
        ;;
    "stop")
        log_info "Stopping all services..."
        if command -v docker-compose &> /dev/null; then
            docker-compose down
        else
            docker compose down
        fi
        ;;
    "restart")
        log_info "Restarting services..."
        if command -v docker-compose &> /dev/null; then
            docker-compose restart
        else
            docker compose restart
        fi
        ;;
    "logs")
        if command -v docker-compose &> /dev/null; then
            docker-compose logs -f ordnungshub-backend
        else
            docker compose logs -f ordnungshub-backend
        fi
        ;;
    "status")
        show_status
        ;;
    *)
        echo "Usage: $0 {production|staging|development|stop|restart|logs|status}"
        echo ""
        echo "Commands:"
        echo "  production  - Deploy to production environment"
        echo "  staging     - Deploy to staging environment" 
        echo "  development - Deploy to development environment"
        echo "  stop        - Stop all services"
        echo "  restart     - Restart all services"
        echo "  logs        - Show backend logs"
        echo "  status      - Show deployment status"
        exit 1
        ;;
esac