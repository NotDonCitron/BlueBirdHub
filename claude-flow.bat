@echo off
REM Claude Code Flow - Quick Start Script for Windows
REM Usage: claude-flow.bat [command] [description]

setlocal enabledelayedexpansion

REM Colors
set RED=[91m
set GREEN=[92m
set BLUE=[94m
set YELLOW=[93m
set NC=[0m

REM Project root
set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

REM Check first argument
if "%1"=="" goto show_help
if "%1"=="help" goto show_help
if "%1"=="--help" goto show_help
if "%1"=="-h" goto show_help

REM Route to appropriate function
if "%1"=="feature" goto run_command
if "%1"=="fix" goto run_command
if "%1"=="refactor" goto run_command
if "%1"=="test" goto run_command
if "%1"=="setup" goto setup_environment
if "%1"=="status" goto show_status

REM Unknown command
echo %RED%Error: Unknown command '%1'%NC%
echo.
goto show_help

:show_help
echo %BLUE%Claude Code Flow - Autonomous Development System%NC%
echo.
echo Usage: claude-flow.bat [command] [options]
echo.
echo Commands:
echo   feature ^<description^>    - Develop a new feature
echo   fix ^<description^>       - Fix a bug
echo   refactor ^<description^>  - Refactor existing code
echo   test ^<description^>      - Add or improve tests
echo   setup                   - Initial setup and configuration
echo   status                  - Show current workflow status
echo.
echo Options:
echo   --auto                  - Auto-approve human checkpoints (dev only)
echo   --verbose               - Show detailed output
echo   --dry-run              - Preview changes without applying
echo.
echo Examples:
echo   claude-flow.bat feature "Add user authentication with JWT"
echo   claude-flow.bat fix "File upload fails on large files"
echo   claude-flow.bat refactor "Optimize database queries in file scanner"
exit /b 0

:check_dependencies
echo %BLUE%Checking dependencies...%NC%

REM Check Python
py --version >nul 2>&1
if errorlevel 1 (
    echo %RED%Error: Python 3 is not installed%NC%
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo %RED%Error: Node.js is not installed%NC%
    exit /b 1
)

REM Check virtual environment
if not exist ".venv" (
    echo %YELLOW%Creating Python virtual environment...%NC%
    py -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check Python packages
py -c "import rich" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%Installing Python dependencies...%NC%
    pip install rich
)

echo %GREEN%Dependencies checked%NC%
exit /b 0

:run_command
if "%2"=="" (
    echo %RED%Error: Description required%NC%
    echo Usage: claude-flow.bat %1 ^<description^>
    exit /b 1
)

call :check_dependencies
if errorlevel 1 exit /b 1

echo %BLUE%Starting Claude Code Flow...%NC%
echo %YELLOW%Task: %1 - %2%NC%
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run the orchestrator
py src\backend\services\claude_code_orchestrator.py %*
exit /b 0

:setup_environment
echo %BLUE%Setting up Claude Code Flow environment...%NC%

call :check_dependencies
if errorlevel 1 exit /b 1

REM Create directories
if not exist ".claude\workflows" mkdir ".claude\workflows"
if not exist ".claude\commands" mkdir ".claude\commands"
if not exist "logs\claude-flow" mkdir "logs\claude-flow"

REM Check configuration
if not exist ".claude\workflows\claude-code-flow.json" (
    echo %RED%Error: Configuration file not found%NC%
    echo Please ensure .claude\workflows\claude-code-flow.json exists
    exit /b 1
)

echo %GREEN%Environment setup complete%NC%
exit /b 0

:show_status
echo %BLUE%Claude Code Flow Status%NC%
echo ========================

REM Check configuration
if exist ".claude\workflows\claude-code-flow.json" (
    echo %GREEN%Configuration found%NC%
) else (
    echo %RED%Configuration missing%NC%
)

REM Check virtual environment
if exist ".venv" (
    echo %GREEN%Virtual environment exists%NC%
) else (
    echo %RED%Virtual environment missing%NC%
)

REM Check logs
if exist "logs\claude-flow" (
    echo %BLUE%Log directory exists%NC%
)

REM Check coverage
if exist "coverage\lcov-report\index.html" (
    echo %BLUE%Latest test coverage report available%NC%
)

exit /b 0
