.DEFAULT_GOAL := help

IMAGE_TAG ?= local
DEPLOY_OUTPUT ?= dist
DEPLOY_NAME = aggregator-deploy-$(IMAGE_TAG)

.PHONY: help test compose-check build up down import-today report deploy-package deploy-check
help:
	@printf '%s\n' 'Targets: test compose-check build up down import-today report deploy-check deploy-package'
test:
	@./scripts/test.sh
compose-check:
	@docker compose -f Docker/compose.yaml config --quiet
build:
	@docker build -f Docker/Dockerfile -t aggregator-ausschreibungen:local .
up:
	@docker compose -f Docker/compose.yaml up --build -d
down:
	@docker compose -f Docker/compose.yaml down
import-today:
	@curl -fsS -X POST "http://localhost:$${SERVICE_PORT:-8080}/imports/$$(date -d yesterday +%F)"
report:
	@curl -fsS -X POST "http://localhost:$${SERVICE_PORT:-8080}/reports/daily"
deploy-check:
	@IMAGE_TAG=$(IMAGE_TAG) POSTGRES_PASSWORD=check DATABASE_URL=postgresql+psycopg://aggregator:check@db:5432/aggregator docker compose -f Docker/compose.production.yaml config --quiet
deploy-package: deploy-check
	@mkdir -p $(DEPLOY_OUTPUT)/$(DEPLOY_NAME)
	@cp Docker/compose.production.yaml $(DEPLOY_OUTPUT)/$(DEPLOY_NAME)/compose.yaml
	@cp deploy/.env.example $(DEPLOY_OUTPUT)/$(DEPLOY_NAME)/.env.example
	@cp docs/deployment.md $(DEPLOY_OUTPUT)/$(DEPLOY_NAME)/README.md
	@tar -C $(DEPLOY_OUTPUT) -czf $(DEPLOY_OUTPUT)/$(DEPLOY_NAME).tar.gz $(DEPLOY_NAME)
	@printf '%s\n' "Created $(DEPLOY_OUTPUT)/$(DEPLOY_NAME).tar.gz"
