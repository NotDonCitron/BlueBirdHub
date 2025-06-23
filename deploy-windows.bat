@echo off
echo.
echo =====================================================
echo    OrdnungsHub - Windows Local Deployment
echo =====================================================
echo.

REM Check Python
echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Check Node.js
echo.
echo Checking Node.js installation...
node --version
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Create environment file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    echo # OrdnungsHub Environment Configuration > .env
    echo NODE_ENV=development >> .env
    echo PYTHON_ENV=development >> .env
    echo SECRET_KEY=your_secret_key_here_change_in_production >> .env
    echo JWT_SECRET_KEY=your_jwt_secret_key_here_change_in_production >> .env
    echo DATABASE_URL=sqlite:///./data/ordnungshub.db >> .env
    echo CORS_ORIGINS=http://localhost:3000,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3002 >> .env
    echo LOG_LEVEL=INFO >> .env
    echo.
    echo Created .env file with default settings
    echo IMPORTANT: Update API keys and secrets before production use!
    echo.
)

REM Install backend dependencies
echo Installing backend dependencies...
cd packages\backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install backend dependencies
    cd ..\..
    pause
    exit /b 1
)
cd ..\..

REM Install frontend dependencies
echo.
echo Installing frontend dependencies...
cd packages\web
npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install frontend dependencies
    cd ..\..
    pause
    exit /b 1
)

REM Build frontend
echo.
echo Building frontend...
npm run build
if %errorlevel% neq 0 (
    echo ERROR: Failed to build frontend
    cd ..\..
    pause
    exit /b 1
)
cd ..\..

REM Create data directory
if not exist data mkdir data

echo.
echo =====================================================
echo    Installation Complete!
echo =====================================================
echo.
echo To start the application:
echo   1. Run: start-backend.bat
echo   2. Run: start-frontend.bat (in another terminal)
echo.
echo Or run both together: start-app.bat
echo.
echo URLs will be:
echo   Backend API: http://localhost:8000
echo   Frontend:    http://localhost:3000
echo   API Docs:    http://localhost:8000/docs
echo.

pause 