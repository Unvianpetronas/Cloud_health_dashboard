#!/bin/bash
set -e

echo "======================================"
echo "Cloud Health Dashboard Deployment"
echo "======================================"

# Configuration
APP_DIR="/home/ubuntu/cloud-health-dashboard"
LOG_FILE="/var/log/cloud-health-deploy.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a $LOG_FILE
}

# Stop services
log "Stopping services..."
sudo systemctl stop cloud-health-api || true
sudo systemctl stop cloud-health-worker || true
sudo systemctl stop nginx || true

# Install dependencies
log "Installing dependencies..."
cd $APP_DIR
chmod +x deployment/scripts/install-dependencies.sh
./deployment/scripts/install-dependencies.sh

# Deploy backend
log "Deploying backend..."
cd $APP_DIR/backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate

# Deploy frontend
log "Deploying frontend..."
sudo rm -rf /var/www/cloud-health
sudo mkdir -p /var/www/cloud-health
sudo cp -r $APP_DIR/frontend-build/* /var/www/cloud-health/
sudo chown -R www-data:www-data /var/www/cloud-health

# Setup services
log "Setting up services..."
cd $APP_DIR
chmod +x deployment/scripts/setup-services.sh
./deployment/scripts/setup-services.sh

# Start Redis
if ! systemctl is-active --quiet redis-server; then
    log "Starting Redis..."
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
fi

# Start services
log "Starting services..."
sudo systemctl daemon-reload
sudo systemctl start cloud-health-api
sudo systemctl start cloud-health-worker
sudo systemctl start nginx

# Health check
sleep 5
log "Running health check..."
chmod +x deployment/scripts/health-check.sh
./deployment/scripts/health-check.sh

log "======================================"
log "Deployment completed!"
log "======================================"