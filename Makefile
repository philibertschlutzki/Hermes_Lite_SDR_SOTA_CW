# Makefile for HL2 SOTA CW Project
# Common development tasks

.PHONY: help install test lint typecheck clean run validate-csv

help:
	@echo "HL2 SOTA CW Development Tasks"
	@echo "=============================="
	@echo "install          - Install Python dependencies"
	@echo "test             - Run pytest tests"
	@echo "lint             - Run ruff linter"
	@echo "typecheck        - Run mypy type checker"
	@echo "validate-csv     - Validate TX quality CSV"
	@echo "run              - Start backend server"
	@echo "clean            - Clean build artifacts"
	@echo "test-all         - Run lint + typecheck + test + validate-csv"

install:
	cd pi/backend && pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio ruff mypy

test:
	cd pi/backend && pytest tests/ -v --cov=src/sota_cw --cov-report=term-missing

lint:
	cd pi/backend && ruff check src/sota_cw/

typecheck:
	cd pi/backend && mypy src/sota_cw/ --ignore-missing-imports

validate-csv:
	python docs/test_reports/tools/validate_tx_quality_csv.py

run:
	cd pi/backend && uvicorn sota_cw.api:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	cd pi/backend && rm -rf .coverage htmlcov/ 2>/dev/null || true

test-all: lint typecheck test validate-csv
	@echo "All checks passed!"
