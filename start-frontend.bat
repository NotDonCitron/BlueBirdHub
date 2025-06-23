@echo off
echo.
echo =====================================================
echo    Starting OrdnungsHub Frontend
echo =====================================================
echo.

REM Navigate to frontend directory
cd /d "%~dp0\packages\web"

REM Check if node_modules exists
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting development server...
echo.
echo Frontend will be available at: http://localhost:3000
echo.

REM Start the development server
npm run dev

pause 