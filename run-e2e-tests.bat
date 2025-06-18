@echo off
REM End-to-End Test Runner for Workspace Management (Windows)
REM This script runs the comprehensive E2E test suite with proper setup and reporting

echo 🧪 OrdnungsHub E2E Test Suite - Workspace Management
echo ==================================================
echo.

REM Check if backend is running
echo 🔍 Checking backend status...
curl -s http://localhost:8001/docs >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend is running
    set BACKEND_RUNNING=true
) else (
    echo ❌ Backend is not running
    echo 🚀 Starting backend server...
    start /B cmd /c "npm run dev:backend"
    echo ⏳ Waiting for backend to start...
    timeout /t 10 /nobreak >nul
    set BACKEND_STARTED=true
)

REM Install Playwright browsers if needed
echo 🔧 Ensuring Playwright browsers are installed...
call npx playwright install

REM Clear previous test results
echo 🧹 Cleaning previous test results...
if exist test-results\ rmdir /s /q test-results
if exist playwright-report\ rmdir /s /q playwright-report

REM Parse command line arguments
set TEST_FILTER=
set EXTRA_ARGS=

:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--filter" (
    set TEST_FILTER=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--headed" (
    set EXTRA_ARGS=%EXTRA_ARGS% --headed
    shift
    goto parse_args
)
if "%~1"=="--debug" (
    set EXTRA_ARGS=%EXTRA_ARGS% --debug
    shift
    goto parse_args
)
if "%~1"=="--report" (
    echo 📊 Opening test report...
    call npx playwright show-report
    goto end
)
shift
goto parse_args
:end_parse

echo.
echo 📝 Test Suite Overview:
echo 1. Workspace CRUD Operations
echo 2. Workspace State Management
echo 3. Templates and Themes
echo 4. AI-Powered Features
echo 5. Settings and Configurations
echo 6. End-to-End Scenarios
echo.

REM Run tests
if not "%TEST_FILTER%"=="" (
    echo 🎯 Running filtered tests: %TEST_FILTER%
    call npx playwright test %TEST_FILTER% %EXTRA_ARGS%
) else (
    echo 🏃 Running all E2E tests
    call npx playwright test %EXTRA_ARGS%
)

REM Check test results
if %errorlevel% equ 0 (
    echo.
    echo ✅ All tests passed!
) else (
    echo.
    echo ❌ Some tests failed
)

REM Ask to view report
echo.
set /p VIEW_REPORT=📊 Would you like to view the detailed test report? (y/n): 
if /i "%VIEW_REPORT%"=="y" (
    call npx playwright show-report
)

:end
echo.
echo 🏁 Test run complete!
pause