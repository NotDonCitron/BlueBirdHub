# OrdnungsHub Deployment Guide

This guide covers multiple deployment options for the OrdnungsHub application.

## 🚀 Quick Start (Windows Local Development)

**Prerequisites:**
- Python 3.11+ ([Download](https://python.org))
- Node.js 18+ ([Download](https://nodejs.org))

**1-Click Setup:**
```cmd
deploy-windows.bat
```

**Start Application:**
```cmd
start-app.bat
```

Access your app at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🐳 Docker Deployment (Recommended for Production)

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available

### Setup
1. **Create Environment File:**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with your settings
   ```

2. **Configure Security Keys:**
   ```bash
   # Generate secure keys (Linux/Mac)
   openssl rand -hex 32  # Use for SECRET_KEY
   openssl rand -hex 32  # Use for JWT_SECRET_KEY
   
   # Windows PowerShell
   [System.Web.Security.Membership]::GeneratePassword(32, 0)
   ```

3. **Deploy:**
   ```bash
   docker-compose --env-file .env.production up -d
   ```

### Services Included
- **Backend API** (Port 8000)
- **Frontend** (Port 3002)
- **PostgreSQL Database** (Port 5432)
- **Redis Cache** (Port 6380)
- **Nginx Reverse Proxy** (Port 80/443)
- **Monitoring** (Optional - Prometheus + Grafana)

### Management Commands
```bash
# View logs
docker-compose logs -f ordnungshub-backend

# Stop services
docker-compose down

# Update application
docker-compose down
docker-compose build
docker-compose up -d
```

---

## ☁️ Cloud Deployments

### Google Cloud App Engine

1. **Install Google Cloud SDK**
2. **Configure app.yaml** (already included)
3. **Deploy:**
   ```bash
   gcloud app deploy
   ```

### Netlify (Serverless)

1. **Connect GitHub repository**
2. **Build settings:**
   - Build command: `npm run build`
   - Publish directory: `packages/web/dist`
3. **Function endpoint:** `/netlify/functions/api`

### Railway/Render/Heroku

1. **Connect repository**
2. **Environment variables:** Copy from `.env.production`
3. **Build command:** `pip install -r requirements.txt && cd packages/web && npm install && npm run build`
4. **Start command:** `uvicorn src.backend.main:app --host 0.0.0.0 --port $PORT`

---

## 🔧 Manual Server Setup

### Prerequisites
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.11+, Node.js 18+
- PostgreSQL 13+, Redis 6+
- Nginx

### Installation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.11 python3.11-venv python3-pip nodejs npm postgresql redis-server nginx -y

# Create application user
sudo useradd -m -s /bin/bash ordnungshub

# Clone repository
sudo -u ordnungshub git clone <your-repo> /home/ordnungshub/app
cd /home/ordnungshub/app

# Setup Python environment
sudo -u ordnungshub python3.11 -m venv venv
sudo -u ordnungshub venv/bin/pip install -r requirements.txt

# Setup frontend
cd packages/web
sudo -u ordnungshub npm install
sudo -u ordnungshub npm run build
cd ../..

# Configure database
sudo -u postgres createdb ordnungshub_prod
sudo -u postgres createuser ordnungshub
sudo -u postgres psql -c "GRANT ALL ON DATABASE ordnungshub_prod TO ordnungshub;"

# Setup systemd services
sudo cp ordnungshub-backend.service /etc/systemd/system/
sudo cp ordnungshub-frontend.service /etc/systemd/system/
sudo systemctl enable ordnungshub-backend ordnungshub-frontend
sudo systemctl start ordnungshub-backend ordnungshub-frontend

# Configure Nginx
sudo cp nginx/nginx.conf /etc/nginx/sites-available/ordnungshub
sudo ln -s /etc/nginx/sites-available/ordnungshub /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## 🔐 Security Configuration

### Environment Variables

**Required for all deployments:**
```env
SECRET_KEY=your_32_character_secret_key
JWT_SECRET_KEY=your_32_character_jwt_key
DATABASE_URL=your_database_connection_string
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**AI Integration (Optional):**
```env
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
```

### SSL/HTTPS Setup

**For Nginx (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

**For Docker with Traefik:**
```yaml
# Add to docker-compose.yml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.ordnungshub.rule=Host(`yourdomain.com`)"
  - "traefik.http.routers.ordnungshub.tls.certresolver=letsencrypt"
```

---

## 📊 Monitoring & Maintenance

### Health Checks
- **Backend:** http://your-domain/health
- **API Status:** http://your-domain/docs

### Log Locations
- **Docker:** `docker-compose logs ordnungshub-backend`
- **Local:** `logs/ordnungshub.log`
- **System:** `/var/log/ordnungshub/`

### Backup Strategy
```bash
# Database backup (PostgreSQL)
pg_dump ordnungshub_prod > backup_$(date +%Y%m%d).sql

# File backup
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/

# Docker volumes backup
docker run --rm -v ordnungshub_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

**2. Database connection errors:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
# Restart if needed
sudo systemctl restart postgresql
```

**3. Permission errors (Linux):**
```bash
# Fix file permissions
sudo chown -R ordnungshub:ordnungshub /path/to/app
sudo chmod -R 755 /path/to/app
```

**4. Frontend build fails:**
```bash
# Clear cache and reinstall
cd packages/web
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Performance Optimization

**1. Database indexes:**
```sql
-- Add indexes for common queries
CREATE INDEX idx_workspace_user_id ON workspaces(user_id);
CREATE INDEX idx_tasks_workspace_id ON tasks(workspace_id);
```

**2. Redis caching:**
```env
# Enable Redis for session storage
REDIS_URL=redis://localhost:6379
ENABLE_CACHING=true
```

**3. Nginx caching:**
```nginx
# Add to nginx.conf
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 📈 Scaling

### Horizontal Scaling
- Use load balancer (HAProxy/Nginx)
- Deploy multiple backend instances
- Use PostgreSQL read replicas
- Implement Redis Cluster

### Vertical Scaling
- Increase CPU/RAM for containers
- Optimize database queries
- Enable connection pooling
- Use CDN for static assets

---

## 📞 Support

For deployment issues:
1. Check logs first
2. Review this documentation
3. Search existing GitHub issues
4. Open new issue with deployment details

**Happy Deploying! 🚀** 