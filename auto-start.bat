@echo off
echo Starting OrdnungsHub with automatic fixes...


echo Cleaning up ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1

echo Starting services...
start "FastAPI Backend" /min py src/backend/main.py
start "Mock Backend" /min py mock_backend.py
timeout /t 3 >nul
start "Frontend" npm run dev:react

echo All services started!
pause
