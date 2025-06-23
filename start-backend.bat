@echo off
echo.
echo =====================================================
echo    Starting OrdnungsHub Backend
echo =====================================================
echo.

REM Load environment variables
if exist .env (
    echo Loading environment from .env file...
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if not "%%a"=="" if not "%%a"=="rem" if not "%%a"=="#" (
            set "%%a=%%b"
        )
    )
)

REM Navigate to project root
cd /d "%~dp0"

REM Create necessary directories
if not exist data mkdir data
if not exist logs mkdir logs
if not exist uploads mkdir uploads

echo Starting FastAPI backend server...
echo.
echo Backend will be available at: http://localhost:8000
echo API Documentation at: http://localhost:8000/docs
echo.

REM Start the backend server
python -m uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 --reload

pause 