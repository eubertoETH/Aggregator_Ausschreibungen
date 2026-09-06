.DEFAULT_GOAL := help

.PHONY: help test compose-check build up down import-today report
help:
	@printf '%s\n' 'Targets: test compose-check build up down import-today report'
test:
	@./scripts/test.sh
compose-check:
	@docker compose -f Docker/compose.yaml config --quiet
build:
	@docker build -f Docker/Dockerfile -t service-template:local .
up:
	@docker compose -f Docker/compose.yaml up --build -d
down:
	@docker compose -f Docker/compose.yaml down
import-today:
	@curl -fsS -X POST "http://localhost:$${SERVICE_PORT:-8080}/imports/$$(date -d yesterday +%F)"
report:
	@curl -fsS -X POST "http://localhost:$${SERVICE_PORT:-8080}/reports/daily"
