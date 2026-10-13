.PHONY: install migrate run test

VENV:= .venv
PYTHON := $(VENV)/bin/python

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
