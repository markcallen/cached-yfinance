# Task: Direct S3 collector storage and bounded option-history retention

## Context

- Owner: Codex
- Date: 2026-09-25
- Mode: Approval-Required; user approved the recommended direct-S3 design.
- PRD Section: 5.1.5 Managed S3 Options History

## Scope

- Add direct S3 configuration to the options collector and package S3 support
  in the collector image.
- Add tested, opt-in pruning of timestamped option snapshots for filesystem
  and S3 caches.
- Preserve the existing S3 key layout and all non-expired retrieval behavior.
- Out of scope: deleting pre-existing production history before the new
  release is deployed, publishing the release image, and applying GitOps.

## Acceptance Criteria

- A configured collector instantiates `S3Cache` directly and does not require
  a local restored cache.
- S3 option snapshots remain readable at their existing object keys.
- Retention deletes only objects dated strictly before the configured cutoff.
- The collector image installs the optional S3 dependency.

## Test Strategy

- Unit: add filesystem and fake-S3 retention regression tests.
- Integration: build the image and render the GitOps chart against the new
  collector flags.
- Failure path: invalid retention values are rejected and no newer snapshot is
  removed.

## Rollback Strategy

- Revert the package release and keep the existing filesystem collector image;
  direct-S3 objects remain in the same layout and are not mutated by rollback.

## Execution Checklist

- [x] Add failing retention regression tests.
- [x] Implement direct-S3 collector selection and cache pruning.
- [x] Build with the S3 extra, run lint/type/tests, and record evidence.

## Outcome

- Added direct `S3Cache` selection through collector configuration, preserving
  the existing S3 object layout.
- Added opt-in retention for timestamped option snapshots in filesystem and
  S3 caches. The MCA chart configures 30 days.
- Evidence: focused regression tests pass; the non-Docker test suite passes
  130 tests; lint, format, typing, Docker build, and an in-image S3 import
  pass. The existing LocalStack E2E test was skipped because the sandbox does
  not make Docker available to pytest.

# Task: Make manual release tagging idempotent

## Context
- Owner: Codex
- Date: 2026-09-25
- Mode: Autonomous; user requested a fix for failed Release run 36089875149.
- PRD Section: `12.1.1 PyPI Release`
- Requirement IDs: REL-VERSION-1

## Scope
- In scope: prevent a no-op version bump from failing before its missing release tag can be created.
- Out of scope: publishing credentials, release assets, and package runtime behavior.

## Acceptance Criteria
- A manual release creates a missing matching tag when the package version is already correct.
- A rerun reuses an existing tag only when it resolves to the intended commit.
- A conflicting existing tag fails before pushing a release.

## Execution Checklist
- [x] Diagnose the failed release log and confirm the missing tag.
- [x] Add workflow regression coverage for the idempotent release path.
- [x] Update release tagging and run relevant validation.

## Test Strategy
- Unit: `uv run pytest -o addopts= tests/test_workflows.py`.
- Failure-path tests: static workflow assertions require a conflicting-tag failure branch.

## Rollback Strategy
- Trigger: a legitimate manual release is blocked.
- Rollback steps: revert the release workflow and its regression test together.

## Outcome
- Result: Complete. Manual releases now tolerate an already-correct package version, create the missing tag, reuse a tag whose release commit was created from the original workflow commit, and reject ambiguous or conflicting tag state.
- Evidence links/commands: `uv run pytest -o addopts= tests/test_workflows.py`, `uv run pytest -o addopts=`, `uv run ruff check .`, `uv run black --check .`, `uv run mypy cached_yfinance`, `bash -n scripts/find_retry_release_tag.sh`, `git diff --check`.
- PRD updates: Expanded REL-VERSION-1 with safe manual-release rerun behavior.

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
- Result: Confirmed issue #6 was already fixed in CI and added regression coverage to keep mypy enabled across the Python matrix. Hardened release version extraction for issue #7 by supporting required manual dispatch versions, validating SemVer tag shape, checking `pyproject.toml` before build, and emitting clear failures for invalid or mismatched versions. Closed GitHub issues #6 and #7 as completed. Opened PR #30 and addressed Copilot review comments by using `uv version --short` in the release workflow, making the CI matrix regression test tolerant of inline and block-list YAML formatting, and allowing SemVer build metadata in release tags.
- Evidence links/commands: `uv run mypy cached_yfinance` passed; `uv run pytest -o addopts= tests/test_workflows.py` initially failed on issue #7 coverage, then passed 2 tests after the workflow fix; `uv run ruff check .` passed; `uv run black --check .` passed; `uv run pytest -o addopts= --ignore-glob='*e2e.py' --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75` passed 126 tests with 92.35% coverage; GitHub closure comments posted at https://github.com/markcallen/cached-yfinance/issues/6#issuecomment-5463195524 and https://github.com/markcallen/cached-yfinance/issues/7#issuecomment-5463195581; Copilot fix validation passed with `uv run pytest -o addopts= tests/test_workflows.py`, `uv run ruff check .`, `uv run black --check .`, and `uv run mypy cached_yfinance`.
- PRD updates: Added `CI-TYPE-1` under PRD section 10.1.2 and `REL-VERSION-1` under PRD section 12.1.1.
