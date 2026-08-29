# Task: LocalStack S3 E2E Coverage

## Context
- Owner: Codex
- Date: 2026-08-28
- Mode: Autonomous
- PRD Section: 10.1 Testing Strategy
- Requirement IDs: CORE-E2E-1, S3-E2E-1

## Scope
- In scope: Merge latest `main`, confirm existing S3 tests, add LocalStack-backed S3 e2e coverage, add core public-client e2e coverage, and run the full test suite with coverage.
- Out of scope: Production S3 credential handling changes, publishing workflow changes, and non-S3 cache behavior changes.

## Acceptance Criteria
- AC1: Branch includes latest `origin/main`.
- AC2: Existing S3 unit tests are identified and pass.
- AC3: LocalStack e2e tests exercise `S3Cache` market data and option chain round trips through boto3 against a Docker Compose-started service.
- AC4: Core e2e tests exercise public client price download cache miss-to-hit behavior and option chain storage/reload behavior.
- AC5: Full local verification passes with coverage at or above 75%.

## Constraints
- Preserve existing user work in the dirty worktree.
- Preserve generated `.ballast/` contents.
- Keep LocalStack coverage deterministic and isolated to test-created buckets/objects.
- Prefer `uv run` for Python tooling.

## Risks and Tradeoffs
- Risk: Docker or LocalStack image availability can make e2e verification unavailable on some machines.
- Tradeoff: The e2e test may be slower than fake-client unit tests, but it verifies real S3-compatible API behavior.

## Execution Checklist
- [x] Merge latest `origin/main` into `feature/s3-cache`.
- [x] Confirm existing S3 unit tests.
- [x] Add PRD acceptance criteria for S3-compatible e2e coverage.
- [x] Add LocalStack-backed e2e test.
- [x] Add core public-client e2e tests for price and option workflows.
- [x] Add separate GitHub Actions e2e job using Docker Compose LocalStack.
- [x] Run targeted and full verification commands.
- [x] Record final evidence and outcome.

## Test Strategy
- Unit: `uv run pytest tests/test_s3_cache.py`
- Integration: N/A
- E2E: `uv run pytest tests/test_client_e2e.py`; `docker compose up --detach localstack`; `LOCALSTACK_S3_ENDPOINT=http://127.0.0.1:4566 uv run pytest tests/test_s3_cache_e2e.py`
- Failure-path tests: Existing fake-client S3 missing-object tests plus LocalStack test skip when Docker is unavailable.
- Requirement-to-test mapping: CORE-E2E-1 maps to `tests/test_client_e2e.py`; S3-E2E-1 maps to `tests/test_s3_cache_e2e.py`.

## Rollback Strategy
- Trigger: LocalStack e2e additions prove flaky or require production behavior changes.
- Rollback steps: Revert the LocalStack test/dependency/PRD changes while preserving the `main` merge.
- Validation after rollback: Re-run existing S3 unit tests and full coverage gate.

## Outcome
- Result: Merged latest `origin/main`, confirmed existing fake-client S3 unit tests, added a Docker Compose LocalStack service, added a LocalStack-backed S3 e2e test for market data, option chains, and object listings, added core public-client e2e tests for price download and option chain cache workflows, and split CI e2e execution into a dedicated Docker Compose-backed job.
- Evidence links/commands: `uv run pytest tests/test_s3_cache.py` passed 4 tests before Copilot fixes; `uv run pytest tests/test_s3_cache_e2e.py` passed 1 self-started LocalStack e2e test; `docker compose config` passed; `docker compose up --detach localstack` started LocalStack; `curl -s http://127.0.0.1:4566/_localstack/health` reported S3 available; `LOCALSTACK_S3_ENDPOINT=http://127.0.0.1:4566 uv run pytest tests/test_s3_cache_e2e.py` passed 1 Compose-backed LocalStack e2e test; `uv run pytest tests/test_client_e2e.py` passed 2 core e2e tests; `LOCALSTACK_S3_ENDPOINT=http://127.0.0.1:4566 uv run pytest tests/test_client_e2e.py tests/test_s3_cache_e2e.py` passed 3 e2e tests; `uv run ruff check .` passed; `uv run black --check .` passed; `uv run mypy cached_yfinance` passed; `uv run pytest -o addopts= tests/test_cache.py tests/test_client.py tests/test_s3_cache.py --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75` passed 121 unit tests with 92.17% coverage before Copilot fixes; `LOCALSTACK_S3_ENDPOINT=http://127.0.0.1:4566 uv run pytest -o addopts= --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75` passed 124 tests with 92.33% coverage before Copilot fixes; CI e2e job split validated with `docker compose config`, the unit-test CI command, and the e2e CI command; Copilot cycle 1 fixes validated with `uv run pytest -o addopts= tests/test_s3_cache.py` passing 5 tests, `LOCALSTACK_S3_ENDPOINT=http://127.0.0.1:4566 uv run pytest -o addopts= tests/test_client_e2e.py tests/test_s3_cache_e2e.py` passing 3 e2e tests, `uv run ruff check .`, `uv run black --check .`, `uv run mypy cached_yfinance`, and `uv run pytest -o addopts= tests/test_cache.py tests/test_client.py tests/test_s3_cache.py --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75` passing 122 unit tests with 92.18% coverage; Copilot cycle 2 fixes validated with `uv run pytest -o addopts= tests/test_s3_cache.py` passing 6 tests, `uv run pytest -o addopts= --ignore-glob='*e2e.py' --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75` passing 123 unit tests with 92.18% coverage, `LOCALSTACK_S3_ENDPOINT=http://127.0.0.1:4566 uv run pytest -o addopts= tests/test_client_e2e.py tests/test_s3_cache_e2e.py` passing 3 e2e tests, `uv run ruff check .`, `uv run black --check .`, `uv run mypy cached_yfinance`, and `git diff --check`; Copilot cycle 3 fixes validated with `uv run pytest -o addopts= tests/test_s3_cache.py` passing 7 tests, `docker compose config`, `LOCALSTACK_S3_ENDPOINT=http://127.0.0.1:4566 uv run pytest -o addopts= tests/test_client_e2e.py tests/test_s3_cache_e2e.py` passing 3 e2e tests, `uv run ruff check .`, `uv run black --check .`, `uv run mypy cached_yfinance`, `uv run pytest -o addopts= --ignore-glob='*e2e.py' --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75` passing 124 unit tests with 92.35% coverage, and `git diff --check`.
- PRD updates: Added `CORE-E2E-1` and `S3-E2E-1` under PRD section 10.1.2 Integration Tests.
