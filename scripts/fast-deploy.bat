@echo off
setlocal enabledelayedexpansion

:: BlueBirdHub Fast Deployment Script (Windows)
:: Reduces deployment time from 30+ minutes to under 2 minutes

echo ⚡ BlueBirdHub FAST Deployment Script (Windows)
echo =============================================

:: Enable Docker BuildKit for faster builds
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1

:: Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

:: Default values
set DEPLOYMENT_TYPE=fast
set FORCE_REBUILD=false
set DEV_MODE=false

:: Parse command line arguments
:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--dev" set DEV_MODE=true
if "%~1"=="-d" set DEV_MODE=true
if "%~1"=="--force" set FORCE_REBUILD=true
if "%~1"=="-f" set FORCE_REBUILD=true
if "%~1"=="--production" set DEPLOYMENT_TYPE=production
if "%~1"=="-p" set DEPLOYMENT_TYPE=production
if "%~1"=="--help" goto show_help
if "%~1"=="-h" goto show_help
shift
goto parse_args

:end_parse

:: Function to check if image exists
set "IMAGE_EXISTS_RESULT=false"
for /f "tokens=*" %%i in ('docker images --format "table {{.Repository}}:{{.Tag}}" 2^>nul ^| findstr "bluebirdhub-backend:cache"') do (
    set IMAGE_EXISTS_RESULT=true
)

:: Clean up old containers if force rebuild
if "%FORCE_REBUILD%"=="true" (
    echo 🧹 Force rebuild - cleaning up old containers...
    docker-compose -f docker-compose.bluebbird.yml down --rmi local 2>nul
)

:: Choose build strategy
if "%DEV_MODE%"=="true" (
    echo 🛠️  Development mode - using simple fast build
    call :dev_build
    set COMPOSE_FILE=docker-compose.dev.yml
) else (
    echo 🚀 Production mode - using optimized multi-stage build
    call :fast_build
    set COMPOSE_FILE=docker-compose.bluebbird.yml
)

:: Start services with optimized settings
echo 🏁 Starting services...
docker-compose -f %COMPOSE_FILE% up -d --no-build

:: Quick health check
echo ⏳ Quick health check...
set /a count=0
:health_check_loop
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 0 goto health_check_success
set /a count+=1
if %count% GEQ 30 goto health_check_failed
timeout /t 2 /nobreak >nul
goto health_check_loop

:health_check_success
echo ✅ Services are ready!
echo.
echo 🎉 Fast deployment complete!
echo ==========================
echo ⏱️  Total time: %date% %time%
echo 🌐 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo 💡 Pro tips:
echo   - Use --dev for development (even faster)
echo   - Use --force to rebuild from scratch
echo   - Use docker system prune to clean up space
goto end

:health_check_failed
echo ❌ Health check failed. Check logs:
echo    docker-compose -f %COMPOSE_FILE% logs
goto end

:: Function for incremental build
:fast_build
echo 🚀 Using optimized build process...
if "%IMAGE_EXISTS_RESULT%"=="true" (
    echo 📦 Using cached layers for faster build...
    docker build ^
        --file Dockerfile.optimized ^
        --target runtime ^
        --cache-from bluebirdhub-backend:cache ^
        --tag bluebirdhub-backend:latest ^
        --tag bluebirdhub-backend:cache ^
        --build-arg BUILDKIT_INLINE_CACHE=1 ^
        .
) else (
    echo 🔨 First build - creating cache layers...
    docker build ^
        --file Dockerfile.optimized ^
        --target runtime ^
        --tag bluebirdhub-backend:latest ^
        --tag bluebirdhub-backend:cache ^
        --build-arg BUILDKIT_INLINE_CACHE=1 ^
        .
)
goto :eof

:: Function for development build (even faster)
:dev_build
echo ⚡ Development build - maximum speed...
:: Check if image exists for development
docker images bluebirdhub-backend:dev >nul 2>&1
if errorlevel 1 (
    echo 🔄 Building development image...
    docker build --file Dockerfile.simple --tag bluebirdhub-backend:dev .
) else (
    echo ✅ Using existing development image
)
goto :eof

:show_help
echo Usage: %0 [--dev^|-d] [--force^|-f] [--production^|-p]
echo.
echo Options:
echo   --dev, -d         Development mode (faster, with hot reload)
echo   --force, -f       Force rebuild from scratch
echo   --production, -p  Production mode with optimizations
echo   --help, -h        Show this help message
echo.
echo Examples:
echo   %0                    # Standard fast deployment
echo   %0 --dev              # Development mode with hot reload
echo   %0 --force            # Force complete rebuild
echo   %0 --production       # Production deployment
goto end

:end
pause 