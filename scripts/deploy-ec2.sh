#!/bin/bash
set -e

echo "==================================="
echo "Deploying Cloud Health Dashboard to EC2"
echo "==================================="

# Configuration
ECR_REGISTRY="${ECR_REGISTRY}"
AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Login to ECR
log_info "Logging in to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Stop existing containers
log_info "Stopping existing containers..."
docker-compose down || true

# Pull latest images from ECR
log_info "Pulling latest Docker images..."
docker pull $ECR_REGISTRY/cloud-health-frontend:latest
docker pull $ECR_REGISTRY/cloud-health-backend:latest
docker pull $ECR_REGISTRY/cloud-health-nginx:latest

# Update docker-compose.yml with ECR images
log_info "Updating docker-compose.yml..."
cat > docker-compose.prod.yml << COMPOSE_EOF
version: '3.8'

services:
  frontend:
    image: $ECR_REGISTRY/cloud-health-frontend:latest
    restart: always
    environment:
      - REACT_APP_BASE_URL=http://localhost:8000/api/v1
    networks:
      - app-network

  backend:
    image: $ECR_REGISTRY/cloud-health-backend:latest
    restart: always
    ports:
      - "8000:8000"
    environment:
      - YOUR_AWS_ACCESS_KEY_ID=${YOUR_AWS_ACCESS_KEY_ID}
      - YOUR_AWS_SECRET_ACCESS_KEY=${YOUR_AWS_SECRET_ACCESS_KEY}
      - YOUR_AWS_REGION=${YOUR_AWS_REGION}
      - SES_SENDER_EMAIL=${SES_SENDER_EMAIL}
      - FRONTEND_URL=http://your-domain.com
    networks:
      - app-network

  nginx:
    image: $ECR_REGISTRY/cloud-health-nginx:latest
    restart: always
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
COMPOSE_EOF

# Start containers
log_info "Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Check health
log_info "Waiting for services to be healthy..."
sleep 10

# Verify deployment
if curl -f http://localhost/health > /dev/null 2>&1; then
    log_info "✅ Deployment successful! Application is healthy."
else
    log_error "❌ Deployment failed! Health check failed."
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi

# Cleanup old images
log_info "Cleaning up old Docker images..."
docker image prune -f

log_info "==================================="
log_info "Deployment completed successfully!"
log_info "==================================="
