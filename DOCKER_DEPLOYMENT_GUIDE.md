# BlueBirdHub Docker Deployment Guide

This guide provides comprehensive instructions for deploying BlueBirdHub using Docker.

## 📋 Prerequisites

Before deploying, ensure you have:
1. Docker installed (version 20.10 or higher)
2. Docker Compose installed (version 2.0 or higher)
3. Git installed
4. At least 4GB of available RAM
5. 10GB of free disk space

## 🚀 Quick Start (Recommended)

### One-Command Deployment

```bash
# Clone the repository and deploy
git clone https://github.com/yourusername/BlueBirdHub.git
cd BlueBirdHub
cp config/env.example .env.production
# Edit .env.production with your values
docker-compose -f docker-compose.bluebbird.yml up -d --build
```

### Automated Deployment Script

For an even easier deployment, use our deployment script:

```bash
# On Linux/Mac
bash scripts/deploy-docker.sh

# On Windows (PowerShell)
powershell scripts/deploy-docker.sh
```

This script will:
- Check Docker prerequisites
- Create .env.production if needed
- Let you choose deployment type
- Build and start all services
- Verify deployment health

## 📦 Detailed Deployment Steps

### 1️⃣ Environment Setup

First, create your production environment file:

```bash
# Create production environment file
cp config/env.example .env.production

# Edit the file with your production values
nano .env.production
```

Required environment variables:
```env
# Database
DB_PASSWORD=your_secure_database_password

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Redis
REDIS_PASSWORD=your_redis_password

# AI API Keys (at least one required)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
GEMINI_API_KEY=your_gemini_key

# Monitoring (optional)
GRAFANA_PASSWORD=your_grafana_password
```

### 2️⃣ Build and Deploy with Docker Compose

#### Standard Deployment (Recommended)

```bash
# Using the BlueBirdHub-specific compose file
docker-compose -f docker-compose.bluebbird.yml up -d --build

# Or using the default compose file
docker-compose up -d --build

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

#### Production Deployment with Monitoring

```bash
# Deploy with monitoring stack (Prometheus + Grafana)
docker-compose --profile monitoring up -d --build

# Access services:
# - Application: http://localhost:8000
# - Frontend: http://localhost:3002
# - Grafana: http://localhost:3001 (admin/your_grafana_password)
# - Prometheus: http://localhost:9091
```

### 3️⃣ Manual Docker Deployment (Alternative)

If you prefer to run containers individually:

#### Create Network

```bash
docker network create bluebbird-network
```

#### Run PostgreSQL

```bash
docker run -d \
  --name bluebbird-postgres \
  --network bluebbird-network \
  -e POSTGRES_DB=bluebbirdhub_prod \
  -e POSTGRES_USER=bluebbirdhub \
  -e POSTGRES_PASSWORD=your_secure_password \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15-alpine
```

#### Run Redis

```bash
docker run -d \
  --name bluebbird-redis \
  --network bluebbird-network \
  -e REDIS_PASSWORD=your_redis_password \
  -v redis_data:/data \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --appendonly yes --requirepass your_redis_password
```

#### Build and Run BlueBirdHub

```bash
# Build the image
docker build -t bluebbirdhub:latest .

# Run the application
docker run -d \
  --name bluebbirdhub \
  --network bluebbird-network \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://bluebbirdhub:your_secure_password@bluebbird-postgres:5432/bluebbirdhub_prod \
  -e REDIS_URL=redis://:your_redis_password@bluebbird-redis:6379 \
  -e SECRET_KEY=your_secret_key \
  -e JWT_SECRET_KEY=your_jwt_secret \
  -v bluebbird_data:/app/data \
  -v bluebbird_uploads:/app/uploads \
  -v bluebbird_logs:/app/logs \
  bluebbirdhub:latest
```

### 4️⃣ Health Checks and Verification

```bash
# Check if all containers are running
docker-compose ps

# Test the health endpoint
curl http://localhost:8000/health

# View application logs (using the simplified compose file)
docker-compose -f docker-compose.bluebbird.yml logs -f bluebbird-backend

# Or with the default compose file
docker-compose logs -f ordnungshub-backend

