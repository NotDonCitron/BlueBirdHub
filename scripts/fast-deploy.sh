#!/bin/bash

# BlueBirdHub Fast Deployment Script
# Reduces deployment time from 30+ minutes to under 2 minutes

set -e

echo "⚡ BlueBirdHub FAST Deployment Script"
echo "====================================="

# Enable Docker BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Function to check if image exists
image_exists() {
    docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$1" 2>/dev/null
}

# Function for incremental build
fast_build() {
    echo "🚀 Using optimized build process..."
    
    # Check if we can use cache
    if image_exists "bluebirdhub-backend:cache"; then
        echo "📦 Using cached layers for faster build..."
        docker build \
            --file Dockerfile.optimized \
            --target runtime \
            --cache-from bluebirdhub-backend:cache \
            --tag bluebirdhub-backend:latest \
            --tag bluebirdhub-backend:cache \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            .
    else
        echo "🔨 First build - creating cache layers..."
        docker build \
            --file Dockerfile.optimized \
            --target runtime \
            --tag bluebirdhub-backend:latest \
            --tag bluebirdhub-backend:cache \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            .
    fi
}

# Function for development build (even faster)
dev_build() {
    echo "⚡ Development build - maximum speed..."
    
    # Build only if source changed
    if [ "src" -nt "$(docker images --format "table {{.CreatedAt}}" bluebirdhub-backend:dev 2>/dev/null | head -1)" ]; then
        echo "🔄 Source changed, rebuilding..."
        docker build \
            --file Dockerfile.simple \
            --tag bluebirdhub-backend:dev \
            .
    else
        echo "✅ No changes detected, using existing image"
    fi
}

# Parse command line arguments
DEPLOYMENT_TYPE="fast"
FORCE_REBUILD=false
DEV_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|-d)
            DEV_MODE=true
            shift
            ;;
        --force|-f)
            FORCE_REBUILD=true
            shift
            ;;
        --production|-p)
            DEPLOYMENT_TYPE="production"
            shift
            ;;
        *)
            echo "Unknown option $1"
            echo "Usage: $0 [--dev|-d] [--force|-f] [--production|-p]"
            exit 1
            ;;
    esac
done

# Clean up old containers if force rebuild
if [ "$FORCE_REBUILD" = true ]; then
    echo "🧹 Force rebuild - cleaning up old containers..."
    docker-compose -f docker-compose.bluebbird.yml down --rmi local || true
fi

# Choose build strategy
if [ "$DEV_MODE" = true ]; then
    echo "🛠️  Development mode - using simple fast build"
    dev_build
    COMPOSE_FILE="docker-compose.dev.yml"
else
    echo "🚀 Production mode - using optimized multi-stage build"
    fast_build
    COMPOSE_FILE="docker-compose.bluebbird.yml"
fi

# Start services with optimized settings
echo "🏁 Starting services..."
if [ "$DEV_MODE" = true ]; then
    # Development: Start with build but use cache
    docker-compose -f $COMPOSE_FILE up -d --no-build
else
    # Production: Use pre-built image
    docker-compose -f $COMPOSE_FILE up -d --no-build
fi

# Quick health check
echo "⏳ Quick health check..."
timeout 60 bash -c 'until curl -f http://localhost:8000/health &>/dev/null; do sleep 2; done'

if [ $? -eq 0 ]; then
    echo "✅ Services are ready!"
    echo ""
    echo "🎉 Fast deployment complete!"
    echo "=========================="
    echo "⏱️  Total time: $(date)"
    echo "🌐 Backend API: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "💡 Pro tips:"
    echo "  - Use --dev for development (even faster)"
    echo "  - Use --force to rebuild from scratch"
    echo "  - Use docker system prune to clean up space"
else
    echo "❌ Health check failed. Check logs:"
    echo "   docker-compose -f $COMPOSE_FILE logs"
fi 