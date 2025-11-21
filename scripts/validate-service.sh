#!/bin/bash
set -e

echo "Validating service deployment..."

# Wait for services to start
sleep 15

# Check if containers are running
if ! docker-compose -f /home/ec2-user/app/docker-compose.prod.yml ps | grep -q "Up"; then
    echo "ERROR: Containers are not running"
    docker-compose -f /home/ec2-user/app/docker-compose.prod.yml logs
    exit 1
fi

# Check health endpoint
max_attempts=10
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Service validation successful!"
        exit 0
    fi
    
    echo "Waiting for health check... (attempt $((attempt+1))/$max_attempts)"
    sleep 5
    attempt=$((attempt+1))
done

echo "❌ Service validation failed!"
exit 1
