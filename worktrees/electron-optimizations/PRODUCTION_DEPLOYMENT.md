# 🚀 OrdnungsHub Production Deployment Guide

## Quick Start

```bash
# 1. Clone and setup
git clone <repository>
cd ordnungshub

# 2. Configure secrets
cp .env.secrets.example .env.secrets
# Edit .env.secrets with your secure values

# 3. Deploy to production
./scripts/deploy.sh production
```

---

## 📋 Prerequisites

### System Requirements
- **Docker** 20.10+ with Docker Compose
- **Minimum RAM**: 4GB (8GB recommended)
- **Storage**: 20GB+ available space
- **OS**: Linux, macOS, or Windows with WSL2

### Required Files
- ✅ `.env.secrets` - Copy from `.env.secrets.example` and fill secure values
- ✅ SSL certificates (for HTTPS) - Place in `nginx/ssl/`
- ✅ Domain configuration (optional)

---

## 🔧 Configuration

### 1. Environment Setup

```bash
# Copy environment template
cp .env.production.example .env.production

# Copy and configure secrets
cp .env.secrets.example .env.secrets
```

### 2. Required Secrets (.env.secrets)

```bash
# Database
DB_PASSWORD=your_very_secure_database_password

# Application Security  
SECRET_KEY=your_super_secret_key_minimum_32_chars
JWT_SECRET_KEY=your_jwt_signing_key_32_chars

# Redis Cache
REDIS_PASSWORD=your_redis_password

# External Services (optional)
OPENAI_API_KEY=sk-your-openai-key
SENTRY_DSN=https://your-sentry-dsn

# Domain Configuration
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 3. SSL Configuration (HTTPS)

```bash
# Place your SSL certificates in nginx/ssl/
nginx/ssl/
├── certificate.crt
└── private.key

# Update nginx.conf to enable HTTPS section
```

---

## 🚀 Deployment Options

### Option 1: Automated Script (Recommended)

```bash
# Full production deployment
./scripts/deploy.sh production

# Other environments  
./scripts/deploy.sh staging
./scripts/deploy.sh development
```

### Option 2: Manual Docker Compose

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ordnungshub-backend
```

### Option 3: Individual Services

```bash
# Start only core services
docker-compose up -d ordnungshub-backend postgres redis

# Add monitoring (optional)
docker-compose --profile monitoring up -d
```

---

## 📊 Service Architecture

### Core Services
- **ordnungshub-backend** - Main application (Port 8000)
- **postgres** - Database (Port 5432)
- **redis** - Cache/Sessions (Port 6379)
- **nginx** - Reverse proxy (Port 80/443)

### Monitoring (Optional)
- **prometheus** - Metrics collection (Port 9091)
- **grafana** - Dashboard (Port 3001)

### Ports & URLs
```
Application:  http://localhost:8000
API Docs:     http://localhost:8000/docs
Health:       http://localhost:8000/health
Grafana:      http://localhost:3001 (admin/admin)
Prometheus:   http://localhost:9091
```

---

## 🔄 Operations

### Deployment Commands

```bash
# Deploy to production
./scripts/deploy.sh production

# Check deployment status  
./scripts/deploy.sh status

# View application logs
./scripts/deploy.sh logs

# Restart services
./scripts/deploy.sh restart

# Stop all services
./scripts/deploy.sh stop
```

### Database Operations

```bash
# Access database shell
docker-compose exec postgres psql -U ordnungshub ordnungshub_prod

# Create database backup
./scripts/backup.sh

# Restore from backup
docker-compose exec -T postgres psql -U ordnungshub ordnungshub_prod < backup.sql
```

### Application Management

```bash
# Access application shell
docker-compose exec ordnungshub-backend bash

# Run database migrations
docker-compose exec ordnungshub-backend python -c "from src.backend.database.database import init_db; init_db()"

# Seed database with sample data
docker-compose exec ordnungshub-backend python -c "from src.backend.database.seed import seed_database; seed_database()"
```

---

## 🔍 Monitoring & Troubleshooting

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database connectivity
docker-compose exec postgres pg_isready -U ordnungshub

# Service status
docker-compose ps
```

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs ordnungshub-backend

# Check disk space
df -h

# Check memory usage
free -h
```

#### Database Connection Issues
```bash
# Verify database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U ordnungshub -c "SELECT 1;"
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# View slow queries (if enabled)
docker-compose exec postgres psql -U ordnungshub -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

---

## 📈 Scaling & Optimization

### Horizontal Scaling

```bash
# Scale backend instances
docker-compose up -d --scale ordnungshub-backend=3

# Update nginx upstream configuration
# Add load balancing to nginx.conf
```

### Performance Tuning

```bash
# Database optimization
# - Increase shared_buffers
# - Tune work_mem
# - Enable query optimization

# Application optimization  
# - Increase worker processes
# - Configure Redis caching
# - Enable CDN for static files
```

---

## 🔐 Security

### Production Security Checklist

- ✅ Change all default passwords
- ✅ Use strong SECRET_KEY and JWT_SECRET_KEY
- ✅ Enable HTTPS with valid SSL certificates
- ✅ Configure firewall rules
- ✅ Set up regular automated backups
- ✅ Enable security headers in nginx
- ✅ Configure rate limiting
- ✅ Set up monitoring and alerting
- ✅ Regular security updates

### Backup Strategy

```bash
# Automated daily backups (add to crontab)
0 2 * * * /path/to/ordnungshub/scripts/backup.sh

# Manual backup
./scripts/backup.sh

# Backup verification
tar -tzf backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## 🆘 Support & Maintenance

### Regular Maintenance

```bash
# Update application
git pull origin main
./scripts/deploy.sh production

# Clean up Docker resources
docker system prune -f

# Update base images
docker-compose pull
docker-compose up -d --force-recreate
```

### Log Management

```bash
# View logs by service
docker-compose logs ordnungshub-backend
docker-compose logs postgres
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f --tail=100 ordnungshub-backend

# Access log files directly
ls -la logs/
tail -f logs/ordnungshub.log
```

---

## 📞 Emergency Procedures

### Complete System Recovery

```bash
# 1. Stop all services
./scripts/deploy.sh stop

# 2. Restore from backup
tar -xzf backups/latest_backup.tar.gz
./scripts/restore.sh backup_directory

# 3. Redeploy
./scripts/deploy.sh production
```

### Database Recovery

```bash
# 1. Create new database
docker-compose exec postgres createdb -U ordnungshub ordnungshub_recovery

# 2. Restore from backup
docker-compose exec -T postgres psql -U ordnungshub ordnungshub_recovery < backup.sql

# 3. Switch database (update .env.production)
DATABASE_URL=postgresql://ordnungshub:password@postgres:5432/ordnungshub_recovery
```

---

## ✅ Production Checklist

Before going live:

- [ ] All secrets configured in `.env.secrets`
- [ ] SSL certificates installed and tested
- [ ] Domain DNS configured
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring dashboards set up
- [ ] Load testing completed
- [ ] Security scan performed
- [ ] Documentation reviewed
- [ ] Emergency procedures tested

---

**🎉 OrdnungsHub is now ready for production!**

For additional support, check the logs or contact the development team.