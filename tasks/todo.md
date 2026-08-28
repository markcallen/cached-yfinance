# Task: Repository Rule Compliance Review

## Context
- Owner: Codex
- Date: 2026-08-27
- Mode: Autonomous
- PRD Section: N/A - repository maintenance only
- Requirement IDs: AGENTS.md repository rules, `.codex/rules/`

## Scope
- In scope: Audit and correct local rule-compliance drift for Python, Docker, CI, docs, hooks, Dependabot, and package metadata.
- Out of scope: Product behavior changes, release-process redesign, external GitHub issue triage.

## Acceptance Criteria
- AC1: Configured Python lint, format, typecheck, and coverage commands pass locally.
- AC2: CI workflows include required concurrency and coverage gates.
- AC3: Local hooks include fast commit checks, gitleaks, and a pre-push test command.
- AC4: Docker runtime avoids root and keeps cache directory writable.
- AC5: README and dependency automation metadata do not contain stale placeholders.

## Constraints
- Preserve existing user work in the dirty worktree.
- Do not change application behavior.

## Risks and Tradeoffs
- Risk: Full Docker build and scanner validation may be unavailable locally if Docker or configured scanners are missing.
- Tradeoff: Release workflow remains tag-driven; a full Ballast bump-and-tag redesign is larger than this maintenance pass.

## Execution Checklist
- [x] Read AGENTS execution framework and repo rule files.
- [x] Inspect workflows, hooks, Docker config, docs, package metadata, and tests.
- [x] Apply low-risk compliance fixes.
- [x] Run verification commands and record results.

## Test Strategy
- Unit: `uv run pytest --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75`
- Integration: N/A
- E2E: N/A
- Failure-path tests: Existing cache and client tests.
- Requirement-to-test mapping: AC1 maps to Ruff, Black, mypy, and pytest coverage gates.

## Rollback Strategy
- Trigger: Any verification failure caused by these maintenance edits.
- Rollback steps: Revert only this task's edits and rerun the original checks.
- Validation after rollback: Re-run Ruff, Black, mypy, and pytest coverage.

## Outcome
- Result: Compliance drift fixed for local Python gates, CI concurrency/coverage/typecheck, pre-commit/pre-push hooks, non-root Docker runtime, README metadata, Dependabot metadata, and package author metadata.
- Evidence links/commands: `uv run ruff check .`; `uv run black --check .`; `uv run mypy cached_yfinance`; `uv run pytest --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75`; `uv run pre-commit run --all-files`; `uv run pre-commit run --hook-stage pre-push --all-files`; `docker build --pull --tag local/cached-yfinance:rule-check .`; `docker run --rm --entrypoint id local/cached-yfinance:rule-check -u`; `docker run --rm --entrypoint uv local/cached-yfinance:rule-check run python tools/download_data.py --help`; `git diff --check`.
- PRD updates: None.
