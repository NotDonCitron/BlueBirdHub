@echo off
setlocal EnableDelayedExpansion

REM OrdnungsHub Quick Start - Neue sichere Architektur
title OrdnungsHub - Sichere API-Architektur

echo 🚀 OrdnungsHub - Neue sichere API-Architektur
echo =============================================

REM 1. Umgebung prüfen
echo 🔍 Prüfe Umgebung...
if not exist ".env" (
    echo ❌ .env Datei fehlt!
    echo Kopiere .env.example zu .env und konfiguriere die Werte.
    pause
    exit /b 1
)

REM 2. Environment-Variablen anzeigen
echo ✅ Environment konfiguriert
echo    API_URL: http://localhost:8000
echo    FALLBACK_URL: http://localhost:8001

REM 3. Ports bereinigen
echo 🧹 Bereinige Ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1

REM 4. Dependencies prüfen
echo 📦 Prüfe Dependencies...
if not exist "node_modules" (
    echo Installiere Node.js Dependencies...
    npm install
    if errorlevel 1 (
        echo ❌ npm install fehlgeschlagen!
        pause
        exit /b 1
    )
)

echo ✅ Dependencies OK

REM 5. Services starten
echo 🚀 Starte Services...

REM FastAPI Backend
echo 📡 Starte FastAPI Backend (Port 8000)...
start "FastAPI Backend" /min py src/backend/main.py

REM Mock Backend mit neuen Automation-Endpunkten
echo 🎭 Starte Mock Backend (Port 8001)...
start "Mock Backend" /min py mock_backend.py

REM Warte auf Backends
echo ⏳ Warte auf Backend-Start...
timeout /t 5 >nul

REM 6. Teste neue API-Architektur
echo 🔍 Teste neue API-Architektur...
py test-api-cors.py
if errorlevel 1 (
    echo ❌ API-Tests fehlgeschlagen!
    pause
    exit /b 1
)

echo ✅ API-Tests bestanden!

REM 7. Frontend starten
echo 🎨 Starte Frontend (Port 3001)...
start "Frontend Dev Server" npm run dev:react

REM Warte kurz für Frontend-Start
timeout /t 3 >nul

echo.
echo 🎉 OrdnungsHub gestartet mit neuer sicherer Architektur!
echo =============================================
echo 📱 Frontend:     http://localhost:3001
echo 📡 FastAPI:      http://localhost:8000  
echo 🎭 Mock Backend: http://localhost:8001
echo.
echo 🛡️ Schutzmaßnahmen aktiv:
echo    ✅ Frontend-Self-Call-Prevention
echo    ✅ Automatische Backend-Auswahl
echo    ✅ Request-Monitoring (Development)
echo    ✅ CORS-Probleme behoben
echo.
echo 🔧 Debug-Tools (Browser-Konsole):
echo    - window.apiManager
echo    - window.debugApi
echo    - window.requestInterceptor
echo.
echo 🌐 Öffne http://localhost:3001 im Browser
echo.
echo ⏹️  Drücke eine beliebige Taste zum Beenden
echo    (Dies stoppt alle Services)

pause >nul

REM Cleanup beim Beenden
echo.
echo 🛑 Stoppe alle Services...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1

echo ✅ Alle Services gestoppt
echo 👋 Auf Wiedersehen!
timeout /t 2 >nul
