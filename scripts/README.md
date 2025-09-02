# Deployment Scripts

This directory contains deployment scripts for the OnCall System.

## Windows Deployment

### 1. Basic Deployment (`deploy.bat`)
For manual deployment and testing with flexible directory structure:
```cmd
scripts\deploy.bat
```

**Deployment Options:**
1. **Standard** - Current directory deployment
2. **Services Structure** - Professional multi-app structure:
   - `/services/apps/appname` - Application code
   - `/services/logs/appname` - Application logs  
   - `/services/data/appname` - Database and data files
   - `/services/envs/appname` - Virtual environments
   - `/services/winsw/winsw-x64-v3.0.0-alpha.11.exe` - WinSW executable
3. **Custom** - Specify your own directory structure

This script will:
- Detect or configure directory structure
- Check for `.env` configuration
- Install dependencies with uv
- Collect static files
- Run database migrations
- Optionally create a superuser
- Show server startup commands

### 2. Windows Service (`install-windows-service.bat`)
For production deployment as a Windows service using WinSW with automatic path detection:

**Prerequisites:**
- Download [WinSW (Windows Service Wrapper)](https://github.com/winsw/winsw/releases)
- Place `winsw-x64-v3.0.0-alpha.11.exe` in one of these locations:
  - `C:\services\winsw\winsw-x64-v3.0.0-alpha.11.exe` (services structure)
  - `scripts\winsw.exe` (standard deployment)
  - Or specify custom path during installation

**Installation:**
```cmd
scripts\install-windows-service.bat
```

**Smart Detection:**
The script automatically detects your deployment structure:
- **Services Structure** - Detects `/services/` layout and configures accordingly
- **Standard** - Uses current directory structure
- **Custom** - Allows manual path specification

This will install OnCall System as a Windows service that:
- Starts automatically on boot (with delayed start)
- Runs on http://localhost:8000
- Logs to configured logs directory with daily rotation
- Has intelligent restart policies on failure
- Generates XML configuration dynamically based on your paths

**Service Management:**
```cmd
# Start the service
net start "OnCallSystem"

# Stop the service
net stop "OnCallSystem"

# Remove the service
scripts\winsw.exe uninstall scripts\oncall-service.xml

# Check service status
scripts\winsw.exe status scripts\oncall-service.xml

# View service configuration
notepad scripts\oncall-service.xml
```

**WinSW Advantages:**
- ✅ **Microsoft-backed** (.NET ecosystem)
- ✅ **XML configuration** (version controlled)
- ✅ **Advanced logging** with rotation
- ✅ **Restart policies** with exponential backoff
- ✅ **Environment variables** support
- ✅ **Dependency management**
- ✅ **Better error handling**

## Linux Deployment

### Basic Deployment (`deploy.sh`)
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Manual Server Commands

**Development:**
```bash
uv run python manage.py runserver
```

**Production (choose one):**
```bash
# WSGI with Gunicorn (traditional)
uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# ASGI with Uvicorn (modern, supports async)
uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

**Network Configuration:**
- `0.0.0.0:8000` - Accepts connections from any IP address
- `127.0.0.1:8000` - Local machine only (not suitable for servers)
- Configure `ALLOWED_HOSTS` in `.env` to restrict domain access
- Consider using IIS or nginx as reverse proxy for SSL/security

## Configuration

Make sure to:
1. Copy `.env.example` to `.env`
2. Configure your production database and secret key
3. Set `DEBUG=False` in production
4. Configure `ALLOWED_HOSTS` with your domain names