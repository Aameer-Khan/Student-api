.PHONY: install migrate run test docker-build docker-migrate docker-run

VENV:= .venv
PYTHON := $(VENV)/bin/python
IMAGE := student-api
VERSION := 1.0.1

install:
	python3.12 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

migrate:
	$(PYTHON) -m flask --app app db upgrade

run:
	$(PYTHON) -m flask --app app run --port=5001 --debug

test:
	$(PYTHON) -m pytest tests -v

docker-build:
	docker build -t $(IMAGE):$(VERSION) .

docker-migrate:
	docker run --rm --env-file .env -v student-data:/app/instance $(IMAGE):$(VERSION) flask --app app db upgrade

docker-run:
	docker run --rm -p 5001:5000 --env-file .env -v student-data:/app/instance $(IMAGE):$(VERSION)
