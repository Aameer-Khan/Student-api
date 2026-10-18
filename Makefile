.PHONY: install migrate run test db-up db-migrate docker-build docker-run down

VENV:= .venv
PYTHON := $(VENV)/bin/python
IMAGE := student-api
VERSION := 1.1.0
export VERSION


install:
	python3.12 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.txt

build: install
	$(PYTHON) -m compileall -q app

lint:
	$(PYTHON) -m ruff check app tests

migrate:
	$(PYTHON) -m flask --app app db upgrade

run:
	$(PYTHON) -m flask --app app run --port=5001 --debug

test:
	$(PYTHON) -m pytest tests -v

db-up:
	docker compose up -d --wait db

db-migrate: db-up
	docker compose run --rm api flask --app app db upgrade

docker-build:
	docker compose build api

docker-run: docker-build db-migrate
	docker compose up -d api

down:
	docker compose down