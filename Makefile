.PHONY: install migrate run test db-up db-migrate docker-build docker-run down version prod-build prod-db prod-migrate deploy prod-ps prod-down prod-stop prod-start prod-logs smoke cluster-up cluster-down k8s-load k8s-deploy vault-unseal k8s-platform helm-lint helm-platform helm-deploy

VENV:= .venv
PYTHON := $(VENV)/bin/python
IMAGE := student-api
VERSION := 1.1.0
VAULT_CHART := 0.34.1
ESO_CHART := 2.13.0
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

version:
	@echo $(VERSION)

PROD := docker compose -f deploy/docker-compose.yml --env-file deploy/.env

prod-build:
	$(PROD) build api1

prod-db:
	$(PROD) up -d --wait db

prod-migrate: prod-db
	$(PROD) run --rm api1 flask --app app db upgrade

deploy: prod-build prod-migrate
	$(PROD) up -d

prod-ps:
	$(PROD) ps

prod-down:
	$(PROD) down

prod-stop:
	$(PROD) stop $(SVC)

prod-start:
	$(PROD) start $(SVC)

prod-logs:
	$(PROD) logs -f $(SVC)

smoke:
	npx --yes newman run deploy/postman/student-api.postman_collection.json -e deploy/postman/local.postman_environment.json

CLUSTER := student-api
KIND_CONFIG := infra/k8s/kind-config.yaml

cluster-up:
	@kind get clusters | grep -qx $(CLUSTER) || kind create cluster --config $(KIND_CONFIG)
	kubectl get nodes -L type

cluster-down:
	kind delete cluster --name $(CLUSTER)

k8s-load:
	kind load docker-image student-api:$(VERSION) --name $(CLUSTER)

vault-unseal:
	kubectl -n vault exec vault-0 -- vault operator unseal $$(jq -r '.unseal_keys_b64[0]' $(HOME)/.vault-lab/init.json)


helm-lint:
	helm lint helm/postgres helm/student-api

helm-platform:
	helm upgrade --install vault ./helm/vault -n vault --create-namespace -f helm/values/vault.yaml
	helm upgrade --install external-secrets ./helm/external-secrets -n external-secrets --create-namespace -f helm/values/external-secrets.yaml --wait

helm-deploy: helm-lint k8s-load
	helm upgrade --install postgres helm/postgres -n student-api --create-namespace --wait
	helm upgrade --install student-api helm/student-api -n student-api --set image.tag=$(VERSION) --wait