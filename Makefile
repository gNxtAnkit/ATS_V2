.PHONY: help setup dev up down restart logs test test-unit test-integration test-db test-migrations lint format typecheck quality db-upgrade db-downgrade db-current db-heads db-history db-check db-reset-local db-validate clean

PYTHON ?= python
COMPOSE ?= docker compose

help:
	$(PYTHON) scripts/dev.py help

setup:
	$(PYTHON) scripts/dev.py setup

dev:
	$(PYTHON) scripts/dev.py dev

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f

test:
	$(PYTHON) -m pytest

test-unit:
	$(PYTHON) -m pytest tests/unit

test-integration:
	$(PYTHON) -m pytest tests/integration

test-db:
	$(PYTHON) -m pytest tests/integration tests/security

test-migrations:
	$(PYTHON) -m pytest tests/integration/test_migrations.py

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy

quality:
	$(PYTHON) scripts/dev.py quality

db-upgrade:
	$(PYTHON) scripts/db.py upgrade

db-downgrade:
	$(PYTHON) scripts/db.py downgrade

db-current:
	$(PYTHON) scripts/db.py current

db-heads:
	$(PYTHON) scripts/db.py heads

db-history:
	$(PYTHON) scripts/db.py history

db-check:
	$(PYTHON) scripts/db.py check

db-reset-local:
	$(PYTHON) scripts/db.py reset-local

db-validate:
	$(PYTHON) scripts/db.py validate

clean:
	$(PYTHON) scripts/dev.py clean
