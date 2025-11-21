.PHONY: help dev build up down logs clean deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

dev: ## Start local development environment
	docker-compose up -d
	@echo "✅ Development environment started!"
	@echo "   Application: http://localhost"
	@echo "   Backend API: http://localhost/api"
	@echo "   Health: http://localhost/health"

build: ## Build Docker images locally
	docker-compose build --no-cache

up: ## Start services
	docker-compose up -d

down: ## Stop services
	docker-compose down

logs: ## View logs
	docker-compose logs -f

clean: ## Remove containers, volumes, and images
	docker-compose down -v --rmi all
	docker system prune -f

restart: ## Restart all services
	docker-compose restart

ps: ## Show running containers
	docker-compose ps

test-frontend: ## Test frontend build
	cd frontend && npm test

test-backend: ## Test backend
	cd backend && pytest

deploy-local: ## Deploy locally with production config
	docker-compose -f docker-compose.yml up -d

status: ## Check service health
	@echo "Checking service status..."
	@curl -f http://localhost/health && echo "✅ Application is healthy" || echo "❌ Application is not responding"

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

shell-nginx: ## Open shell in nginx container
	docker-compose exec nginx /bin/sh

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

lint-backend: ## Lint backend code
	cd backend && flake8 app/

install: ## Install dependencies
	cd frontend && npm install
	cd backend && pip install -r requirements.txt

push-ecr: ## Push images to ECR (requires AWS credentials)
	@echo "Logging in to ECR..."
	@aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(ECR_REGISTRY)
	@echo "Building and pushing images..."
	docker-compose build
	docker tag cloud_health_dashboard_frontend:latest $(ECR_REGISTRY)/cloud-health-frontend:latest
	docker tag cloud_health_dashboard_backend:latest $(ECR_REGISTRY)/cloud-health-backend:latest
	docker push $(ECR_REGISTRY)/cloud-health-frontend:latest
	docker push $(ECR_REGISTRY)/cloud-health-backend:latest
	@echo "✅ Images pushed to ECR"
