.PHONY: help install dev-install lint format clean run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  dev-install  Install development dependencies"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  clean        Clean up generated files"
	@echo "  run          Run the development server"

# Install production dependencies
install:
	poetry install --only=main

# Install development dependencies
dev-install:
	poetry install



# Run linting
lint:
	poetry run flake8 .
	poetry run mypy .

# Format code
format:
	poetry run black .
	poetry run isort .

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .mypy_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Run development server
run:
	poetry run uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Run production server
run-prod:
	poetry run uvicorn server:app --host 0.0.0.0 --port 8000

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
