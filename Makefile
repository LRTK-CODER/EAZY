# EAZY Project Makefile
# Development commands for the EAZY DAST project

.PHONY: dev worker test test-cov lint format build up down clean help

# Default target
help:
	@echo "EAZY Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start DB + Redis, then run API server"
	@echo "  make worker     - Run Worker Pool (separate terminal)"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run all tests"
	@echo "  make test-cov   - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint       - Run linters (ruff, black)"
	@echo "  make format     - Auto-format code"
	@echo ""
	@echo "Docker:"
	@echo "  make build      - Build all Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make clean      - Remove volumes and caches"

# Development
dev:
	docker compose up -d db redis
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd backend && uv run python -m app.workers.pool

# Testing
test:
	cd backend && uv run pytest tests/ -v

test-cov:
	cd backend && uv run pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Code Quality
lint:
	cd backend && uv run ruff check app/ tests/
	cd backend && uv run black --check app/ tests/

format:
	cd backend && uv run ruff check --fix app/ tests/
	cd backend && uv run black app/ tests/

# Docker
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

# Database
db-migrate:
	cd backend && uv run alembic upgrade head

db-revision:
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

# Frontend
frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint
