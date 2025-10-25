#!/bin/bash
set -e

APP_DIR="/home/ec2-user/cloud-health-dashboard"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "======================================"
echo "Deployment Script Started"
echo "======================================"

cd "$APP_DIR"

# Install Python dependencies if requirements.txt exists
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip3 install --user -r requirements.txt || echo "Failed to install some Python dependencies"
fi

# Set up backend
if [ -d backend ]; then
    echo "Setting up backend..."
    cd backend
    if [ -f requirements.txt ]; then
        pip3 install --user -r requirements.txt || echo "Failed to install backend dependencies"
    fi
    cd ..
fi

# Stop existing services if they exist (won't fail if they don't)
echo "Stopping services if they exist..."
sudo systemctl stop cloud-health-api.service 2>/dev/null || echo "cloud-health-api.service not running"
sudo systemctl stop cloud-health-worker.service 2>/dev/null || echo "cloud-health-worker.service not running"
sudo systemctl stop nginx.service 2>/dev/null || echo "nginx not running"

# Set permissions
echo "Setting permissions..."
sudo chown -R ec2-user:ec2-user "$APP_DIR"
chmod +x deployment/scripts/*.sh 2>/dev/null || true

# Copy frontend build to nginx directory (if nginx is installed)
if [ -d frontend-build ] && [ -d /usr/share/nginx/html ]; then
    echo "Deploying frontend to nginx..."
    sudo rm -rf /usr/share/nginx/html/*
    sudo cp -r frontend-build/* /usr/share/nginx/html/
    sudo chown -R nginx:nginx /usr/share/nginx/html 2>/dev/null || true
fi

# Start services if they exist
echo "Starting services if they exist..."
sudo systemctl start cloud-health-api.service 2>/dev/null || echo "cloud-health-api.service not configured yet"
sudo systemctl start cloud-health-worker.service 2>/dev/null || echo "cloud-health-worker.service not configured yet"
sudo systemctl start nginx.service 2>/dev/null || echo "nginx not configured yet"

echo "======================================"
echo "Deployment Script Completed"
echo "======================================"
echo ""
echo "Next steps if this is first deployment:"
echo "1. SSH to your EC2 instance"
echo "2. Install required services (nginx, python, etc.)"
echo "3. Set up systemd services for your application"
echo "4. Configure nginx"
echo ""