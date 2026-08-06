PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
MYPY := $(VENV)/bin/mypy
RUFF := $(VENV)/bin/ruff
TERRAFORM_DIR := infra/terraform
ECR_IMAGE_TAG ?= $(shell git rev-parse HEAD 2>/dev/null || echo local)
AWS_REGION ?= ap-south-1

.PHONY: setup test lint typecheck format reproduce simulate deploy plan plan-artifact collect-evidence destroy clean docker-build

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	$(VENV)/bin/pre-commit install

test:
	$(RUFF) check src tests
	$(RUFF) format --check src tests
	$(MYPY) src/
	$(PYTEST) --cov=src/india_football_funnel --cov-report=term-missing

lint:
	$(RUFF) check src tests
	$(RUFF) format --check src tests

typecheck:
	$(MYPY) src/

format:
	$(RUFF) format src tests
	$(RUFF) check --fix src tests

reproduce:
	$(VENV)/bin/iff-reproduce

simulate:
	$(VENV)/bin/iff-simulate

plan:
	@test -n "$(AWS_ACCOUNT_ID)" || (echo "Set AWS_ACCOUNT_ID before deploy/plan" && exit 1)
	cd $(TERRAFORM_DIR) && terraform init && terraform plan \
		-var="aws_account_id=$(AWS_ACCOUNT_ID)" \
		-var="aws_region=$(AWS_REGION)" \
		-var="ecr_image_tag=$(ECR_IMAGE_TAG)"

plan-artifact:
	@test -n "$(AWS_ACCOUNT_ID)" || (echo "Set AWS_ACCOUNT_ID before plan-artifact" && exit 1)
	@mkdir -p docs/deployment_evidence/runs/local-$$(date -u +%Y%m%dT%H%M%SZ)
	@RUN_DIR=$$(ls -td docs/deployment_evidence/runs/local-* | head -1); \
	cd $(TERRAFORM_DIR) && terraform init -input=false && terraform plan -input=false -no-color \
		-var="aws_account_id=$(AWS_ACCOUNT_ID)" \
		-var="aws_region=$(AWS_REGION)" \
		-var="ecr_image_tag=$(ECR_IMAGE_TAG)" \
		| tee "$$RUN_DIR/terraform_plan.txt"; \
	echo "Plan saved to $$RUN_DIR/terraform_plan.txt"

collect-evidence:
	@chmod +x scripts/collect_deploy_evidence.sh
	./scripts/collect_deploy_evidence.sh post-deploy

deploy:
	@test -n "$(AWS_ACCOUNT_ID)" || (echo "Set AWS_ACCOUNT_ID before deploy" && exit 1)
	@echo "WARNING: This creates billable AWS resources. Run 'make destroy' when done."
	cd $(TERRAFORM_DIR) && terraform init && terraform apply -auto-approve \
		-var="aws_account_id=$(AWS_ACCOUNT_ID)" \
		-var="aws_region=$(AWS_REGION)" \
		-var="ecr_image_tag=$(ECR_IMAGE_TAG)"

destroy:
	@echo "Tearing down AWS resources..."
	cd $(TERRAFORM_DIR) && terraform destroy -auto-approve \
		-var="aws_account_id=$(AWS_ACCOUNT_ID)" \
		-var="aws_region=$(AWS_REGION)" \
		-var="ecr_image_tag=$(ECR_IMAGE_TAG)"

docker-build:
	docker build -t india-football-funnel:latest .

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
