# =============================================================================
# Pyckle - atajos de desarrollo y despliegue
# Requiere GNU make. Si no esta disponible usa ./dev <target>.
# =============================================================================
COMPOSE      ?= docker compose
COMPOSE_PROD ?= docker compose -f docker-compose.prod.yml
BACKEND      ?= $(COMPOSE) exec -T backend

.DEFAULT_GOAL := help

.PHONY: help up down build rebuild restart ps logs migrate revision downgrade \
        seed test lint format shell backend-shell db-shell redis-cli \
        prod-build prod-up prod-down prod-logs clean

help: ## Muestra esta ayuda
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

up: ## Levanta el stack de desarrollo
	$(COMPOSE) up -d --build

down: ## Detiene el stack (conserva volumenes)
	$(COMPOSE) down

build: ## Construye las imagenes de desarrollo
	$(COMPOSE) build

rebuild: ## Reconstruye sin cache
	$(COMPOSE) build --no-cache

restart: ## Reinicia los servicios
	$(COMPOSE) restart

ps: ## Estado de los contenedores
	$(COMPOSE) ps

logs: ## Logs en vivo
	$(COMPOSE) logs -f --tail=200

migrate: ## Aplica migraciones hasta head
	$(BACKEND) alembic upgrade head

revision: ## Crea una migracion (m="descripcion")
	$(BACKEND) alembic revision --autogenerate -m "$(m)"

downgrade: ## Revierte la ultima migracion (n=1 por defecto)
	$(BACKEND) alembic downgrade -1

seed: ## Carga datos semilla de desarrollo
	$(BACKEND) python -m app.db.seed

test: ## Ejecuta la suite de tests
	$(BACKEND) pytest -q

lint: ## Ruff check + format check
	$(BACKEND) ruff check app tests migrations
	$(BACKEND) ruff format --check app tests migrations

format: ## Aplica formato con Ruff
	$(BACKEND) ruff format app tests migrations
	$(BACKEND) ruff check --fix app tests migrations

shell: ## Shell en el contenedor backend
	$(COMPOSE) exec backend sh

backend-shell: shell ## Alias de shell

db-shell: ## psql en el contenedor postgres
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-pyckle} -d $${POSTGRES_DB:-pyckle}

redis-cli: ## redis-cli en el contenedor redis
	$(COMPOSE) exec redis redis-cli

prod-build: ## Construye imagenes de produccion
	$(COMPOSE_PROD) build

prod-up: ## Levanta produccion
	$(COMPOSE_PROD) up -d --build

prod-down: ## Detiene produccion
	$(COMPOSE_PROD) down

prod-logs: ## Logs de produccion
	$(COMPOSE_PROD) logs -f --tail=200

clean: ## Borra contenedores y volumenes (destructivo)
	$(COMPOSE) down -v --remove-orphans
