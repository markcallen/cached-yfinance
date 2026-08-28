# AGENTS.md

This file provides shared repository guidance for agent tools that read AGENTS.md.

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
- Preferred build/test/lint/format/coverage commands: `<commands>`
- Coverage threshold: `<value>`
- Generated or protected paths agents should avoid editing directly: `dist/, .ballast/`

Update this section when those facts change. If live runtime state is required, discover it separately instead of treating it as a durable repo fact.

## Installed agent rules

Created by Ballast. Do not edit this section.

Read and follow these rule files in `.codex/rules/` when they apply:

- `.codex/rules/common/local-dev-badges.md` — Rules for common/local-dev-badges
- `.codex/rules/common/local-dev-env.md` — Rules for common/local-dev-env
- `.codex/rules/common/local-dev-license.md` — Rules for common/local-dev-license
- `.codex/rules/common/local-dev-mcp.md` — Rules for common/local-dev-mcp
- `.codex/rules/common/docs.md` — Rules for common/docs
- `.codex/rules/common/cicd.md` — Rules for common/cicd
- `.codex/rules/common/observability.md` — Rules for common/observability
- `.codex/rules/common/publishing-api.md` — Rules for common/publishing-api
- `.codex/rules/common/publishing-apps.md` — Rules for common/publishing-apps
- `.codex/rules/common/publishing-apt.md` — Rules for common/publishing-apt
- `.codex/rules/common/publishing-brew.md` — Rules for common/publishing-brew
- `.codex/rules/common/publishing-cli.md` — Rules for common/publishing-cli
- `.codex/rules/common/publishing-libraries.md` — Rules for common/publishing-libraries
- `.codex/rules/common/publishing-sdks.md` — Rules for common/publishing-sdks
- `.codex/rules/common/publishing-web.md` — Rules for common/publishing-web
- `.codex/rules/common/git-hooks.md` — Rules for common/git-hooks
- `.codex/rules/common/tasks-task-system.md` — Rules for common/tasks-task-system
- `.codex/rules/common/tasks-todo.md` — Rules for common/tasks-todo
- `.codex/rules/common/plan-lifecycle.md` — Rules for common/plan-lifecycle
- `.codex/rules/python/python-linting.md` — Rules for python/linting
- `.codex/rules/python/python-logging.md` — Rules for python/logging
- `.codex/rules/python/python-testing.md` — Rules for python/testing
- `.codex/rules/docker/docker-linting.md` — Rules for docker/linting
- `.codex/rules/docker/docker-logging.md` — Rules for docker/logging
- `.codex/rules/docker/docker-testing.md` — Rules for docker/testing

## Installed skills

Created by Ballast. Do not edit this section.

Read and use these skill files in `.codex/skills/` when they are relevant:

- `.codex/skills/owasp-security-scan/SKILL.md` — run an OWASP-aligned security audit across Go, TypeScript, and Python projects
- `.codex/skills/aws-health-review/SKILL.md` — run a weekly read-only AWS health review covering configuration, performance, errors, and warnings
- `.codex/skills/aws-live-health-review/SKILL.md` — run a read-only AWS live health review for current EC2, RDS, ALB, CloudWatch alarms, and logs
- `.codex/skills/aws-weekly-security-review/SKILL.md` — run a weekly read-only AWS security baseline review and generate a prioritized findings report
- `.codex/skills/github-health-check/SKILL.md` — run a comprehensive GitHub repository health check covering CI status, code quality, branch hygiene, and repo configuration
- `.codex/skills/github-pr-copilot-cycle/SKILL.md` — create or update a GitHub PR, request Copilot review, triage and fix Copilot comments, push fixes, check CI, and repeat up to three cycles
- `.codex/skills/ballast-audit/SKILL.md` — audit AI rule and skill files for context density, duplication, and bloat
- `.codex/skills/ballast-project-maintenance/SKILL.md` — inspect, bootstrap, and repair Ballast-managed repository state including .ballast/ local tools
- `.codex/skills/docker-registry-publish/SKILL.md` — set up Docker image publishing to GHCR or Docker Hub with public or private registry visibility
