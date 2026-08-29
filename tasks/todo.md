# Task: Resolve GitHub Issues 6 and 7

## Context
- Owner: Codex
- Date: 2026-08-29
- Mode: Autonomous
- PRD Section: 10.1 Testing Strategy; 12.1.1 PyPI Release
- Requirement IDs: CI-TYPE-1, REL-VERSION-1

## Scope
- In scope: Verify and preserve CI mypy execution for issue #6, harden release version extraction/validation for issue #7, add regression coverage for workflow requirements, and close both GitHub issues with evidence.
- Out of scope: Publishing credentials, release creation action replacement, package runtime behavior changes, and Docker publishing changes.

## Acceptance Criteria
- AC1: `.github/workflows/ci.yml` runs `uv run mypy cached_yfinance` in the Python 3.10, 3.11, and 3.12 matrix.
- AC2: `uv run mypy cached_yfinance` passes locally.
- AC3: `.github/workflows/release.yml` validates tag/manual versions before building release artifacts.
- AC4: Release version validation rejects malformed or mismatched versions with clear errors.
- AC5: Relevant lint, typing, workflow regression tests, and coverage tests pass.

## Constraints
- Preserve existing user work in the dirty worktree.
- Preserve generated `.ballast/` contents.
- Prefer `uv run` for Python tooling.

## Risks and Tradeoffs
- Risk: GitHub Actions expression contexts differ between tag and manual dispatch events.
- Tradeoff: Version mismatch now fails early instead of attempting to rewrite `pyproject.toml` during release.

## Execution Checklist
- [x] Inspect the two open GitHub issues.
- [x] Confirm current CI mypy workflow state and local mypy result.
- [x] Add PRD requirements for CI type checking and release version validation.
- [x] Add workflow regression tests.
- [x] Harden release version extraction and validation.
- [x] Run verification commands.
- [x] Close issues #6 and #7 with evidence.

## Test Strategy
- Unit: `uv run pytest tests/test_workflows.py`
- Integration: N/A
- E2E: N/A
- Failure-path tests: Static workflow checks verify malformed release inputs are rejected before build.
- Requirement-to-test mapping: CI-TYPE-1 and REL-VERSION-1 map to `tests/test_workflows.py`.

## Rollback Strategy
- Trigger: Release workflow validation blocks legitimate SemVer tags or manual releases.
- Rollback steps: Revert the release workflow and workflow regression test changes.
- Validation after rollback: Re-run mypy, lint, and workflow tests.

## Outcome
- Result: Confirmed issue #6 was already fixed in CI and added regression coverage to keep mypy enabled across the Python matrix. Hardened release version extraction for issue #7 by supporting required manual dispatch versions, validating SemVer tag shape, checking `pyproject.toml` before build, and emitting clear failures for invalid or mismatched versions. Closed GitHub issues #6 and #7 as completed.
- Evidence links/commands: `uv run mypy cached_yfinance` passed; `uv run pytest -o addopts= tests/test_workflows.py` initially failed on issue #7 coverage, then passed 2 tests after the workflow fix; `uv run ruff check .` passed; `uv run black --check .` passed; `uv run pytest -o addopts= --ignore-glob='*e2e.py' --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75` passed 126 tests with 92.35% coverage; GitHub closure comments posted at https://github.com/markcallen/cached-yfinance/issues/6#issuecomment-5463195524 and https://github.com/markcallen/cached-yfinance/issues/7#issuecomment-5463195581.
- PRD updates: Added `CI-TYPE-1` under PRD section 10.1.2 and `REL-VERSION-1` under PRD section 12.1.1.
