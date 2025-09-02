@echo off
setlocal enabledelayedexpansion

REM OnCall System Windows Deployment Script
REM This script helps deploy the Django application in production on Windows

echo 🚀 OnCall System Production Deployment (Windows)
echo ===============================================
echo.

REM Deployment Structure Options
echo 📁 Deployment Structure Options:
echo    1. Standard (current directory)
echo    2. Services structure (/services/apps/appname, /services/logs/appname, etc.)
echo    3. Custom paths
echo.
set /p deploy_type="Choose deployment type (1-3): "

REM Set default paths
set "APP_NAME=oncall-system"
set "APP_DIR=%cd%"
set "LOG_DIR=%cd%\logs"
set "DATA_DIR=%cd%\data"
set "VENV_DIR=%cd%\.venv"
set "WINSW_PATH=%cd%\scripts\winsw.exe"

if "%deploy_type%"=="2" (
    echo.
    echo 📂 Services Structure Configuration
    set /p services_root="Services root directory [C:\services]: "
    if "!services_root!"=="" set "services_root=C:\services"
    
    set /p app_name="Application name [!APP_NAME!]: "
    if "!app_name!"=="" set "app_name=!APP_NAME!"
    
    set "APP_DIR=!services_root!\apps\!app_name!"
    set "LOG_DIR=!services_root!\logs\!app_name!"
    set "DATA_DIR=!services_root!\data\!app_name!"
    set "VENV_DIR=!services_root!\envs\!app_name!"
    set "WINSW_PATH=!services_root!\winsw\winsw-x64-v3.0.0-alpha.11.exe"
    
    echo.
    echo 📍 Configured paths:
    echo    App Code: !APP_DIR!
    echo    Logs:     !LOG_DIR!
    echo    Data:     !DATA_DIR!
    echo    Venv:     !VENV_DIR!
    echo    WinSW:    !WINSW_PATH!
    echo.
    
) else if "%deploy_type%"=="3" (
    echo.
    echo 🛠️  Custom Path Configuration
    set /p APP_DIR="Application directory [%cd%]: "
    if "!APP_DIR!"=="" set "APP_DIR=%cd%"
    
    set /p LOG_DIR="Logs directory [!APP_DIR!\logs]: "
    if "!LOG_DIR!"=="" set "LOG_DIR=!APP_DIR!\logs"
    
    set /p DATA_DIR="Data directory [!APP_DIR!\data]: "
    if "!DATA_DIR!"=="" set "DATA_DIR=!APP_DIR!\data"
    
    set /p VENV_DIR="Virtual environment [!APP_DIR!\.venv]: "
    if "!VENV_DIR!"=="" set "VENV_DIR=!APP_DIR!\.venv"
    
    set /p WINSW_PATH="WinSW executable [!APP_DIR!\scripts\winsw.exe]: "
    if "!WINSW_PATH!"=="" set "WINSW_PATH=!APP_DIR!\scripts\winsw.exe"
)

REM Create directories if they don't exist
echo 📁 Creating directory structure...
if not exist "!APP_DIR!" mkdir "!APP_DIR!"
if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"
if not exist "!DATA_DIR!" mkdir "!DATA_DIR!"

REM Change to application directory
cd /d "!APP_DIR!"

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found in !APP_DIR!
    echo 📋 Please copy .env.example to .env and configure your production settings
    echo 💡 You may need to update DATABASE paths to use !DATA_DIR!
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
uv install --production
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Collect static files
echo 🗂️  Collecting static files...
uv run python manage.py collectstatic --noinput --settings=config.settings.prod
if %errorlevel% neq 0 (
    echo ❌ Failed to collect static files
    pause
    exit /b 1
)

REM Run migrations
echo 💾 Running database migrations...
uv run python manage.py migrate --settings=config.settings.prod
if %errorlevel% neq 0 (
    echo ❌ Failed to run migrations
    pause
    exit /b 1
)

REM Create superuser (optional)
echo.
set /p create_superuser="👤 Create superuser? (y/n): "
if /i "%create_superuser%"=="y" (
    uv run python manage.py createsuperuser --settings=config.settings.prod
)

echo.
echo ✅ Deployment complete!
echo.
echo 📍 Deployment Summary:
echo    App Directory:  !APP_DIR!
echo    Logs Directory: !LOG_DIR!
echo    Data Directory: !DATA_DIR!
echo    Venv Directory: !VENV_DIR!
echo.
echo 🌐 Manual Server Options:
echo    WSGI: uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
echo    ASGI: uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
echo.
echo 🔧 Windows Service Installation:
if exist "!WINSW_PATH!" (
    echo    ✅ WinSW found at: !WINSW_PATH!
    echo    🚀 Run: scripts\install-windows-service.bat
) else (
    echo    ❌ WinSW not found at: !WINSW_PATH!
    echo    📥 Download from: https://github.com/winsw/winsw/releases
)
echo.
echo 💾 Database Configuration:
echo    💡 Update your .env file to use !DATA_DIR! for database storage
echo    📄 Example: DB_NAME=!DATA_DIR!\db.sqlite3
echo.
pause