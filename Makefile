PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
MYPY := $(VENV)/bin/mypy
RUFF := $(VENV)/bin/ruff
TERRAFORM_DIR := infra/terraform

.PHONY: setup test lint typecheck format reproduce simulate deploy plan destroy clean docker-build

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
		-var="aws_region=$(AWS_REGION)"

deploy:
	@test -n "$(AWS_ACCOUNT_ID)" || (echo "Set AWS_ACCOUNT_ID before deploy" && exit 1)
	@echo "WARNING: This creates billable AWS resources. Run 'make destroy' when done."
	cd $(TERRAFORM_DIR) && terraform init && terraform apply -auto-approve \
		-var="aws_account_id=$(AWS_ACCOUNT_ID)" \
		-var="aws_region=$(AWS_REGION)"

destroy:
	@echo "Tearing down AWS resources..."
	cd $(TERRAFORM_DIR) && terraform destroy -auto-approve \
		-var="aws_account_id=$(AWS_ACCOUNT_ID)" \
		-var="aws_region=$(AWS_REGION)"

docker-build:
	docker build -t india-football-funnel:latest .

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
