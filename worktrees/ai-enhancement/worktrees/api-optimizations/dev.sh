#!/bin/bash
# OrdnungsHub Development Starter
# Startet Frontend und Backend für Development

set -e

echo "🚀 Starting OrdnungsHub Development Environment"
echo "================================================"

# Kill existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "webpack" 2>/dev/null || true
sleep 2

# Start test backend
echo "🔧 Starting test backend..."
python3 test_backend.py &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Test backend
if curl -s http://127.0.0.1:8001/ > /dev/null; then
    echo "✅ Backend is running on http://127.0.0.1:8001"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend
echo "🌐 Starting frontend..."
npm run dev:react &
FRONTEND_PID=$!

echo ""
echo "🎉 Development environment is ready!"
echo "Frontend: http://localhost:3001"
echo "Backend:  http://127.0.0.1:8001"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping development environment..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    pkill -f "uvicorn" 2>/dev/null || true
    pkill -f "webpack" 2>/dev/null || true
    echo "✅ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait