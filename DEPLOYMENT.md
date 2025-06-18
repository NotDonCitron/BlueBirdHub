# 🚀 OrdnungsHub Deployment Guide

This guide shows how to deploy OrdnungsHub to various cloud platforms.

## ☁️ Deployment Options

### 1. Railway (Recommended - Easy)

Railway is perfect for FastAPI apps with zero configuration needed.

**Steps:**

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select this repository
5. Railway will automatically detect it's a Python app and deploy!

**Files included:**

- `railway.json` - Railway configuration
- `Procfile` - Process definition
- `requirements.txt` - Python dependencies

### 2. Vercel (Fast & Free)

**Steps:**

1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Framework preset: "Other"
4. Build command: `pip install -r requirements.txt`
5. Output directory: `.`
6. Install command: `pip install -r requirements.txt`

### 3. Heroku

**Steps:**

1. Install Heroku CLI
2. Run these commands:

```bash
heroku create ordnungshub-demo
git push heroku main
```

### 4. Render

**Steps:**

1. Go to [render.com](https://render.com)
2. Connect GitHub repository
3. Select "Web Service"
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn src.backend.main:app --host 0.0.0.0 --port $PORT`

## 🔧 Configuration

The app is configured to work in cloud environments with:
- ✅ Mock data for Taskmaster when not available locally
- ✅ CORS enabled for web access
- ✅ Environment detection for cloud vs local
- ✅ Minimal dependencies for fast deployment
- ✅ Health check endpoints

## 🌐 Frontend Demo

The `index.html` file provides a complete web interface that:
- Auto-detects the API URL (cloud or local)
- Tests all major features interactively
- Shows real-time API responses
- Works with any deployment platform

## 📁 Key Files

- `src/backend/main.py` - FastAPI application
- `requirements.txt` - Python dependencies (streamlined for cloud)
- `Procfile` - Process definition for Heroku/Railway
- `railway.json` - Railway-specific configuration
- `runtime.txt` - Python version specification
- `index.html` - Web demo interface

## 🧪 Testing Deployment

After deployment, your API will be available at endpoints like:

- `GET /` - Basic info
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /tasks/taskmaster/all` - Task management

## 🎯 Demo Features

Once deployed, users can test:

1. **Dashboard Analytics** - Real-time statistics
2. **Taskmaster AI** - Task management with mock data
3. **Workspace Management** - AI-powered content assignment
4. **AI Services** - Text analysis and suggestions

The deployment includes comprehensive mock data so all features work even without local Taskmaster setup.