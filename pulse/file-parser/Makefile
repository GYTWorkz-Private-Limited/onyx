.PHONY: help install dev-install test lint format clean run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  dev-install  Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  clean        Clean up generated files"
	@echo "  run          Run the development server"

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
dev-install:
	pip install -e ".[dev]"

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-coverage:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 .
	mypy .

# Format code
format:
	black .
	isort .

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Run development server
run:
	uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Run production server
run-prod:
	uvicorn server:app --host 0.0.0.0 --port 8000

# Future: Docker support can be added here when needed

# Setup development environment
setup-dev: dev-install
	cp .env.example .env
	mkdir -p output temp logs
	@echo "Development environment setup complete!"
	@echo "Please edit .env file with your API keys"

# Check code quality
check: lint test

# Full development setup
dev-setup: clean setup-dev check
	@echo "Development setup complete and verified!"
