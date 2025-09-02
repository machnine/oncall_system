@echo off
setlocal enabledelayedexpansion

REM Install OnCall System as Windows Service using WinSW
REM Download WinSW from https://github.com/winsw/winsw/releases

echo 🔧 OnCall System Windows Service Installation (WinSW)
echo ====================================================
echo.

REM Detect deployment structure
echo 🔍 Detecting deployment structure...
set "CURRENT_DIR=%cd%"
set "APP_NAME=oncall-system"
set "SERVICE_NAME=OnCallSystem"

REM Check for services structure
if exist "C:\services\winsw\winsw-x64-v3.0.0-alpha.11.exe" (
    set "DEPLOY_TYPE=services"
    set "SERVICES_ROOT=C:\services"
    set "WINSW_PATH=!SERVICES_ROOT!\winsw\winsw-x64-v3.0.0-alpha.11.exe"
    set "APP_DIR=!SERVICES_ROOT!\apps\!APP_NAME!"
    set "LOG_DIR=!SERVICES_ROOT!\logs\!APP_NAME!"
    set "DATA_DIR=!SERVICES_ROOT!\data\!APP_NAME!"
    echo 📂 Detected services structure at !SERVICES_ROOT!
) else if exist "scripts\winsw.exe" (
    set "DEPLOY_TYPE=standard"
    set "WINSW_PATH=%cd%\scripts\winsw.exe"
    set "APP_DIR=%cd%"
    set "LOG_DIR=%cd%\logs"
    set "DATA_DIR=%cd%\data"
    echo 📁 Using standard deployment structure
) else (
    echo ❌ WinSW not found in expected locations!
    echo.
    echo 🔍 Searched for:
    echo    - C:\services\winsw\winsw-x64-v3.0.0-alpha.11.exe
    echo    - %cd%\scripts\winsw.exe
    echo.
    echo 📥 Please download WinSW from: https://github.com/winsw/winsw/releases
    echo 📂 And place it in one of the above locations
    echo.
    set /p custom_path="Or enter custom WinSW path: "
    if "!custom_path!"=="" (
        pause
        exit /b 1
    )
    set "WINSW_PATH=!custom_path!"
    set "DEPLOY_TYPE=custom"
    set "APP_DIR=%cd%"
    set "LOG_DIR=%cd%\logs"
    set "DATA_DIR=%cd%\data"
)

REM Allow override of detected paths
echo.
echo 📍 Current Configuration:
echo    WinSW:    !WINSW_PATH!
echo    App Dir:  !APP_DIR!
echo    Log Dir:  !LOG_DIR!
echo    Data Dir: !DATA_DIR!
echo.
set /p use_config="Use this configuration? (y/n) [y]: "
if "!use_config!"=="" set "use_config=y"

if /i not "!use_config!"=="y" (
    echo.
    echo 🛠️  Custom Configuration
    set /p WINSW_PATH="WinSW executable path: "
    set /p APP_DIR="Application directory: "
    set /p LOG_DIR="Logs directory: "
    set /p DATA_DIR="Data directory: "
    set /p APP_NAME="Application name [!APP_NAME!]: "
    if "!APP_NAME!"=="" set "APP_NAME=oncall-system"
    set /p SERVICE_NAME="Service name [!SERVICE_NAME!]: "
    if "!SERVICE_NAME!"=="" set "SERVICE_NAME=OnCallSystem"
)

REM Verify WinSW exists
if not exist "!WINSW_PATH!" (
    echo ❌ WinSW not found at: !WINSW_PATH!
    pause
    exit /b 1
)

REM Check if service already exists
sc query "!SERVICE_NAME!" >nul 2>nul
if %errorlevel% equ 0 (
    echo ⚠️  Service "!SERVICE_NAME!" already exists
    set /p remove="Remove existing service? (y/n): "
    if /i "!remove!"=="y" (
        echo 🗑️  Stopping and removing existing service...
        "!WINSW_PATH!" uninstall scripts\oncall-service.xml
    ) else (
        echo ❌ Installation cancelled
        pause
        exit /b 1
    )
)

REM Find uv.exe path
for /f "delims=" %%i in ('where uv') do set "UV_PATH=%%i"

