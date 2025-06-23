#!/bin/bash

echo "🛑 Stopping OrdnungsHub Debug Session"
echo "====================================="

cd "/mnt/c/Users/pasca/BlueBirdHub"

# Read PIDs if available
if [ -f "logs/debug-session/pids.txt" ]; then
    PIDS=$(cat logs/debug-session/pids.txt)
    IFS=',' read -ra PID_ARRAY <<< "$PIDS"
    
    for pid in "${PID_ARRAY[@]}"; do
        if [ ! -z "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "Stopping process $pid"
            kill "$pid" 2>/dev/null || true
        fi
    done
fi

# Kill by name as backup
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true  
pkill -f "electron" 2>/dev/null || true
pkill -f "node.*debug" 2>/dev/null || true

# Kill ports as final cleanup
npm run predev 2>/dev/null || true

echo "✅ All services stopped"
echo "📝 Logs preserved in: logs/debug-session/"