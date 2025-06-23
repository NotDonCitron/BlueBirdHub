@echo off
echo.
echo =====================================================
echo    Starting Complete OrdnungsHub Application
echo =====================================================
echo.

REM Check if .env file exists
if not exist .env (
    echo ⚠️  WARNING: .env file not found!
    echo Creating basic .env file...
    echo NODE_ENV=development > .env
    echo PYTHON_ENV=development >> .env
    echo DATABASE_URL=sqlite:///./data/ordnungshub.db >> .env
    echo LOG_LEVEL=INFO >> .env
    echo CORS_ORIGINS=http://localhost:3002,http://localhost:3001,http://localhost:3000 >> .env
    echo ✅ Basic .env file created. You can add API keys later.
    echo.
)

REM Start backend in a new window
echo Starting backend server...
start "OrdnungsHub Backend" cmd /k "start-backend.bat"

REM Wait a few seconds for backend to start
echo Waiting for backend to initialize...
timeout /t 8 /nobreak >nul

REM Start frontend in a new window
echo Starting frontend server...
start "OrdnungsHub Frontend" cmd /k "start-frontend.bat"

REM Wait for frontend to start
echo Waiting for frontend to initialize...
timeout /t 5 /nobreak >nul

echo.
echo =====================================================
echo    OrdnungsHub Started Successfully!
echo =====================================================
echo.
echo Two windows should have opened:
echo   1. Backend (API): http://localhost:8000
echo   2. Frontend:      http://localhost:3002 (or 3001)
echo.
echo 🌐 Access URLs:
echo   • Frontend App:   http://localhost:3002
echo   • Backend API:    http://localhost:8000
echo   • API Docs:       http://localhost:8000/docs
echo   • Health Check:   http://localhost:8000/health
echo.
echo 🔧 To test deployment:
echo   python test_deployment.py
echo.
echo To stop the application, close both terminal windows.
echo.

pause 