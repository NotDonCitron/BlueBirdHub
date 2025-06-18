@echo off
REM Comprehensive Function Testing Script for Windows
REM Automatically test every function in your codebase

setlocal enabledelayedexpansion

REM Colors (ANSI codes)
set RED=[91m
set GREEN=[92m
set BLUE=[94m
set YELLOW=[93m
set NC=[0m

REM Project root
set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

REM Show banner
echo %BLUE%=============================================================%NC%
echo %BLUE%        Comprehensive Function Testing Workflow              %NC%
echo %BLUE%  Automatically discover, test, and validate every function  %NC%
echo %BLUE%=============================================================%NC%
echo.

REM Check first argument
if "%1"=="" goto run_full
if "%1"=="help" goto show_help
if "%1"=="--help" goto show_help
if "%1"=="-h" goto show_help
if "%1"=="full" goto run_full
if "%1"=="generate" goto run_generate
if "%1"=="execute" goto run_execute
if "%1"=="report" goto run_report
if "%1"=="target" goto run_target

REM Unknown command
echo %RED%Unknown command: %1%NC%
goto show_help

:check_deps
echo %YELLOW%Checking dependencies...%NC%

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%Python 3 not found%NC%
    exit /b 1
)

REM Check pytest
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%Installing pytest...%NC%
    pip install pytest pytest-cov pytest-json-report
)

REM Check rich
python -c "import rich" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%Installing rich...%NC%
    pip install rich
)

echo %GREEN%Dependencies ready%NC%
exit /b 0

:run_full
call :check_deps
if errorlevel 1 exit /b 1

echo %BLUE%Running full comprehensive testing...%NC%
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python src\backend\services\comprehensive_test_orchestrator.py
goto show_stats

:run_generate
call :check_deps
if errorlevel 1 exit /b 1

echo %BLUE%Generating tests only...%NC%
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python src\backend\services\comprehensive_test_orchestrator.py --generate-only
goto show_stats

:run_execute
call :check_deps
if errorlevel 1 exit /b 1

echo %BLUE%Executing tests only...%NC%
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python src\backend\services\comprehensive_test_orchestrator.py --execute-only
goto show_stats

:run_report
call :check_deps
if errorlevel 1 exit /b 1

echo %BLUE%Generating report only...%NC%
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python src\backend\services\comprehensive_test_orchestrator.py --report-only
goto show_stats

:run_target
if "%2"=="" (
    echo %RED%Error: Target path required%NC%
    echo Usage: test-all-functions.bat target ^<path^>
    exit /b 1
)

call :check_deps
if errorlevel 1 exit /b 1

echo %BLUE%Testing specific target: %2%NC%
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python src\backend\services\comprehensive_test_orchestrator.py --target %2
goto show_stats

:show_help
echo Usage: test-all-functions.bat [command] [options]
echo.
echo Commands:
echo   full       - Run complete testing workflow (default)
echo   generate   - Only generate missing tests
echo   execute    - Only execute existing tests  
echo   report     - Only generate coverage report
echo   target     - Test specific file/directory
echo   help       - Show this help message
echo.
echo Examples:
echo   test-all-functions.bat
echo   test-all-functions.bat generate
echo   test-all-functions.bat target src\backend\services
echo.
echo The workflow will:
echo   1. Discover all functions in your codebase
echo   2. Generate tests for untested functions
echo   3. Execute all tests and collect results
echo   4. Generate comprehensive coverage report
exit /b 0

:show_stats
if exist "test_coverage_report.json" (
    echo.
    echo %BLUE%Current Test Coverage:%NC%
    python -c "import json; data=json.load(open('test_coverage_report.json')); s=data.get('summary',{}); print(f'  Total Functions: {s.get(\"total_functions\",0)}'); print(f'  Functions with Tests: {s.get(\"functions_with_tests\",0)}'); print(f'  Coverage: {s.get(\"test_coverage\",0):.1f}%%'); print(f'  High Risk Functions: {len(data.get(\"high_risk_functions\",[]))}')"
)

echo.
echo %GREEN%Testing workflow complete!%NC%
echo Check %BLUE%test_coverage_report.json%NC% for detailed results
exit /b 0
