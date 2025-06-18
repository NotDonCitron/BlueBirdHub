# 🆓 Deploy OrdnungsHub to Google Cloud FREE

## Complete Free Tier Deployment Guide

### 🎁 What You Get FREE
- **$300 credit** for 3 months (enough for months of usage!)
- **Cloud Run**: 2 million requests/month FREE forever
- **Cloud SQL**: db-f1-micro PostgreSQL instance
- **Container Registry**: 0.5GB storage FREE
- **Networking**: 1GB egress/month FREE
- **Cloud Build**: 120 build-minutes/day FREE

---

## Step 1: Set Up Google Cloud Account

### 1.1 Create Account
1. Go to [cloud.google.com](https://cloud.google.com)
2. Click **"Get started for free"**
3. Sign in with Google account
4. Enter billing info (verification only - you won't be charged)
5. **Get $300 FREE credits!**

### 1.2 Install gcloud CLI
```bash
# Linux/WSL
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# macOS
brew install --cask google-cloud-sdk

# Windows
# Download from: https://cloud.google.com/sdk/docs/install

# Verify installation
gcloud version
```

### 1.3 Login and Initialize
```bash
# Login to your account
gcloud auth login

# Set up default configuration
gcloud init

# Choose or create project: ordnungshub-free
# Choose default region: us-central1 (free tier eligible)
```

---

## Step 2: Create Project and Enable APIs

```bash
# Create new project
gcloud projects create ordnungshub-free --name="OrdnungsHub Free"

# Set as current project
gcloud config set project ordnungshub-free

# Enable required APIs (FREE)
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  containerregistry.googleapis.com
```

---

## Step 3: Build and Deploy to Cloud Run (FREE!)

### 3.1 Build Image with Cloud Build (FREE 120 min/day)
```bash
# Build directly in the cloud (no local Docker needed!)
gcloud builds submit --tag gcr.io/ordnungshub-free/ordnungshub:latest

# This will:
# 1. Upload your code
# 2. Build Docker image in cloud
# 3. Store in Container Registry
# 4. All for FREE!
```

### 3.2 Deploy to Cloud Run (2M requests/month FREE!)
```bash
gcloud run deploy ordnungshub \
  --image gcr.io/ordnungshub-free/ordnungshub:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 3 \
  --set-env-vars "ENABLE_METRICS=true,LOG_LEVEL=INFO,PYTHON_ENV=production"

# Get your live URL!
echo "🎉 Your app is live at:"
gcloud run services describe ordnungshub --region=us-central1 --format="value(status.url)"
```

---

## Step 4: Set Up FREE Database

### Option A: Cloud SQL Free Tier
```bash
# Create FREE PostgreSQL instance (db-f1-micro)
gcloud sql instances create ordnungshub-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-size=10GB \
  --storage-type=HDD

# Create database
gcloud sql databases create ordnungshub \
  --instance=ordnungshub-db

# Create user
gcloud sql users create ordnungshub \
  --instance=ordnungshub-db \
  --password=SecurePassword123!

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe ordnungshub-db --format="value(connectionName)")

# Connect Cloud Run to database
gcloud run services update ordnungshub \
  --add-cloudsql-instances=$CONNECTION_NAME \
  --set-env-vars DATABASE_URL="postgresql://ordnungshub:SecurePassword123!@/ordnungshub?host=/cloudsql/$CONNECTION_NAME"
```

### Option B: Free External Database (Alternative)
```bash
# Use free PostgreSQL from Supabase, Neon, or PlanetScale
# These offer generous free tiers

# Example with Supabase (free 500MB):
# 1. Go to supabase.com
# 2. Create free project
# 3. Get database URL
# 4. Update Cloud Run:

gcloud run services update ordnungshub \
  --set-env-vars DATABASE_URL="postgresql://user:pass@db.supabase.co:5432/postgres"
```

---

## Step 5: Add Redis Cache (FREE options)

### Option A: Memorystore Basic (Paid but within free credits)
```bash
# Create small Redis instance
gcloud redis instances create ordnungshub-cache \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=basic

# Create VPC connector for Cloud Run
gcloud compute networks vpc-access connectors create ordnungshub-connector \
  --region=us-central1 \
  --subnet=default \
  --range=10.8.0.0/28

# Connect Cloud Run
REDIS_HOST=$(gcloud redis instances describe ordnungshub-cache --region=us-central1 --format="value(host)")

gcloud run services update ordnungshub \
  --vpc-connector=ordnungshub-connector \
  --set-env-vars REDIS_URL="redis://$REDIS_HOST:6379"
```

### Option B: Free External Redis
```bash
# Use free Redis from Railway, Upstash, or Redis Cloud
# Example with Upstash (10K commands/day free):

# 1. Go to upstash.com
# 2. Create free Redis database
# 3. Get Redis URL
# 4. Update Cloud Run:

gcloud run services update ordnungshub \
  --set-env-vars REDIS_URL="redis://user:pass@redis.upstash.io:port"
```

---

## Step 6: Set Environment Variables

```bash
# Generate secure keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Update Cloud Run with all environment variables
gcloud run services update ordnungshub \
  --set-env-vars "SECRET_KEY=$SECRET_KEY,JWT_SECRET_KEY=$JWT_SECRET,CORS_ORIGINS=https://ordnungshub-free.app,ENABLE_METRICS=true"
```

---

## Step 7: Custom Domain (FREE)

```bash
# Map your own domain (free with Google Domains or any registrar)
gcloud run domain-mappings create \
  --service ordnungshub \
  --domain your-domain.com \
  --region us-central1

# Get DNS records to configure
gcloud run domain-mappings describe \
  --domain your-domain.com \
  --region us-central1
```

---

## 🎉 Your FREE App is Live!

### Access Your App
```bash
# Get your app URL
APP_URL=$(gcloud run services describe ordnungshub --region=us-central1 --format="value(status.url)")

echo "🌐 Your OrdnungsHub is live at:"
echo "📱 Main App: $APP_URL"
echo "📚 API Docs: $APP_URL/docs"
echo "❤️  Health: $APP_URL/health"
echo "📊 Metrics: $APP_URL/metrics"
```

### Example URLs:
- **Main App**: https://ordnungshub-xxx-uc.a.run.app
- **API Docs**: https://ordnungshub-xxx-uc.a.run.app/docs
- **Health Check**: https://ordnungshub-xxx-uc.a.run.app/health

---

## 💰 Cost Breakdown (FREE!)

### What's Actually FREE:
- **Cloud Run**: 2M requests/month (your app can handle ~65K daily users!)
- **Cloud Build**: 120 build minutes/day
- **Container Registry**: 0.5GB storage
- **Networking**: 1GB egress/month
- **Logging**: 50GB/month

### What Uses Your $300 Credits:
- **Cloud SQL**: ~$10/month (covered by credits for 30 months!)
- **Memorystore Redis**: ~$25/month (covered by credits for 12 months!)

### Total Real Cost: $0 for many months! 🎉

---

## Monitoring and Optimization

### View Logs (FREE)
```bash
# View application logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ordnungshub" --limit 50

# Monitor costs
gcloud billing accounts list
gcloud billing budgets list --billing-account=BILLING_ACCOUNT_ID
```

### Auto-scaling Configuration (FREE)
```bash
# Update scaling settings
gcloud run services update ordnungshub \
  --concurrency 100 \
  --max-instances 10 \
  --cpu 1 \
  --memory 512Mi
```

---

## 🔧 Troubleshooting

### Common Issues:
1. **Build fails**: Check Dockerfile syntax
2. **Database connection**: Verify Cloud SQL proxy setup
3. **Memory issues**: Increase to 1Gi if needed
4. **Cold starts**: Enable minimum instances if needed

### Helpful Commands:
```bash
# Check service status
gcloud run services describe ordnungshub --region=us-central1

# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit=20

# Update environment variables
gcloud run services update ordnungshub --set-env-vars NEW_VAR=value
```

---

## 🎯 Next Steps

1. ✅ **Test all endpoints**
2. ✅ **Set up monitoring alerts**
3. ✅ **Configure custom domain**
4. ✅ **Add SSL certificate** (automatic with Cloud Run)
5. ✅ **Set up CI/CD** with GitHub Actions

**Your OrdnungsHub is now running on enterprise-grade infrastructure for FREE!** 🚀