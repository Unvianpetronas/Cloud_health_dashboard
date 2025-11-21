#!/bin/bash
set -e

echo "Stopping application..."
cd /home/ec2-user/app
docker-compose -f docker-compose.prod.yml down || true
echo "Application stopped successfully"
