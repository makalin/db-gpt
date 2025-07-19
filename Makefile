.PHONY: help install install-dev test test-coverage lint format clean run demo

help: ## Show this help message
	@echo "DB-GPT Development Commands"
	@echo "=========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 mypy

test: ## Run tests
	pytest

test-coverage: ## Run tests with coverage report
	pytest --cov=src --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/ -m "not integration"

test-integration: ## Run integration tests only
	pytest tests/ -m integration

lint: ## Run linting checks
	flake8 src/ tests/
	mypy src/

format: ## Format code with black
	black src/ tests/

format-check: ## Check code formatting
	black --check src/ tests/

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf build/
	rm -rf dist/

run: ## Run DB-GPT with example objective
	python main.py --objective "Analyze sample data and generate insights"

demo: ## Run a quick demo
	python main.py --objective "Show me the top 10 users by activity" --verbose

setup-db: ## Setup SQLite database for testing
	sqlite3 db_gpt.db "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, active BOOLEAN DEFAULT true);"
	sqlite3 db_gpt.db "INSERT OR IGNORE INTO users (id, name, email) VALUES (1, 'John Doe', 'john@example.com'), (2, 'Jane Smith', 'jane@example.com');"

check: ## Run all checks (format, lint, test)
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test

build: ## Build the package
	python setup.py sdist bdist_wheel

install-local: ## Install the package in development mode
	pip install -e .

uninstall: ## Uninstall the package
	pip uninstall db-gpt -y

docs: ## Generate documentation
	# Add documentation generation commands here
	@echo "Documentation generation not implemented yet"

docker-build: ## Build Docker image
	docker build -t db-gpt .

docker-run: ## Run DB-GPT in Docker
	docker run -it --rm db-gpt python main.py --objective "Analyze data"

docker-test: ## Run tests in Docker
	docker run -it --rm db-gpt pytest

# Development shortcuts
dev: install-dev setup-db ## Setup development environment
	@echo "Development environment ready!"

quick-test: ## Quick test run
	pytest tests/test_agent_manager.py -v

quick-lint: ## Quick lint check
	flake8 src/core/agent_manager.py

quick-format: ## Quick format check
	black --check src/core/agent_manager.py 