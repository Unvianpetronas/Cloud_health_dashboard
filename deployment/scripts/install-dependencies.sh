#!/bin/bash
set -e

echo "Installing system dependencies..."

sudo apt-get update -qq

# Python
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential

# Node.js (if not installed)
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Redis (if not installed)
if ! command -v redis-server &> /dev/null; then
    sudo apt-get install -y redis-server
fi

# Nginx (if not installed)
if ! command -v nginx &> /dev/null; then
    sudo apt-get install -y nginx
fi

echo "Dependencies installed!"