#!/bin/bash
set -e

APP_DIR="/home/ubuntu/cloud-health-dashboard"

# API service
cat << EOF | sudo tee /etc/systemd/system/cloud-health-api.service
[Unit]
Description=Cloud Health API
After=network.target redis-server.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Worker service
cat << EOF | sudo tee /etc/systemd/system/cloud-health-worker.service
[Unit]
Description=Cloud Health Worker
After=network.target redis-server.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/python -m app.worker_manager
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Nginx config
cat << 'EOF' | sudo tee /etc/nginx/sites-available/cloud-health
server {
    listen 80;
    server_name _;

    location / {
        root /var/www/cloud-health;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/cloud-health /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

sudo systemctl daemon-reload
sudo systemctl enable cloud-health-api
sudo systemctl enable cloud-health-worker
sudo systemctl enable nginx

echo "Services configured!"