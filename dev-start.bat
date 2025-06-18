@echo off
setlocal EnableDelayedExpansion

echo 🚀 OrdnungsHub Development Environment Startup
echo =================================================

:: Function to check if port is in use
:check_port
    netstat -ano | findstr :%1 > nul
    if !errorlevel! == 0 (
        echo ⚠️  Port %1 is already in use
        call :kill_port %1
    ) else (
        echo ✅ Port %1 is available
    )
goto :eof

:: Function to kill process on port
:kill_port
    echo 🔄 Killing process on port %1...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%1') do (
        taskkill /F /PID %%a > nul 2>&1
    )
    timeout /t 1 > nul
goto :eof

:: Check Python installation
echo.
echo 🐍 Checking Python installation...
python --version > nul 2>&1
if !errorlevel! == 0 (
    for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i found
) else (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)

:: Check Node.js installation
echo.
echo 📦 Checking Node.js installation...
node --version > nul 2>&1
if !errorlevel! == 0 (
    for /f "tokens=*" %%i in ('node --version') do echo ✅ Node.js %%i found
) else (
    echo ❌ Node.js not found. Please install Node.js 18+
    exit /b 1
)

:: Check dependencies
echo.
echo 🔍 Checking dependencies...

:: Check Python dependencies
python -c "import fastapi, uvicorn" > nul 2>&1
if !errorlevel! == 0 (
    echo ✅ Python dependencies installed
) else (
    echo 📦 Installing Python dependencies...
    pip install -r requirements.txt
)

:: Check Node modules
if exist "node_modules" (
    echo ✅ Node.js dependencies installed
) else (
    echo 📦 Installing Node.js dependencies...
    npm install
)

:: Clean up ports
echo.
echo 🧹 Cleaning up ports...
call :check_port 3000
call :check_port 3001
call :check_port 8000
call :check_port 8001

timeout /t 2 > nul

:: Start backend services
echo.
echo 🔄 Starting backend services...

:: Start FastAPI backend
echo 📡 Starting FastAPI backend on port 8000...
start "FastAPI Backend" /min python src/backend/main.py

:: Start mock backend
echo 🎭 Starting mock backend on port 8001...
start "Mock Backend" /min python mock_backend.py

:: Wait for backends to start
echo ⏳ Waiting for backends to start...
timeout /t 5 > nul

:: Test backend connections
echo.
echo 🩺 Testing backend connections...

:: Test FastAPI backend
curl -s http://localhost:8000/health > nul 2>&1
if !errorlevel! == 0 (
    echo ✅ FastAPI backend responding on port 8000
) else (
    echo ⚠️  FastAPI backend not responding on port 8000
)

:: Test mock backend
curl -s http://localhost:8001/health > nul 2>&1
if !errorlevel! == 0 (
    echo ✅ Mock backend responding on port 8001
) else (
    echo ⚠️  Mock backend not responding on port 8001
)

:: Start frontend
echo.
echo 🎨 Starting frontend development server...
echo 📱 Frontend will be available at http://localhost:3001

:: Start the development server
start "Frontend Dev Server" npm run dev:react

echo.
echo 🎉 Development environment started!
echo ==================================
echo 📱 Frontend: http://localhost:3001
echo 📡 FastAPI Backend: http://localhost:8000
echo 🎭 Mock Backend: http://localhost:8001
echo.
echo 📊 Backend Status:
echo    - FastAPI: http://localhost:8000/health
echo    - Mock: http://localhost:8001/health
echo.
echo ⏹️  Close this window or press Ctrl+C to stop monitoring

:: Keep the script running
pause > nul
