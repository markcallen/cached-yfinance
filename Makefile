SHELL := /bin/bash

.PHONY: help check-uv deps setup

help:
	@printf "Available targets:\n"
	@printf "  make deps   Install project and development dependencies with uv\n"
	@printf "  make setup  Verify the local environment and install Git hooks\n"

check-uv:
	@command -v uv >/dev/null || { \
		printf "uv is required but was not found on PATH.\n"; \
		printf "Install uv from https://docs.astral.sh/uv/ and rerun make setup.\n"; \
		exit 1; \
	}

deps: check-uv
	uv sync --dev
	uv lock --check

setup: deps
	uv run python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else "Python 3.10 or newer is required")'
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push
	@printf "Local environment is ready.\n"
