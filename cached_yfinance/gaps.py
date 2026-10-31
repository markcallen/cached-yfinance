"""Read-only checks for missing cached market-price bars."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Sequence
from zoneinfo import ZoneInfo

import pandas as pd
import pandas_market_calendars as mcal

from .cache import CacheKey, FileSystemCache


@dataclass(frozen=True)
class GapFinding:
    symbol: str
    day: date
    interval: str
    expected_bars: int
    missing_bars: int
    first_missing: datetime
    last_missing: datetime
    reason: str


def _interval_duration(interval: str) -> timedelta | None:
    match = re.fullmatch(r"([1-9][0-9]*)(m|h|d)", interval)
    if match is None:
        raise ValueError(f"Unsupported interval for gap audit: {interval}")
    size = int(match.group(1))
    unit = match.group(2)
    if unit == "d":
        if size != 1:
            raise ValueError(f"Unsupported interval for gap audit: {interval}")
        return None
    if unit == "h":
        return timedelta(hours=size)
    return timedelta(minutes=size)


def _valid_observed_times(
    frame: pd.DataFrame, interval: str, timezone: str
) -> pd.DatetimeIndex:
    if not isinstance(frame.index, pd.DatetimeIndex):
        return pd.DatetimeIndex([], tz=timezone)
    if "Close" not in frame.columns.get_level_values(0):
        return pd.DatetimeIndex([], tz=timezone)
    closes = frame["Close"]
    valid = closes.notna()
    if isinstance(valid, pd.DataFrame):
        valid = valid.any(axis=1)
    index = frame.index[valid.to_numpy()]
    if interval == "1d":
        return pd.DatetimeIndex(index)
    if index.tz is None:
        index = index.tz_localize("UTC")
    return index.tz_convert(ZoneInfo(timezone))


def expected_session_times(
    day: date,
    interval: str,
    *,
    calendar_name: str = "NYSE",
    timezone: str = "America/New_York",
) -> pd.DatetimeIndex:
    """Return bar starts for one regular exchange session, including early closes."""
    duration = _interval_duration(interval)
    schedule = mcal.get_calendar(calendar_name).schedule(start_date=day, end_date=day)
    if schedule.empty:
        return pd.DatetimeIndex([], tz=timezone)
    if duration is None:
        return pd.DatetimeIndex([pd.Timestamp(day, tz=timezone)])
    row = schedule.iloc[0]
    return pd.date_range(
        row["market_open"].tz_convert(timezone),
        row["market_close"].tz_convert(timezone),
        freq=duration,
        inclusive="left",
    )


def missing_session_times(
    frame: pd.DataFrame | None,
    expected: pd.DatetimeIndex,
    interval: str,
    timezone: str = "America/New_York",
) -> pd.DatetimeIndex:
    """Return expected starts without a non-null close in the archived frame."""
    if frame is None:
        return expected
    observed = _valid_observed_times(frame, interval, timezone)
    if interval == "1d":
        day = expected[0].date() if len(expected) else None
        return (
            expected
            if day not in {value.date() for value in observed}
            else expected[:0]
        )
    return expected.difference(observed)


def check_cache_gaps(
    cache: FileSystemCache,
    symbols: Sequence[str],
    interval: str,
    *,
    days: int = 30,
    now: datetime | None = None,
    calendar_name: str = "NYSE",
    timezone: str = "America/New_York",
) -> list[GapFinding]:
    """Find missing or null bars in completed sessions over recent calendar days.

    The current local day is excluded because its session may still be in
    progress. The cache is only read; this function never fetches or stores data.
    """
    if days < 1:
        raise ValueError("days must be at least 1")
    _interval_duration(interval)
    local_now = now or datetime.now(ZoneInfo(timezone))
    if local_now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    today = local_now.astimezone(ZoneInfo(timezone)).date()
    schedule = mcal.get_calendar(calendar_name).schedule(
        start_date=today - timedelta(days=days),
        end_date=today - timedelta(days=1),
    )
    findings: list[GapFinding] = []

    for session in schedule.index:
        session_day = session.date()
        expected = expected_session_times(
            session_day, interval, calendar_name=calendar_name, timezone=timezone
        )
        for symbol in symbols:
            frame = cache.load(
                CacheKey(symbol=symbol, interval=interval, day=session_day)
            )
            missing = missing_session_times(frame, expected, interval, timezone)
            reason = "missing archive" if frame is None else "missing bars"
            if len(missing) > 0:
                findings.append(
                    GapFinding(
                        symbol=symbol,
                        day=session_day,
                        interval=interval,
                        expected_bars=len(expected),
                        missing_bars=len(missing),
                        first_missing=missing[0].to_pydatetime(),
                        last_missing=missing[-1].to_pydatetime(),
                        reason=reason,
                    )
                )
    return findings
