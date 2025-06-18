@echo off
title OrdnungsHub Development Environment
color 0A

echo =========================================
echo     OrdnungsHub Development Startup
echo =========================================
echo.

:: Check if we're in the right directory
if not exist "package.json" (
    echo ❌ package.json nicht gefunden!
    echo Bitte starten Sie das Script im Projektverzeichnis.
    pause
    exit /b 1
)

echo ✅ Projektverzeichnis gefunden
echo.

:: Clean up any existing processes
echo 🧹 Bereinige Ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do (
    echo   Beende Prozess auf Port 3001 (PID %%a)
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo   Beende Prozess auf Port 8000 (PID %%a)
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    echo   Beende Prozess auf Port 8001 (PID %%a)
    taskkill /F /PID %%a >nul 2>&1
)

echo ✅ Ports bereinigt
echo.

:: Check dependencies
echo 📦 Prüfe Dependencies...
if not exist "node_modules" (
    echo   Node.js Dependencies werden installiert...
    npm install
    if errorlevel 1 (
        echo ❌ npm install fehlgeschlagen!
        pause
        exit /b 1
    )
)
echo ✅ Node.js Dependencies OK
echo.

:: Start backends
echo 🚀 Starte Backend Services...

echo   📡 Starte FastAPI Backend (Port 8000)...
start "FastAPI Backend" /min cmd /c "cd /d %CD% && py src/backend/main.py"

echo   🎭 Starte Mock Backend (Port 8001)...
start "Mock Backend" /min cmd /c "cd /d %CD% && py mock_backend.py"

echo   ⏳ Warte auf Backend-Start...
timeout /t 5 >nul

:: Test backends
echo 🔍 Teste Backend-Verbindungen...
ping -n 2 127.0.0.1 >nul
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  FastAPI Backend nicht erreichbar
) else (
    echo   ✅ FastAPI Backend läuft
)

curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  Mock Backend nicht erreichbar
) else (
    echo   ✅ Mock Backend läuft
)

echo.

:: Start frontend
echo 🎨 Starte Frontend Development Server...
echo   📱 Frontend wird verfügbar unter: http://localhost:3001
echo.

start "Frontend Dev Server" cmd /c "cd /d %CD% && npm run dev:react"

:: Wait a moment for frontend to start
timeout /t 3 >nul

echo.
echo =========================================
echo     🎉 Development Environment Ready! 
echo =========================================
echo.
echo 📱 Frontend:     http://localhost:3001
echo 📡 FastAPI:      http://localhost:8000
echo 🎭 Mock Backend: http://localhost:8001
echo 🔍 Test Tool:    connection-test.html
echo.
echo ℹ️  Öffnen Sie connection-test.html um die 
echo    Verbindungen zu testen.
echo.
echo ⏹️  Drücken Sie eine beliebige Taste zum Beenden
echo    (Dies stoppt alle Services)

pause >nul

:: Cleanup on exit
echo.
echo 🛑 Stoppe alle Services...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1

echo ✅ Alle Services gestoppt
echo 👋 Auf Wiedersehen!
timeout /t 2 >nul
