# 🚂 Deploy OrdnungsHub to Railway

## Quick Deploy (5 minutes)

### Prerequisites
- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Deploy OrdnungsHub with improvements"
git push origin main
```

### Step 2: Deploy on Railway

1. **Go to [railway.app](https://railway.app)**
2. **Click "Start a New Project"**
3. **Choose "Deploy from GitHub repo"**
4. **Select your repository**
5. **Railway will auto-detect the configuration**

### Step 3: Add Services

Railway will automatically:
- ✅ Deploy your FastAPI backend
- ✅ Create a PostgreSQL database
- ✅ Set up Redis cache
- ✅ Configure environment variables

### Step 4: Set Environment Variables

Add these in Railway dashboard:
```env
# Security (generate new values!)
SECRET_KEY=your-generated-secret-key
JWT_SECRET_KEY=your-generated-jwt-key

# Database (auto-configured by Railway)
DATABASE_URL=${{POSTGRES.DATABASE_URL}}

# Redis (auto-configured by Railway)
REDIS_URL=${{REDIS.REDIS_URL}}

# API Keys (optional)
ANTHROPIC_API_KEY=your-key-if-needed
OPENAI_API_KEY=your-key-if-needed

# Features
ENABLE_METRICS=true
LOG_LEVEL=INFO
```

### Step 5: Deploy!

Railway will:
1. Build your Docker image
2. Deploy the backend
3. Set up HTTPS automatically
4. Provide a URL like: `ordnungshub.up.railway.app`

### 🎉 That's it! Your app is live!

## Access Your Deployed App

- **API**: `https://your-app.up.railway.app/`
- **Docs**: `https://your-app.up.railway.app/docs`
- **Health**: `https://your-app.up.railway.app/health`

## Monitoring

Railway provides:
- Deployment logs
- Resource usage
- Automatic scaling
- Zero-downtime deploys