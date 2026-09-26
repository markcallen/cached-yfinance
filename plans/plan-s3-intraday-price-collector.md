# Plan: S3 Intraday Price Collector

**Status:** Awaiting image release
**Branch:** feat/s3-intraday-price-collector
**Created:** 2026-09-26
**Related ADRs:** _(none)_

## Problem

`ticker_collector.py` stores one-minute price data only in a filesystem cache,
which is lost when it runs in an ephemeral Kubernetes Job. The MCA deployment
needs an independent hourly collector that writes current-session data directly
to S3.

## Approach

Give `ticker_collector.py` the established S3 configuration contract used by
`options_collector.py`. For intraday intervals, request `period="1d"` on every
run so the current session is fetched again and its S3 day object is replaced
with the latest complete response. Add a second timezone-aware Helm CronJob
that invokes this collector hourly, while keeping the existing options job
unchanged.

## Files Affected

- `PRD.md` - define the managed S3 intraday-price requirement.
- `tools/ticker_collector.py` - select S3 and refresh current intraday data.
- `tests/` - cover S3 selection and current-session refresh behavior.
- `tools/ticker_collector_config.json`, `tools/README.md`, `docs/S3_CACHE.md` -
  document the shared S3 collector configuration.
- `apps/cached-yfinance/` in `mca-gitops` - render the independent hourly Job.

## Phases

- [x] Phase 1: Confirm the existing ticker collector and S3 cache layout.
- [x] Phase 2: Add direct-S3 selection and fresh intraday collection.
- [x] Phase 3: Add tests, documentation, and the independent Helm CronJob.
- [x] Phase 4: Validate package tests, image build, and rendered manifests.

## Verification

- Focused tests prove S3 configuration is passed to `S3Cache` and a one-minute
  run requests the current session directly from Yahoo on each invocation.
- Run the package lint, formatter, type checker, and test suite.
- Render and lint the production Helm chart, verifying separate options and
  price CronJobs and no accidental local cache volume when S3 is enabled.

## Alternatives Rejected

| Option | Why rejected |
| --- | --- |
| Run the existing filesystem-only ticker collector in Kubernetes | Its output disappears when the Job exits. |
| Add price downloads to the options collector | It couples independent workloads, schedules, and failures. |
| Reuse a cached partial intraday day | It leaves the newest bars stale after the first run. |

## Open Questions

None. The requested price symbols are IWM, AMZN, NVDA, AAPL, and SPCX.

## Change Log

| Date | Change |
| --- | --- |
| 2026-09-26 | Plan created. |
| 2026-09-26 | Implemented and validated locally; production activation waits for a published immutable image. |
