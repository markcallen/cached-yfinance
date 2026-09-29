# Plan: Current-session price freshness

**Status:** In Progress
**Branch:** `fix/current-session-price-freshness`
**Created:** 2026-09-29
**Related ADRs:** None

## Problem

The production hourly price Job exits successfully while returning the prior
trading day's bars or no bars at all. On September 29, none of the five
configured ticker prefixes received a current-day one-minute object. A manual
Job reported zero successful tickers and still reached Kubernetes Complete.

## Approach

- Make an explicit current-session one-minute request fetch upstream on every
  execution and persist the response. Correct the generic intraday fetch bound
  so a missing current day is fetched through the current instant.
- Validate each ticker against the NYSE session date and market close. Reject
  empty, prior-session, or lagging responses and return a nonzero process status
  when any required ticker fails. Skip known non-trading days.
- Preserve the S3 key layout and the independent options collector.

## Files Affected

- `cached_yfinance/client.py` — fetch the active intraday session.
- `tools/ticker_collector.py` — validate data and propagate failures.
- `tests/test_client.py`, `tests/test_ticker_collector_s3.py` — regression tests.
- `PRD.md`, `tasks/todo.md`, `tasks/lessons.md` — contract and evidence.

## Phases

- [x] Add failing current-day fetch and stale/empty failure tests.
- [x] Implement fresh fetch and current-day range bound.
- [x] Implement session validation and nonzero exit behavior.
- [x] Run targeted and full checks; open PR and check review/CI.

## Verification

Run the relevant pytest modules first, then the repository's Ruff, Black,
Mypy, build, and full pytest coverage checks. Confirm a mocked current-day
request calls upstream even when today's cache already exists. Check a market
holiday skip, a regular session, an early close, stale bars, and zero data.

## Rollback

Revert the source change before releasing a new image, or restore the previous
image in GitOps if a release regresses. The existing S3 objects remain intact;
the previous image's false-success behavior would need continued monitoring.

## Alternatives Rejected

| Option | Why rejected |
| --- | --- |
| Accept Kubernetes Complete as evidence of data freshness | The September 29 Job completed after collecting zero tickers. |
| Fix only the fetch end bound | A partially cached current day would still bypass upstream refresh. |

## Change Log

| Date | Change |
| --- | --- |
| 2026-09-29 | Plan created from production Job and S3 evidence. |
| 2026-09-29 | Local checks passed: 149 tests, 91% coverage, Ruff, Black, Mypy, and package build. |
| 2026-09-29 | PR #41 opened; all four CI checks passed. Copilot review was requested but quota limited. |
