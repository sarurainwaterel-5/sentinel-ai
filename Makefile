SHELL := /bin/bash

BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV := $(BACKEND_DIR)/venv
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
ALEMBIC := $(VENV)/bin/alembic
UVICORN := $(VENV)/bin/uvicorn

.PHONY: help infra infra-status backend frontend health migrations test \
        test-backend test-frontend build lint status stop clean-check

help:
	@echo ""
	@echo "SentinelAI Development Commands"
	@echo "==============================="
	@echo "make infra          Start PostgreSQL/Qdrant"
	@echo "make infra-status   Show Docker service state"
	@echo "make backend        Start Sentinel API"
	@echo "make frontend       Start Vite frontend"
	@echo "make health         Check Sentinel services"
	@echo "make migrations     Show Alembic current/head"
	@echo "make test           Run backend + frontend tests"
	@echo "make build          Production frontend build"
	@echo "make lint           Run frontend lint"
	@echo "make status         Repository + service status"
	@echo "make stop           Stop Docker infrastructure"
	@echo ""

infra:
	docker compose up -d
	@echo ""
	docker compose ps

infra-status:
	docker compose ps

backend:
	cd $(BACKEND_DIR) && \
		venv/bin/uvicorn app.main:app --reload

frontend:
	cd $(FRONTEND_DIR) && npm run dev

migrations:
	cd $(BACKEND_DIR) && \
		venv/bin/alembic current && \
		venv/bin/alembic heads

health:
	@echo "=== Docker ==="
	@docker compose ps
	@echo ""
	@echo "=== Qdrant ==="
	@curl -fsS http://127.0.0.1:6333/ >/dev/null \
		&& echo "Qdrant: GREEN" \
		|| echo "Qdrant: DOWN"
	@echo ""
	@echo "=== Sentinel API ==="
	@curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null \
		&& echo "Sentinel API: GREEN" \
		|| echo "Sentinel API: DOWN"
	@echo ""
	@echo "=== Frontend ==="
	@curl -fsS http://127.0.0.1:5173/ >/dev/null \
		&& echo "Frontend: GREEN" \
		|| echo "Frontend: DOWN"

test: test-backend test-frontend

test-backend:
	cd $(BACKEND_DIR) && venv/bin/pytest -q

test-frontend:
	cd $(FRONTEND_DIR) && npm run test:run

build:
	cd $(FRONTEND_DIR) && npm run build

lint:
	cd $(FRONTEND_DIR) && npm run lint

clean-check:
	@if [ -z "$$(git status --porcelain)" ]; then \
		echo "Working tree: CLEAN"; \
	else \
		echo "Working tree: DIRTY"; \
		git status --short; \
	fi

status:
	@echo "=== Git ==="
	@git branch --show-current
	@git log -1 --oneline --decorate
	@echo ""
	@$(MAKE) --no-print-directory clean-check
	@echo ""
	@echo "=== Docker ==="
	@docker compose ps
	@echo ""
	@echo "=== Migrations ==="
	@cd $(BACKEND_DIR) && \
		venv/bin/alembic current && \
		venv/bin/alembic heads

stop:
	docker compose down