if "!UV_PATH!"=="" (
    echo ❌ uv not found in PATH!
    echo 📥 Please install uv first: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo 📦 Installing OnCall System as Windows Service...
echo 📍 Service Name: !SERVICE_NAME!
echo 🏠 Working Directory: !APP_DIR!
echo 📊 Logs Directory: !LOG_DIR!
echo 💾 Data Directory: !DATA_DIR!
echo 🚀 UV Path: !UV_PATH!
echo 🔧 WinSW Path: !WINSW_PATH!
echo.

REM Create directories
echo 📁 Creating directory structure...
if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"
if not exist "!DATA_DIR!" mkdir "!DATA_DIR!"

REM Generate service XML configuration
echo 📝 Generating service configuration...
call :generate_service_xml "!APP_DIR!" "!LOG_DIR!" "!DATA_DIR!" "!SERVICE_NAME!" "!UV_PATH!"

echo 📄 Service configuration: scripts\oncall-service.xml
echo.

REM Install service using WinSW
"!WINSW_PATH!" install scripts\oncall-service.xml

if %errorlevel% equ 0 (
    echo ✅ Service installed successfully!
    echo.
    echo 🎮 Service Management Commands:
    echo    Start:   net start "!SERVICE_NAME!"
    echo    Stop:    net stop "!SERVICE_NAME!"
    echo    Remove:  "!WINSW_PATH!" uninstall scripts\oncall-service.xml
    echo    Status:  "!WINSW_PATH!" status scripts\oncall-service.xml
    echo.
    echo 🔍 Service will be available at: http://localhost:8000 and http://[server-ip]:8000
    echo 📋 Logs will be saved to: !LOG_DIR!
    echo.
    set /p start_now="🚀 Start service now? (y/n): "
    if /i "!start_now!"=="y" (
        net start "!SERVICE_NAME!"
        echo.
        echo 🌐 Service started! Check http://localhost:8000
    )
) else (
    echo ❌ Failed to install service
    echo 📋 Check the console output above for errors
)

pause
goto :eof

:generate_service_xml
set "xml_app_dir=%~1"
set "xml_log_dir=%~2"
set "xml_data_dir=%~3"
set "xml_service_name=%~4"
set "xml_uv_path=%~5"

(
echo ^<?xml version="1.0" encoding="UTF-8"?^>
echo ^<service^>
echo   ^<!-- Service Identity --^>
echo   ^<id^>%xml_service_name%^</id^>
echo   ^<name^>OnCall System^</name^>
echo   ^<description^>OnCall System - Django Web Application for managing on-call staff records and schedules^</description^>
echo.  
echo   ^<!-- Executable Configuration --^>
echo   ^<executable^>%xml_uv_path%^</executable^>
echo   ^<arguments^>run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --keepalive 2^</arguments^>
echo   ^<workingdirectory^>%xml_app_dir%^</workingdirectory^>
echo.
echo   ^<!-- Service Startup --^>
echo   ^<startmode^>Automatic^</startmode^>
echo   ^<delayedAutoStart^>true^</delayedAutoStart^>
echo.
echo   ^<!-- Process Management --^>
echo   ^<stoptimeout^>15 sec^</stoptimeout^>
echo   ^<stopparentprocessfirst^>true^</stopparentprocessfirst^>
echo.
echo   ^<!-- Environment Variables --^>
echo   ^<env name="DJANGO_SETTINGS_MODULE" value="config.settings.prod"/^>
echo   ^<env name="PYTHONUNBUFFERED" value="1"/^>
echo   ^<env name="DJANGO_LOG_LEVEL" value="INFO"/^>
echo.
echo   ^<!-- Logging Configuration --^>
echo   ^<log mode="roll-by-time"^>
echo     ^<pattern^>yyyy-MM-dd^</pattern^>
echo   ^</log^>
echo   ^<logpath^>%xml_log_dir%^</logpath^>
echo.
echo   ^<!-- Restart Policy --^>
echo   ^<onfailure action="restart" delay="10 sec"/^>
echo   ^<onfailure action="restart" delay="20 sec"/^>
echo   ^<onfailure action="restart" delay="30 sec"/^>
echo   ^<onfailure action="none"/^>
echo   ^<resetfailure^>1 hour^</resetfailure^>
echo.
echo   ^<!-- Process Priority --^>
echo   ^<priority^>Normal^</priority^>
echo ^</service^>
) > scripts\oncall-service.xml

goto :eof