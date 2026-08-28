# Plan: LocalStack S3 E2E

**Status:** In Progress
**Branch:** `feature/s3-cache`
**Created:** 2026-08-28
**Related ADRs:** _(none)_

## Problem

`S3Cache` has unit coverage through a fake S3 client, but it lacks an end-to-end check against an S3-compatible HTTP service. The broader library also benefits from public-client e2e coverage that proves the main price and option cache workflows through real cache persistence.

## Approach

Add pytest e2e tests that can use a Docker Compose-started LocalStack endpoint, create a bucket with boto3, write market data and option chain data through `S3Cache`, and verify reads plus listings through the same S3-compatible endpoint. Add deterministic public-client e2e tests with real `FileSystemCache` storage and mocked upstream yfinance responses for price and option workflows.

## Files Affected

- `PRD.md` - add S3-compatible cache acceptance criteria.
- `pyproject.toml` / `uv.lock` - add dev dependencies required for LocalStack e2e tests.
- `docker-compose.yml` - define the LocalStack S3 service for local e2e runs.
- `tests/test_client_e2e.py` - add public client e2e coverage for price and option workflows.
- `tests/test_s3_cache_e2e.py` - add LocalStack-backed e2e coverage.
- `tasks/todo.md` - record checklist, evidence, and outcome for this branch task.

## Phases

- [x] Phase 1: Explore and confirm existing S3 unit coverage.
- [x] Phase 2: Add LocalStack e2e test and dependency configuration.
- [x] Phase 3: Run targeted and full verification.
- [x] Phase 4: Record evidence and cleanup.

## Verification

- `uv run pytest tests/test_s3_cache.py`
- `uv run pytest tests/test_client_e2e.py`
- `docker compose up --detach localstack`
- `LOCALSTACK_S3_ENDPOINT=http://127.0.0.1:4566 uv run pytest tests/test_s3_cache_e2e.py`
- `uv run ruff check .`
- `uv run black --check .`
- `uv run mypy cached_yfinance`
- `uv run pytest -o addopts= --cov=cached_yfinance --cov-report=term-missing --cov-fail-under=75`

## Alternatives Rejected

| Option | Why rejected |
| --- | --- |
| Continue using only fake S3 client tests | Does not verify boto3 and S3-compatible HTTP semantics. |
| Require a manually running LocalStack service | Adds hidden local setup and makes CI/local behavior less reproducible. |

## Open Questions

None.

## Change Log

| Date | Change |
| --- | --- |
| 2026-08-28 | Plan created after merging `origin/main`. |
| 2026-08-28 | Added LocalStack S3 e2e coverage and completed verification. |
| 2026-08-28 | Added Docker Compose LocalStack service and verified e2e tests against the Compose endpoint. |
| 2026-08-28 | Added public-client filesystem e2e tests for price and option cache workflows. |
