PYTHON := python3
PIP := pip3
PACKAGE := clinirepgen

.PHONY: setup install run-demo lint clean help

setup: ## Install the package with dev dependencies
	$(PIP) install -e ".[dev]"

install: ## Install the package
	$(PIP) install -e .

run-demo: ## Run the offline demo (no API key required)
	$(PYTHON) -m clinirepgen.cli demo

lint: ## Run ruff linter
	$(PYTHON) -m ruff check $(PACKAGE)

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/ demo_output/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
