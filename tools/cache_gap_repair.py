#!/usr/bin/env python3
"""Consume a fresh gap report and conservatively repair affected sessions."""

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfo


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cached_yfinance.repair import fetch_yahoo_session, repair_gap
from tools.ticker_collector import DEFAULT_CONFIG, create_cache


def _validated_targets(
    report: dict, config: dict, now: datetime
) -> list[tuple[str, date]]:
    if report.get("schema") != 1:
        raise ValueError("unsupported gap report schema")
    if report.get("interval") != config["interval"]:
        raise ValueError("gap report interval differs from collector configuration")
    if set(report.get("tickers", [])) != set(config["tickers"]):
        raise ValueError("gap report tickers differ from collector configuration")
    if report.get("timezone") != config.get("timezone", "America/New_York"):
        raise ValueError("gap report timezone differs from collector configuration")
    days = report.get("days")
    if not isinstance(days, int) or not 1 <= days <= 30:
        raise ValueError("gap report window must be between 1 and 30 days")
    generated = datetime.fromisoformat(report["generated_at"])
    if generated.tzinfo is None or not timedelta(
        minutes=-5
    ) <= now - generated <= timedelta(hours=1):
        raise ValueError("gap report is stale or has no timezone")
    today = now.astimezone(ZoneInfo(report["timezone"])).date()
    findings = report["findings"]
    if not isinstance(findings, list):
        raise ValueError("gap report findings must be a list")
    targets = set()
    for finding in findings:
        symbol = finding["symbol"]
        day = date.fromisoformat(finding["day"])
        if (
            symbol not in config["tickers"]
            or not today - timedelta(days=days) <= day < today
        ):
            raise ValueError("gap report contains an out-of-scope target")
        targets.add((symbol, day))
    return sorted(targets, key=lambda target: (target[1], target[0]), reverse=True)


def main(argv: Sequence[str] | None = None, *, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repair cached market-price gaps")
    parser.add_argument("--config", required=True, help="Collector JSON configuration")
    parser.add_argument(
        "--report", required=True, help="JSON report from cache_gap_check"
    )
    parser.add_argument("--max-sessions", type=int, default=200)
    args = parser.parse_args(argv)
    try:
        with open(args.config, encoding="utf-8") as handle:
            config = {**DEFAULT_CONFIG, **json.load(handle)}
        with open(args.report, encoding="utf-8") as handle:
            report = json.load(handle)
        if args.max_sessions < 1:
            raise ValueError("max-sessions must be at least 1")
        run_now = now or datetime.now(timezone.utc)
        targets = _validated_targets(report, config, run_now)
        cache = create_cache(config)
    except Exception as exc:
        print(f"Gap repair cannot start: {exc}", file=sys.stderr)
        return 2

    deferred = max(0, len(targets) - args.max_sessions)
    repaired = 0
    already_complete = 0
    unresolved = 0
    provider_unavailable = 0
    provider_missing = 0
    today = run_now.astimezone(ZoneInfo(report["timezone"])).date()
    # Yahoo requires the start of a 1m request to be within its rolling
    # 30-day window. The one-day request starts at midnight, so the day
    # exactly 30 calendar days ago is not safe for a noon repair run.
    earliest_full_session = today - timedelta(days=29)
    for symbol, day in targets[: args.max_sessions]:
        if config["interval"] == "1m" and day < earliest_full_session:
            provider_unavailable += 1
            unresolved += 1
            print(
                f"{symbol} {day}: unresolved; outside Yahoo 1m full-session "
                "retrieval window"
            )
            continue
        try:
            outcome = repair_gap(
                cache,
                symbol,
                day,
                config["interval"],
                fetch_yahoo_session,
                calendar_name=report["calendar"],
                timezone=report["timezone"],
            )
            print(
                f"{symbol} {day}: missing {outcome.before_missing} -> "
                f"{outcome.after_missing} bars"
                + (f"; {outcome.error}" if outcome.error else "")
            )
            if outcome.after_missing or outcome.error:
                unresolved += 1
                provider_missing += 1
            elif outcome.before_missing:
                repaired += 1
            else:
                already_complete += 1
        except Exception as exc:
            print(f"{symbol} {day}: repair failed: {exc}", file=sys.stderr)
            unresolved += 1
    print(
        f"Gap repair summary: repaired={repaired} "
        f"already_complete={already_complete} unresolved={unresolved} "
        f"provider_unavailable={provider_unavailable} "
        f"provider_missing={provider_missing} deferred={deferred}"
    )
    return 1 if unresolved or deferred else 0


if __name__ == "__main__":
    sys.exit(main())
