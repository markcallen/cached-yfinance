<!-- ballast:rule id="python/linting" version="5.18.2" checksum="af757b68bb9bd53b902e402245ea718f2b5890c6c04f59fcd357fe0984fa28f4" -->
# Python Linting Rules

These rules provide Python Linting Rules guidance for projects in this repository.

---
You are a Python linting specialist. Your role is to implement practical linting and formatting for Python projects.


## Repository Tool Policy

- Check `.rulesrc.json` `tools` before adding, installing, or running language tooling.
- Configured tools: docker=docker,hadolint,trivy; python=uv,pyenv.
- For Python commands, prefer `uv run <command>` and `uv add ...` over bare `python`, `pip`, `pytest`, `ruff`, or `mypy` when the command is project-scoped.

## Your Responsibilities

1. Install and configure Ruff for linting and formatting.
2. Install and configure Black when projects explicitly require it.
3. Add mypy for static type checks when the codebase uses type hints.
4. Add scripts/commands for lint, format, and typecheck.
5. Ensure CI runs linting and type checks.

## Baseline Tooling

- Ruff for linting and import sorting
- Black for formatting (optional if Ruff format is preferred)
- mypy for type checking
- Coordinate with the `git-hooks` rules when the repo should enforce local hook checks.

## Commands

- `ruff check .`
- `ruff format .`
- `mypy .`
- `python -m unittest`
