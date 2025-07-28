.PHONY: help install clean test lint format download analyze generate pipeline example

help:
	@echo "DJNet Dataset Generator - Available Commands"
	@echo "==========================================="
	@echo "install     - Install dependencies"
	@echo "clean       - Clean generated files and cache"
	@echo "test        - Run unit tests"
	@echo "lint        - Run code linting with flake8"
	@echo "format      - Format code with black"
	@echo "download    - Download FMA dataset"
	@echo "analyze     - Analyze audio tracks"
	@echo "generate    - Generate transition dataset"
	@echo "pipeline    - Run complete pipeline"
	@echo "example     - Run example demo"

install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements.txt
	pip install -e .[dev]

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

test:
	python -m pytest tests/ -v

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ scripts/ tests/ --max-line-length=100

format:
	black src/ scripts/ tests/ example.py
	isort src/ scripts/ tests/ example.py

download:
	python scripts/download_data.py

analyze:
	python scripts/analyze_tracks.py

generate:
	python scripts/generate_dataset.py

pipeline:
	python scripts/run_pipeline.py

example:
	python example.py

# Development targets
setup-dev: install-dev
	pre-commit install

check: lint test
	@echo "All checks passed!"

# Docker targets (if you want to add Docker support later)
docker-build:
	docker build -t djnet-dataset .

docker-run:
	docker run -it --rm -v $(PWD)/data:/app/data djnet-dataset

# Data management
clean-data:
	rm -rf data/raw/fma_small/
	rm -rf data/processed/track_analysis/
	rm -rf data/output/djnet_dataset/

# Quick start for new users
quickstart: install download analyze
	@echo "Quick start complete! Run 'make generate' to create the dataset."
