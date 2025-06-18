#!/bin/bash

# OrdnungsHub Development Startup Script
# Diagnoses and fixes common front/backend connection issues

echo "🚀 OrdnungsHub Development Environment Startup"
echo "================================================="

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
        return 1
    else
        echo "✅ Port $port is available"
        return 0
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    echo "🔄 Killing process on port $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    sleep 1
}

# Check Python installation
echo ""
echo "🐍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo "✅ $python_version found"
else
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Node.js installation
echo ""
echo "📦 Checking Node.js installation..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "✅ Node.js $node_version found"
else
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check required dependencies
echo ""
echo "🔍 Checking dependencies..."

# Check if Python requirements are installed
if python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "✅ Python dependencies installed"
else
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Check if Node modules are installed
if [ -d "node_modules" ]; then
    echo "✅ Node.js dependencies installed"
else
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Clean up ports
echo ""
echo "🧹 Cleaning up ports..."
kill_port 3000
kill_port 3001
kill_port 8000
kill_port 8001

sleep 2

# Check port availability
echo ""
echo "🔌 Checking port availability..."
check_port 3001 || kill_port 3001
check_port 8000 || kill_port 8000
check_port 8001 || kill_port 8001

# Start backend services
echo ""
echo "🔄 Starting backend services..."

# Start FastAPI backend
echo "📡 Starting FastAPI backend on port 8000..."
python3 src/backend/main.py &
FASTAPI_PID=$!

# Start mock backend as fallback
echo "🎭 Starting mock backend on port 8001..."
python3 mock_backend.py &
MOCK_PID=$!

# Wait for backends to start
echo "⏳ Waiting for backends to start..."
sleep 5

# Test backend connections
echo ""
echo "🩺 Testing backend connections..."

# Test FastAPI backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI backend responding on port 8000"
else
    echo "⚠️  FastAPI backend not responding on port 8000"
fi

# Test mock backend
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Mock backend responding on port 8001"
else
    echo "⚠️  Mock backend not responding on port 8001"
fi

# Start frontend
echo ""
echo "🎨 Starting frontend development server..."
echo "📱 Frontend will be available at http://localhost:3001"

# Start the development server
npm run dev:react &
FRONTEND_PID=$!

echo ""
echo "🎉 Development environment started!"
echo "=================================="
echo "📱 Frontend: http://localhost:3001"
echo "📡 FastAPI Backend: http://localhost:8000"
echo "🎭 Mock Backend: http://localhost:8001"
echo ""
echo "📊 Backend Status:"
echo "   - FastAPI: http://localhost:8000/health"
echo "   - Mock: http://localhost:8001/health"
echo ""
echo "⏹️  Press Ctrl+C to stop all services"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping development environment..."
    kill $FASTAPI_PID $MOCK_PID $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Handle Ctrl+C
trap cleanup SIGINT

# Wait for user to stop
wait
