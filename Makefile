.PHONY: help install test run clean check-health lint format

help:
	@echo "TPRM Frameworks MCP Server - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install       - Install the package in editable mode"
	@echo "  test          - Run test suite"
	@echo "  run           - Start the MCP server"
	@echo "  check-health  - Check server health"
	@echo "  lint          - Run linting (ruff)"
	@echo "  format        - Format code (black)"
	@echo "  clean         - Clean build artifacts"
	@echo "  dev           - Install with dev dependencies"

install:
	pip3 install -e .

dev:
	pip3 install -e ".[dev]"

test:
	python3 test_server.py

run:
	./start-server.sh

check-health:
	@python3 -c "import asyncio; from tprm_frameworks_mcp.server import health_check; print(asyncio.run(health_check()))"

lint:
	ruff check src/

format:
	black src/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.DEFAULT_GOAL := help
