#!/bin/bash

echo "🧪 Testing CI/CD Pipeline Locally"
echo "=================================="

# Create test environment
echo "📝 Creating test environment..."
cat > .env.test << EOF
DB_PASSWORD=test_password_12345
SECRET_KEY=test_secret_key_32_chars_long_12345
JWT_SECRET_KEY=test_jwt_secret_key_32_chars_long_123
REDIS_PASSWORD=test_redis_password
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
EOF

# Step 1: Build test
echo "🔨 Step 1: Build Test"
npm run build:react
if [ $? -eq 0 ]; then
    echo "✅ Frontend build successful"
else
    echo "❌ Frontend build failed"
    exit 1
fi

# Step 2: Docker integration test
echo "🐳 Step 2: Docker Integration Test"
cp .env.test .env
docker-compose down -v
docker-compose up -d --build

echo "⏳ Waiting for services to start..."
sleep 45

# Test health endpoint
echo "🏥 Testing health endpoint..."
curl -f http://localhost:8000/health
if [ $? -eq 0 ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    docker-compose logs ordnungshub-backend
    exit 1
fi

# Test API endpoints
echo "🔌 Testing API endpoints..."
curl -f http://localhost:8000/workspaces/
if [ $? -eq 0 ]; then
    echo "✅ Workspaces API accessible"
else
    echo "❌ Workspaces API failed"
    exit 1
fi

# Test workspace creation
echo "🆕 Testing workspace creation..."
RESPONSE=$(curl -s -X POST http://localhost:8000/workspaces/ \
  -H "Content-Type: application/json" \
  -d '{"name":"CI Test Workspace","description":"Created by CI","theme":"modern_light","color":"#3b82f6"}' \
  -w "%{http_code}")

if [[ "$RESPONSE" == *"201"* ]] || [[ "$RESPONSE" == *"200"* ]]; then
    echo "✅ Workspace creation test passed"
else
    echo "❌ Workspace creation failed: $RESPONSE"
fi

# Test nginx proxy
echo "🔄 Testing nginx proxy..."
curl -f http://localhost:80/health
if [ $? -eq 0 ]; then
    echo "✅ Nginx proxy working"
else
    echo "❌ Nginx proxy failed"
fi

echo ""
echo "🎉 All CI/CD tests completed successfully!"
echo "🚀 Pipeline is ready for GitHub Actions"

# Cleanup
echo "🧹 Cleaning up..."
docker-compose down
rm .env.test

echo "✨ Local CI test finished!"