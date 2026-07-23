# ============================================================
# DeepGuard Makefile
# ============================================================

.PHONY: help setup dev prod stop logs test lint migrate seed train clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------- Environment ----------

setup: ## Initial setup — copy .env, build images
	@test -f .env || cp .env.example .env
	@echo "✅ .env file ready (edit with your secrets)"
	docker-compose build
	@echo "✅ Docker images built"

# ---------- Development ----------

dev: ## Start all services in development mode
	docker-compose up -d
	@echo "✅ DeepGuard dev stack running"
	@echo "   Backend:  http://localhost:5000"
	@echo "   Frontend: http://localhost:3000"
	@echo "   API Docs: http://localhost:5000/api/docs"

dev-logs: ## Tail logs for all dev services
	docker-compose logs -f

# ---------- Production ----------

prod: ## Start all services in production mode
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ DeepGuard production stack running on http://localhost:80"

prod-logs: ## Tail logs for all prod services
	docker-compose -f docker-compose.prod.yml logs -f

# ---------- Stop ----------

stop: ## Stop all services
	docker-compose down
	docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
	@echo "✅ All services stopped"

clean: ## Stop services and remove volumes
	docker-compose down -v
	docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
	@echo "✅ All services stopped and volumes removed"

# ---------- Database ----------

migrate: ## Run Alembic migrations
	docker-compose exec backend flask db upgrade
	@echo "✅ Migrations applied"

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add xyz")
	docker-compose exec backend flask db migrate -m "$(MSG)"

seed: ## Seed the database with sample data
	docker-compose exec mysql mysql -u$(MYSQL_USER) -p$(MYSQL_PASSWORD) $(MYSQL_DATABASE) < database/seed_data.sql
	@echo "✅ Database seeded"

# ---------- Testing ----------

test: test-backend test-ml ## Run all tests

test-backend: ## Run backend tests
	docker-compose exec backend python -m pytest tests/ -v --tb=short
	@echo "✅ Backend tests passed"

test-ml: ## Run ML tests
	cd ml && python -m pytest tests/ -v --tb=short
	@echo "✅ ML tests passed"

test-frontend: ## Run frontend tests
	cd frontend && npm test
	@echo "✅ Frontend tests passed"

# ---------- Linting ----------

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend Python code
	cd backend && flake8 app/ --max-line-length=120 --exclude=__pycache__,migrations
	@echo "✅ Backend lint passed"

lint-frontend: ## Lint frontend JavaScript code
	cd frontend && npx eslint src/ --ext .js,.jsx
	@echo "✅ Frontend lint passed"

# ---------- ML Training ----------

train: ## Train the ML model
	cd ml && python -m training.train
	@echo "✅ Model training complete"

evaluate: ## Evaluate the trained model
	cd ml && python -m training.evaluate
	@echo "✅ Model evaluation complete"

# ---------- Utilities ----------

shell-backend: ## Open a shell in the backend container
	docker-compose exec backend bash

shell-mysql: ## Open MySQL CLI
	docker-compose exec mysql mysql -u$(MYSQL_USER) -p$(MYSQL_PASSWORD) $(MYSQL_DATABASE)

shell-redis: ## Open Redis CLI
	docker-compose exec redis redis-cli
