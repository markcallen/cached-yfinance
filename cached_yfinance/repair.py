"""Conservative repair of archived bars identified by a gap audit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

import pandas as pd

from .cache import CacheKey, FileSystemCache
from .gaps import expected_session_times, missing_session_times


BarFetcher = Callable[[str, date, str], pd.DataFrame]


@dataclass(frozen=True)
class RepairOutcome:
    symbol: str
    day: date
    before_missing: int
    after_missing: int
    error: str | None = None


def _valid_fetched_rows(
    frame: pd.DataFrame, expected: pd.DatetimeIndex, interval: str, timezone: str
) -> pd.DataFrame:
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError("downloaded bars have no datetime index")
    if "Close" not in frame.columns.get_level_values(0):
        raise ValueError("downloaded bars have no Close column")
    index = frame.index
    if interval == "1d":
        in_session = index.date == expected[0].date()
    else:
        if index.tz is None:
            index = index.tz_localize("UTC")
        in_session = index.tz_convert(timezone).isin(expected)
    closes = frame["Close"]
    valid = closes.notna()
    if isinstance(valid, pd.DataFrame):
        valid = valid.any(axis=1)
    return frame.loc[in_session & valid.to_numpy()]


def repair_gap(
    cache: FileSystemCache,
    symbol: str,
    day: date,
    interval: str,
    fetch: BarFetcher,
    *,
    calendar_name: str = "NYSE",
    timezone: str = "America/New_York",
) -> RepairOutcome:
    """Fetch one affected session and store only a merge that reduces missing bars."""
    expected = expected_session_times(
        day, interval, calendar_name=calendar_name, timezone=timezone
    )
    if expected.empty:
        raise ValueError(f"{day} is not a {calendar_name} session")
    key = CacheKey(symbol=symbol, interval=interval, day=day)
    existing = cache.load(key)
    before = len(missing_session_times(existing, expected, interval, timezone))
    if before == 0:
        return RepairOutcome(symbol, day, 0, 0)

    try:
        fetched = _valid_fetched_rows(
            fetch(symbol, day, interval), expected, interval, timezone
        )
        if fetched.empty:
            return RepairOutcome(symbol, day, before, before, "no valid bars returned")
        if existing is not None and not existing.empty:
            if not existing.columns.equals(fetched.columns):
                return RepairOutcome(
                    symbol,
                    day,
                    before,
                    before,
                    "downloaded columns differ from archive",
                )
            merged = existing.combine_first(fetched).sort_index()
        else:
            merged = fetched.sort_index()
        after = len(missing_session_times(merged, expected, interval, timezone))
        if after < before:
            cache.store(key, merged)
        return RepairOutcome(symbol, day, before, after)
    except Exception as exc:
        return RepairOutcome(symbol, day, before, before, str(exc))


def fetch_yahoo_session(symbol: str, day: date, interval: str) -> pd.DataFrame:
    """Fetch one session so intraday provider limits do not truncate the request."""
    import yfinance as yf

    return yf.download(
        symbol,
        start=day.isoformat(),
        end=(day + timedelta(days=1)).isoformat(),
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )
