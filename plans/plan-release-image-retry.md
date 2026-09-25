# Plan: Release Image Retry

**Status:** In Progress
**Branch:** `fix/release-image-retry`
**Created:** 2026-09-25
**Related ADRs:** _(none)_

## Problem

The manually released `v0.2.1` GitHub Release did not produce the Docker tag
required by the MCA collector. `docker/metadata-action` receives the `main`
ref for a manual dispatch, so its tag-event rules produce no version tag.

## Approach

Add the validated release tag as an explicit Docker metadata tag. Make a
release retry detect an existing GitHub Release and skip only duplicate release
and asset creation, allowing it to build and publish the missing image.

## Files Affected

- `.github/workflows/release.yml` - tag manual images and allow a publish retry.
- `tests/test_workflows.py` - regression assertions for the release contract.
- `PRD.md` - define the image publishing/retry acceptance criteria.

## Phases

- [x] Phase 1: Diagnose missing v0.2.1 Docker tag.
- [x] Phase 2: Implement explicit version tag and release-exists gate.
- [x] Phase 3: Validate the workflow repair locally; publish and production Job verification remain pending merge.
- [ ] Phase 4: Document outcome and graduate the plan.

## Verification

- Run targeted release workflow tests, lint, format, typing, and the full test suite.
- Merge the workflow repair, manually rerun the patch release, and verify
  `markcallen/cached-yfinance:v0.2.1` is pullable by the MCA Job.

## Alternatives Rejected

| Option | Why rejected |
| --- | --- |
| Build/push locally | Bypasses the audited release pipeline and its registry credential scope. |
| Retag an older image | Would omit the direct-S3 collector code shipped in v0.2.1. |

## Open Questions

None.

## Change Log

| Date | Change |
| --- | --- |
| 2026-09-25 | Plan created after production image-pull diagnosis. |
