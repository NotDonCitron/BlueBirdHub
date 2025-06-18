# 🌊 Deploy OrdnungsHub to DigitalOcean

## Complete Docker Deployment Guide

### Prerequisites
- DigitalOcean account ([Sign up with $200 credit](https://www.digitalocean.com/))
- GitHub repository with your code
- Docker Hub account (free)

---

## Step 1: Prepare Your Docker Image

### 1.1 Create Production Dockerfile (already done ✅)
Your `Dockerfile` is production-ready!

### 1.2 Build and Test Locally
```bash
# Build production image
docker build -t ordnungshub:latest .

# Test it works
docker run -p 8000:8000 ordnungshub:latest
```

---

## Step 2: Push to Docker Hub

### 2.1 Create Docker Hub Repository
1. Go to [hub.docker.com](https://hub.docker.com)
2. Create repository named `ordnungshub`

### 2.2 Tag and Push Image
```bash
# Login to Docker Hub
docker login

# Tag your image (replace YOUR_USERNAME)
docker tag ordnungshub:latest YOUR_USERNAME/ordnungshub:latest

# Push to Docker Hub
docker push YOUR_USERNAME/ordnungshub:latest
```

---

## Step 3: Deploy on DigitalOcean

### Option A: App Platform (Easiest)

1. **Go to DigitalOcean App Platform**
   - Navigate to: Create → Apps

2. **Create New App**
   - Source: Docker Hub
   - Repository: `YOUR_USERNAME/ordnungshub`
   - Tag: `latest`

3. **Configure Resources**
   ```yaml
   name: ordnungshub
   services:
   - name: backend
     image:
       registry_type: DOCKER_HUB
       registry: YOUR_USERNAME
       repository: ordnungshub
       tag: latest
     http_port: 8000
     health_check:
       http_path: /health
     envs:
     - key: DATABASE_URL
       scope: RUN_TIME
       value: ${db.DATABASE_URL}
     - key: REDIS_URL
       scope: RUN_TIME
       value: ${redis.REDIS_URL}
   
   databases:
   - name: db
     engine: PG
     version: "15"
   
   - name: redis
     engine: REDIS
     version: "7"
   ```

### Option B: Droplet with Docker Compose

1. **Create Droplet**
   - Choose Docker marketplace image
   - Size: $20/month (2GB RAM minimum)
   - Region: Choose closest to users

2. **SSH and Deploy**
   ```bash
   # SSH into droplet
   ssh root@your-droplet-ip

   # Clone your repository
   git clone https://github.com/YOUR_USERNAME/ordnungshub.git
   cd ordnungshub

   # Create .env file
   nano .env
   # Add your environment variables

   # Start with Docker Compose
   docker-compose up -d
   ```

3. **Set Up Domain (Optional)**
   ```bash
   # Install Nginx
   apt update && apt install nginx certbot python3-certbot-nginx

   # Configure Nginx
   nano /etc/nginx/sites-available/ordnungshub
   ```

   ```nginx
   server {
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

   ```bash
   # Enable site
   ln -s /etc/nginx/sites-available/ordnungshub /etc/nginx/sites-enabled/
   nginx -t && systemctl reload nginx

   # Get SSL certificate
   certbot --nginx -d yourdomain.com
   ```

---

## Step 4: Environment Variables

### Required Environment Variables
```env
# Database (auto-provided by DigitalOcean)
DATABASE_URL=${db.DATABASE_URL}

# Redis (auto-provided by DigitalOcean)
REDIS_URL=${redis.REDIS_URL}
REDIS_PASSWORD=${redis.PASSWORD}

# Security
SECRET_KEY=generate-strong-secret-key
JWT_SECRET_KEY=generate-another-secret

# Features
ENABLE_METRICS=true
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com

# Optional API Keys
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
```

### Generate Secret Keys
```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Step 5: Monitor and Scale

### View Logs
```bash
# App Platform
doctl apps logs YOUR_APP_ID

# Docker Compose
docker-compose logs -f
```

### Scale Resources
- App Platform: Use dashboard to adjust
- Droplet: Resize or add load balancer

### Set Up Monitoring
1. Enable DigitalOcean monitoring
2. Access Prometheus metrics at `/metrics`
3. Optional: Set up Grafana dashboard

---

## 🎉 Your App is Live!

### Access URLs
- **API**: `https://your-app.ondigitalocean.app/`
- **Docs**: `https://your-app.ondigitalocean.app/docs`
- **Health**: `https://your-app.ondigitalocean.app/health`
- **Metrics**: `https://your-app.ondigitalocean.app/metrics`

### Next Steps
1. ✅ Test all endpoints
2. ✅ Set up monitoring alerts
3. ✅ Configure backups
4. ✅ Add custom domain
5. ✅ Enable auto-scaling

---

## Troubleshooting

### Common Issues

1. **Container won't start**
   - Check logs: `docker logs container-name`
   - Verify environment variables

2. **Database connection fails**
   - Ensure DATABASE_URL is correct
   - Check network connectivity

3. **High memory usage**
   - Scale to larger instance
   - Optimize Python workers

### Support
- DigitalOcean Support: 24/7 available
- Community: digitalocean.com/community