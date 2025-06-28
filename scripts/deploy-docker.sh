#!/bin/bash

# BlueBirdHub Docker Deployment Script
# This script simplifies the deployment process

set -e

echo "🚀 BlueBirdHub Docker Deployment Script"
echo "======================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "📝 Creating .env.production from template..."
    cp config/env.example .env.production
    echo "⚠️  Please edit .env.production with your production values before continuing."
    echo "   Required: DB_PASSWORD, SECRET_KEY, JWT_SECRET_KEY, REDIS_PASSWORD"
    echo "   At least one AI API key is also required."
    read -p "Press Enter after you've updated .env.production..."
fi

# Choose deployment type
echo ""
echo "Select deployment type:"
echo "1) Standard deployment (recommended)"
echo "2) Production deployment with monitoring"
echo "3) Development deployment"
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "🔨 Building and starting standard deployment..."
        docker-compose -f docker-compose.bluebbird.yml up -d --build
        ;;
    2)
        echo "🔨 Building and starting production deployment with monitoring..."
        docker-compose -f docker-compose.bluebbird.yml --profile production up -d --build
        echo "📊 Monitoring services will be available at:"
        echo "   - Grafana: http://localhost:3001"
        echo "   - Prometheus: http://localhost:9091"
        ;;
    3)
        echo "🔨 Building and starting development deployment..."
        docker-compose -f docker-compose.bluebbird.yml up --build
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo ""
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Backend health check failed. Check logs with: docker-compose logs bluebbird-backend"
fi

# Display access information
echo ""
echo "🎉 Deployment complete!"
echo "========================"
echo "Access your BlueBirdHub at:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.bluebbird.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.bluebbird.yml down"
echo "  - Restart services: docker-compose -f docker-compose.bluebbird.yml restart"
echo "  - Access backend shell: docker-compose -f docker-compose.bluebbird.yml exec bluebbird-backend bash"
echo ""
echo "Happy organizing! 🗂️" 