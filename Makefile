.PHONY: help install dev up down logs clean test deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Done!"

dev: ## Start development environment
	docker-compose up -d

up: ## Start all services
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services started!"
	@echo "Frontend: http://localhost:3001"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/api/docs"
	@echo "Grafana: http://localhost:3000 (admin/admin)"

down: ## Stop all services
	docker-compose down

down-v: ## Stop all services and remove volumes
	docker-compose down -v

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

clean: ## Clean up docker resources
	docker-compose down -v
	docker system prune -f

test: ## Run tests
	@echo "Running backend tests..."
	cd backend && pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test

test-backend: ## Run backend tests
	cd backend && pytest tests/ -v --cov=app

test-frontend: ## Run frontend tests
	cd frontend && npm test

build: ## Build docker images
	docker-compose build

rebuild: ## Rebuild docker images without cache
	docker-compose build --no-cache

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d ragchatbot

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

deploy-k8s: ## Deploy to Kubernetes
	kubectl apply -k infrastructure/kubernetes/base/

deploy-k8s-prod: ## Deploy to Kubernetes production
	kubectl apply -k infrastructure/kubernetes/overlays/prod/

skaffold-dev: ## Run Skaffold in dev mode
	cd devops/skaffold && skaffold dev

skaffold-run: ## Deploy with Skaffold
	cd devops/skaffold && skaffold run

format: ## Format code
	cd backend && black app/ tests/
	cd frontend && npm run lint:fix

lint: ## Lint code
	cd backend && pylint app/
	cd frontend && npm run lint

status: ## Show service status
	docker-compose ps

health: ## Check service health
	@echo "Checking backend health..."
	@curl -f http://localhost:8000/health || echo "Backend not healthy"
	@echo "\nChecking frontend health..."
	@curl -f http://localhost:3001 || echo "Frontend not healthy"

backup-db: ## Backup PostgreSQL database
	docker-compose exec postgres pg_dump -U postgres ragchatbot > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore PostgreSQL database (usage: make restore-db FILE=backup.sql)
	docker-compose exec -T postgres psql -U postgres ragchatbot < $(FILE)

monitor: ## Open monitoring dashboards
	@echo "Opening Grafana..."
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Visit http://localhost:3000"

docs: ## Generate API documentation
	cd backend && python -m app.generate_docs

.DEFAULT_GOAL := help
