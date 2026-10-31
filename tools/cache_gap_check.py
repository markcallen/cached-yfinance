#!/usr/bin/env python3
"""Report missing cached price bars without downloading or changing data."""

import argparse
import json
import sys
from datetime import datetime
from datetime import timezone as datetime_timezone
from pathlib import Path
from typing import Sequence


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cached_yfinance.gaps import check_cache_gaps
from tools.ticker_collector import create_cache


def main(argv: Sequence[str] | None = None, *, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit cached market-price gaps")
    parser.add_argument("--config", required=True, help="Collector JSON configuration")
    parser.add_argument("--days", type=int, default=30, help="Calendar days to inspect")
    parser.add_argument("--interval", help="Override the configured interval")
    parser.add_argument("--calendar", default="NYSE", help="Exchange calendar name")
    parser.add_argument("--json-output", help="Write a machine-readable repair report")
    args = parser.parse_args(argv)

    try:
        with open(args.config, encoding="utf-8") as handle:
            config = json.load(handle)
        tickers = config["tickers"]
        if not isinstance(tickers, list) or not tickers:
            raise ValueError("tickers must be a nonempty list")
        interval = args.interval or config["interval"]
        timezone = config.get("timezone", "America/New_York")
        findings = check_cache_gaps(
            create_cache(config),
            tickers,
            interval,
            days=args.days,
            now=now,
            calendar_name=args.calendar,
            timezone=timezone,
        )
        if args.json_output:
            report = {
                "schema": 1,
                "generated_at": (
                    now or datetime.now(datetime_timezone.utc)
                ).isoformat(),
                "days": args.days,
                "calendar": args.calendar,
                "timezone": timezone,
                "interval": interval,
                "tickers": tickers,
                "findings": [
                    {"symbol": finding.symbol, "day": finding.day.isoformat()}
                    for finding in findings
                ],
            }
            Path(args.json_output).write_text(json.dumps(report), encoding="utf-8")
    except Exception as exc:
        # A cache or provider read error must not look like a clean audit.
        print(f"Gap audit failed: {exc}", file=sys.stderr)
        return 2

    for finding in findings:
        print(
            f"{finding.symbol} {finding.day} {finding.interval}: "
            f"missing {finding.missing_bars}/{finding.expected_bars} bars "
            f"({finding.reason}; first {finding.first_missing.isoformat()}, "
            f"last {finding.last_missing.isoformat()})"
        )
    if findings:
        print(f"Gap audit found {len(findings)} affected ticker-sessions")
        return 1
    print(f"Gap audit found no gaps across {args.days} calendar days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
