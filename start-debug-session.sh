#!/bin/bash

echo "🚀 Starting Complete OrdnungsHub Debug Session"
echo "============================================="

# Set working directory
cd "/mnt/c/Users/pasca/BlueBirdHub"

# Create logs directory
mkdir -p logs/debug-session

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Start backend in background
log_with_timestamp "Starting Backend (FastAPI)..."
npm run dev:backend > logs/debug-session/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 5
log_with_timestamp "Backend started, waiting for health check..."

# Check backend health
for i in {1..10}; do
    if curl -s http://127.0.0.1:8001/health > /dev/null; then
        log_with_timestamp "✅ Backend is healthy!"
        break
    else
        log_with_timestamp "⏳ Waiting for backend... (attempt $i/10)"
        sleep 2
    fi
done

# Start frontend in background
log_with_timestamp "Starting Frontend (Vite)..."
npm run dev:vite > logs/debug-session/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 8
log_with_timestamp "Frontend started, checking availability..."

# Check frontend health
for i in {1..15}; do
    if curl -s -I http://localhost:3002 > /dev/null; then
        log_with_timestamp "✅ Frontend is healthy!"
        break
    else
        log_with_timestamp "⏳ Waiting for frontend... (attempt $i/15)"
        sleep 2
    fi
done

# Start MCP Debug Server
log_with_timestamp "Starting MCP Debug Server..."
cd mcp-servers/localhost-debug-mcp
npm start > ../../logs/debug-session/mcp-debug.log 2>&1 &
MCP_PID=$!
cd ../..
echo "MCP Debug Server PID: $MCP_PID"

# Wait for MCP server
sleep 3
log_with_timestamp "MCP Debug Server started"

# Start Electron (optional)
log_with_timestamp "Starting Electron Desktop App..."
npm run dev:electron > logs/debug-session/electron.log 2>&1 &
ELECTRON_PID=$!
echo "Electron PID: $ELECTRON_PID"

# Save PIDs for cleanup
echo "$BACKEND_PID,$FRONTEND_PID,$MCP_PID,$ELECTRON_PID" > logs/debug-session/pids.txt

log_with_timestamp "🎉 All services started!"
echo ""
echo "📊 Service URLs:"
echo "  Frontend:    http://localhost:3002"
echo "  Backend API: http://127.0.0.1:8001/docs"
echo "  MCP Debug:   http://localhost:3004"
echo "  Debug Dashboard: file://$(pwd)/debug-session.html"
echo ""
echo "📝 Logs available in: logs/debug-session/"
echo "🛑 To stop all services: ./stop-debug-session.sh"

# Keep script running and show live logs
log_with_timestamp "Monitoring services... (Ctrl+C to stop)"
tail -f logs/debug-session/*.log