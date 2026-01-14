# CliniRepGen Makefile
# 
# Commands for development, testing, and running the pipeline
#

.PHONY: setup install test lint format run-demo clean help

# Default Python
PYTHON := python3
PIP := pip3

# Project paths
PACKAGE := clinirepgen
TESTS := tests

#
# Setup and Installation
#

setup: ## Set up development environment
	$(PIP) install -e ".[dev]"
	@echo "✅ Development environment set up"

install: ## Install the package
	$(PIP) install -e .
	@echo "✅ Package installed"

install-dev: ## Install with development dependencies
	$(PIP) install -e ".[dev]"
	@echo "✅ Package installed with dev dependencies"

#
# Testing
#

test: ## Run all tests
	$(PYTHON) -m pytest $(TESTS) -v

test-unit: ## Run unit tests only
	$(PYTHON) -m pytest $(TESTS)/test_schemas.py $(TESTS)/test_manifest.py $(TESTS)/test_tools.py -v

test-integration: ## Run integration tests only
	$(PYTHON) -m pytest $(TESTS)/test_integration.py -v

test-cov: ## Run tests with coverage
	$(PYTHON) -m pytest $(TESTS) --cov=$(PACKAGE) --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

#
# Code Quality
#

lint: ## Run linters
	$(PYTHON) -m ruff check $(PACKAGE) $(TESTS)

lint-fix: ## Run linters and fix issues
	$(PYTHON) -m ruff check $(PACKAGE) $(TESTS) --fix

format: ## Format code
	$(PYTHON) -m black $(PACKAGE) $(TESTS)

type-check: ## Run type checking
	$(PYTHON) -m mypy $(PACKAGE)

#
# Running the Pipeline
#

run-demo: ## Run demo with sample data
	$(PYTHON) -m clinirepgen.cli demo
	@echo ""
	@echo "Demo completed! Check demo_output/ for results."

run-sample: ## Run full pipeline on sample data (requires API_KEY)
	$(PYTHON) -m clinirepgen.cli run \
		--trial NCT00000001 \
		--ctgov sample_data/demo_trial.json \
		--input sample_data/ \
		--out output/
	@echo "Pipeline completed! Check output/ for results."

ingest-sample: ## Ingest sample data only
	$(PYTHON) -m clinirepgen.cli ingest \
		--trial NCT00000001 \
		--input sample_data/ \
		--ctgov sample_data/demo_trial.json \
		--out output/manifest.json

#
# Development Helpers
#

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf demo_output/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned"

clean-output: ## Clean output files
	rm -rf output/
	rm -rf demo_output/
	@echo "✅ Output directories cleaned"

show-structure: ## Show package structure
	@echo "📦 CliniRepGen Package Structure:"
	@find $(PACKAGE) -type f -name "*.py" | head -30

#
# Help
#

help: ## Show this help
	@echo "CliniRepGen - Clinical Trial Report Generator"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make setup      # Install dependencies"
	@echo "  2. make test       # Run tests"
	@echo "  3. make run-demo   # Run demo pipeline"

# Default target
.DEFAULT_GOAL := help
