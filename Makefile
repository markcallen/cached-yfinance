SHELL := /bin/bash

.PHONY: help check-uv check-python deps setup

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

check-python: check-uv
	uv run --no-sync python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else "Python 3.10 or newer is required")'

deps: check-python
	uv sync --dev
	uv lock --check

setup: deps
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push
	@printf "Local environment is ready.\n"
