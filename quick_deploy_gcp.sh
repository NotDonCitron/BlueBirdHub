#!/bin/bash

# 🚀 Quick Deploy OrdnungsHub to Google Cloud FREE
# This script helps you deploy your app to Google Cloud's free tier

set -e

echo "🆓 ORDNUNGSHUB → GOOGLE CLOUD FREE DEPLOYMENT"
echo "=============================================="
echo ""

# Step 1: Install gcloud CLI
echo "📥 Step 1: Installing Google Cloud CLI..."
if ! command -v gcloud &> /dev/null; then
    echo "Installing gcloud CLI..."
    
    # Download and install gcloud
    curl https://sdk.cloud.google.com | bash
    
    # Reload shell
    exec -l $SHELL
    
    echo "✅ gcloud CLI installed!"
else
    echo "✅ gcloud CLI already installed"
fi

# Step 2: Login and setup
echo ""
echo "🔑 Step 2: Login to Google Cloud..."
echo "This will open your browser for authentication..."
gcloud auth login

echo ""
echo "🏗️  Step 3: Initialize project..."
echo "Choose 'Create a new project' and name it 'ordnungshub-free'"
gcloud init

# Step 4: Enable APIs
echo ""
echo "⚙️  Step 4: Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  containerregistry.googleapis.com

echo "✅ APIs enabled!"

# Step 5: Build and deploy
echo ""
echo "🐳 Step 5: Building Docker image in cloud..."
echo "This might take 2-3 minutes..."

gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/ordnungshub:latest

echo ""
echo "🚀 Step 6: Deploying to Cloud Run..."

gcloud run deploy ordnungshub \
  --image gcr.io/$(gcloud config get-value project)/ordnungshub:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5 \
  --set-env-vars "ENABLE_METRICS=true,LOG_LEVEL=INFO,PYTHON_ENV=production"

# Get the URL
APP_URL=$(gcloud run services describe ordnungshub --region=us-central1 --format="value(status.url)")

echo ""
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "========================"
echo ""
echo "🌐 Your OrdnungsHub is live at:"
echo "📱 Main App: $APP_URL"
echo "📚 API Docs: $APP_URL/docs"
echo "❤️  Health: $APP_URL/health"
echo "📊 Metrics: $APP_URL/metrics"
echo ""
echo "💡 Next steps:"
echo "1. Visit $APP_URL/docs to see your API"
echo "2. Set up database (optional - see DEPLOY_GOOGLE_FREE.md)"
echo "3. Configure custom domain (optional)"
echo ""
echo "💰 Cost: FREE for 2M requests/month!"
echo ""
echo "🎊 Congratulations! Your app is live on Google Cloud!"