# Check database connection
docker-compose exec postgres psql -U bluebbirdhub -d bluebbirdhub_prod -c "SELECT 1"

# Check Redis connection
docker-compose exec redis redis-cli -a your_redis_password ping
```

### 5️⃣ Common Operations

#### View Logs

```bash
# All services
docker-compose logs -f

# Specific service (simplified compose)
docker-compose -f docker-compose.bluebbird.yml logs -f bluebbird-backend

# Specific service (default compose)
docker-compose logs -f ordnungshub-backend

# Last 100 lines
docker-compose logs --tail=100 bluebbird-backend
```

#### Access Container Shell

```bash
# Backend container (simplified compose)
docker-compose -f docker-compose.bluebbird.yml exec bluebbird-backend bash

# Backend container (default compose)
docker-compose exec ordnungshub-backend bash

# Database container
docker-compose exec postgres psql -U bluebbirdhub -d bluebbirdhub_prod

# Redis CLI
docker-compose exec redis redis-cli -a your_redis_password
```

#### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart bluebbird-backend
```

#### Update Deployment

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### 6️⃣ Production Best Practices

#### SSL/TLS Configuration

1. Place your SSL certificates in `nginx/ssl/`
2. Update `nginx/nginx.conf` with your domain
3. Restart nginx: `docker-compose restart nginx`

#### Backup Strategy

```bash
# Backup database
docker-compose exec postgres pg_dump -U bluebbirdhub bluebbirdhub_prod > backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v bluebbird_data:/data -v $(pwd):/backup alpine tar czf /backup/data_backup_$(date +%Y%m%d).tar.gz -C /data .
```

#### Resource Limits

Add to docker-compose.yml for production:
```yaml
services:
  bluebbird-backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 7️⃣ Troubleshooting

#### Container Won't Start

```bash
# Check logs
docker-compose logs bluebbird-backend

# Check permissions
docker-compose exec bluebbird-backend ls -la /app/data
```

#### Database Connection Issues

```bash
# Test connection
docker-compose exec bluebbird-backend python -c "from src.backend.database.database import test_connection; test_connection()"

# Check database logs
docker-compose logs postgres
```

#### Port Conflicts

```bash
# Check what's using the port (Linux/Mac)
sudo lsof -i :8000

# Check what's using the port (Windows)
netstat -ano | findstr :8000

# Use different ports in docker-compose.yml
ports:
  - "8080:8000"  # Map to 8080 instead
```

### 8️⃣ Scaling

#### Horizontal Scaling

```bash
# Scale backend workers
docker-compose up -d --scale bluebbird-backend=3

# With load balancer (requires nginx configuration)
docker-compose --profile production up -d
```

#### Performance Tuning

```bash
# Increase worker count
docker-compose exec bluebbird-backend bash -c "WORKERS=8 python -m uvicorn src.backend.main:app --workers 8"

# Monitor performance
docker stats
```

## 🛡️ Security Checklist

- [ ] Change all default passwords
- [ ] Use strong, unique passwords for database and Redis
- [ ] Set secure SECRET_KEY and JWT_SECRET_KEY
- [ ] Configure CORS_ORIGINS for your domain only
- [ ] Enable SSL/TLS in production
- [ ] Regularly update Docker images
- [ ] Implement firewall rules
- [ ] Enable container security scanning

## 📊 Monitoring

Access monitoring dashboards:
- Grafana: http://localhost:3001 (admin/your_password)
- Prometheus: http://localhost:9091

## 🆘 Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables are set correctly
3. Ensure ports are not already in use
4. Check Docker daemon is running: `docker info`

## 📝 Additional Notes

- The application uses a non-root user (`ordnungshub`) for security
- Data is persisted in Docker volumes
- Health checks ensure service availability
- The setup includes automatic database migrations
- Frontend is served via nginx for better performance
- Two Docker Compose files are available:
  - `docker-compose.yml` - Original configuration with "ordnungshub" naming
  - `docker-compose.bluebbird.yml` - Simplified configuration with "bluebbird" naming

---

For more detailed configuration options, refer to the individual service documentation in the `docs/` directory. 