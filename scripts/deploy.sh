#!/bin/bash

# OnCall System Deployment Script
# This script helps deploy the Django application in production

echo "🚀 OnCall System Production Deployment"
echo "======================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📋 Please copy .env.example to .env and configure your production settings"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv install --production

# Collect static files
echo "🗂️  Collecting static files..."
uv run python manage.py collectstatic --noinput --settings=config.settings.prod

# Run migrations
echo "💾 Running database migrations..."
uv run python manage.py migrate --settings=config.settings.prod

# Create superuser (optional)
echo "👤 Create superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    uv run python manage.py createsuperuser --settings=config.settings.prod
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Server Options:"
echo "   WSGI (Gunicorn): gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4"
echo "   ASGI (Uvicorn):  uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4"
echo ""
echo "📊 For systemd service, create /etc/systemd/system/oncall-system.service"