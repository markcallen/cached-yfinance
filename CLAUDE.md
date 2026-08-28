# CLAUDE.md

This file provides guidance to Claude Code for working in this repository.

## Repository Facts

Use this section for durable repo-specific facts that agents repeatedly need. Prefer facts stored here over re-deriving them with shell commands on every task.

Keep only stable, reviewable metadata here. Do not store secrets, credentials, or ephemeral runtime state.

Suggested facts to record:

- Canonical GitHub repo: `markcallen/cached-yfinance`
- Default branch: `main`
- Primary package manager: `uv`
- Version-file locations agents should check first: `pyproject.toml, uv.lock, .python-version`
- Canonical config files: `pyproject.toml`
- Primary CI workflows: `build.yml, ci.yml`
- Primary release/publish workflows: `release.yml`
- Preferred build/test/lint/format/coverage commands: `make deps`; `uv build`; `uv run ruff check .`; `uv run black --check .`; `uv run mypy cached_yfinance`; `uv run pytest -o addopts= --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75`
- Coverage threshold: `75%`
- Generated or protected paths agents should avoid editing directly: `dist/, .ballast/`

Update this section when those facts change. If live runtime state is required, discover it separately instead of treating it as a durable repo fact.

## Installed agent rules

Created by Ballast. Do not edit this section.

Read and follow these rule files in `.claude/rules/` when they apply:

- `.claude/rules/common/local-dev-badges.md` — Rules for common/local-dev-badges
- `.claude/rules/common/local-dev-env.md` — Rules for common/local-dev-env
- `.claude/rules/common/local-dev-license.md` — Rules for common/local-dev-license
- `.claude/rules/common/local-dev-mcp.md` — Rules for common/local-dev-mcp
- `.claude/rules/common/docs.md` — Rules for common/docs
- `.claude/rules/common/cicd.md` — Rules for common/cicd
- `.claude/rules/common/observability.md` — Rules for common/observability
- `.claude/rules/common/publishing-api.md` — Rules for common/publishing-api
- `.claude/rules/common/publishing-apps.md` — Rules for common/publishing-apps
- `.claude/rules/common/publishing-apt.md` — Rules for common/publishing-apt
- `.claude/rules/common/publishing-brew.md` — Rules for common/publishing-brew
- `.claude/rules/common/publishing-cli.md` — Rules for common/publishing-cli
- `.claude/rules/common/publishing-libraries.md` — Rules for common/publishing-libraries
- `.claude/rules/common/publishing-sdks.md` — Rules for common/publishing-sdks
- `.claude/rules/common/publishing-web.md` — Rules for common/publishing-web
- `.claude/rules/common/git-hooks.md` — Rules for common/git-hooks
- `.claude/rules/common/tasks-task-system.md` — Rules for common/tasks-task-system
- `.claude/rules/common/tasks-todo.md` — Rules for common/tasks-todo
- `.claude/rules/common/plan-lifecycle.md` — Rules for common/plan-lifecycle
- `.claude/rules/python/python-linting.md` — Rules for python/linting
- `.claude/rules/python/python-logging.md` — Rules for python/logging
- `.claude/rules/python/python-testing.md` — Rules for python/testing
- `.claude/rules/docker/docker-linting.md` — Rules for docker/linting
- `.claude/rules/docker/docker-logging.md` — Rules for docker/logging
- `.claude/rules/docker/docker-testing.md` — Rules for docker/testing

## Installed skills

Created by Ballast. Do not edit this section.

Read and use these skill files in `.claude/skills/` when they are relevant:

- `.claude/skills/owasp-security-scan.skill` — run an OWASP-aligned security audit across Go, TypeScript, and Python projects
- `.claude/skills/aws-health-review.skill` — run a weekly read-only AWS health review covering configuration, performance, errors, and warnings
- `.claude/skills/aws-live-health-review.skill` — run a read-only AWS live health review for current EC2, RDS, ALB, CloudWatch alarms, and logs
- `.claude/skills/aws-weekly-security-review.skill` — run a weekly read-only AWS security baseline review and generate a prioritized findings report
- `.claude/skills/github-health-check.skill` — run a comprehensive GitHub repository health check covering CI status, code quality, branch hygiene, and repo configuration
- `.claude/skills/github-pr-copilot-cycle.skill` — create or update a GitHub PR, request Copilot review, triage and fix Copilot comments, push fixes, check CI, and repeat up to three cycles
- `.claude/skills/ballast-audit.skill` — audit AI rule and skill files for context density, duplication, and bloat
- `.claude/skills/ballast-project-maintenance.skill` — inspect, bootstrap, and repair Ballast-managed repository state including .ballast/ local tools
- `.claude/skills/docker-registry-publish.skill` — set up Docker image publishing to GHCR or Docker Hub with public or private registry visibility
