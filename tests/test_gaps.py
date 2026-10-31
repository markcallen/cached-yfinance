import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from cached_yfinance.cache import CacheKey
from cached_yfinance.gaps import check_cache_gaps
from tools import cache_gap_check


class ReadOnlyCache:
    def __init__(self, frames: dict[CacheKey, pd.DataFrame]) -> None:
        self.frames = frames

    def load(self, key: CacheKey) -> pd.DataFrame | None:
        return self.frames.get(key)

    def store(self, key: CacheKey, frame: pd.DataFrame) -> None:
        raise AssertionError("gap audit must not write to the cache")


def test_one_minute_audit_reports_internal_gap_and_missing_object() -> None:
    session = date(2026, 10, 30)
    full = pd.date_range(
        "2026-10-30 09:30", periods=390, freq="min", tz="America/New_York"
    )
    frame = pd.DataFrame({"Close": [100.0] * 389}, index=full.delete(123))
    cache = ReadOnlyCache({CacheKey("SPCX", "1m", session): frame})

    findings = check_cache_gaps(
        cache,
        ["SPCX", "IWM"],
        "1m",
        days=1,
        now=datetime(2026, 10, 31, 12, 0, tzinfo=ZoneInfo("America/New_York")),
    )

    assert [
        (f.symbol, f.missing_bars, f.expected_bars, f.reason) for f in findings
    ] == [
        ("SPCX", 1, 390, "missing bars"),
        ("IWM", 390, 390, "missing archive"),
    ]
    assert findings[0].first_missing == full[123].to_pydatetime()


def test_audit_uses_interval_and_early_close() -> None:
    session = date(2026, 11, 27)
    five_minute = pd.date_range(
        "2026-11-27 09:30", periods=42, freq="5min", tz="America/New_York"
    )
    frame = pd.DataFrame({"Close": [100.0] * 41}, index=five_minute.delete(-1))
    cache = ReadOnlyCache({CacheKey("IWM", "5m", session): frame})

    findings = check_cache_gaps(
        cache,
        ["IWM"],
        "5m",
        days=1,
        now=datetime(2026, 11, 28, 12, 0, tzinfo=ZoneInfo("America/New_York")),
    )

    assert len(findings) == 1
    assert (findings[0].expected_bars, findings[0].missing_bars) == (42, 1)
    assert findings[0].last_missing == five_minute[-1].to_pydatetime()


def test_audit_skips_holiday_and_accepts_daily_bar() -> None:
    cache = ReadOnlyCache(
        {
            CacheKey("SPCX", "1d", date(2026, 10, 30)): pd.DataFrame(
                {"Close": [100.0]}, index=pd.DatetimeIndex(["2026-10-30"])
            )
        }
    )
    assert (
        check_cache_gaps(
            cache,
            ["SPCX"],
            "1d",
            days=1,
            now=datetime(2026, 10, 31, 12, 0, tzinfo=ZoneInfo("America/New_York")),
        )
        == []
    )
    assert (
        check_cache_gaps(
            cache,
            ["SPCX"],
            "1m",
            days=1,
            now=datetime(2026, 12, 26, 12, 0, tzinfo=ZoneInfo("America/New_York")),
        )
        == []
    )


def test_audit_treats_null_close_as_gap_and_rejects_unsupported_interval() -> None:
    session = date(2026, 10, 30)
    hourly = pd.date_range(
        "2026-10-30 09:30", periods=7, freq="h", tz="America/New_York"
    )
    frame = pd.DataFrame({("Close", "SPCX"): [100.0] * 7}, index=hourly)
    frame.iloc[3, 0] = float("nan")
    cache = ReadOnlyCache({CacheKey("SPCX", "1h", session): frame})

    findings = check_cache_gaps(
        cache,
        ["SPCX"],
        "1h",
        days=1,
        now=datetime(2026, 10, 31, 12, 0, tzinfo=ZoneInfo("America/New_York")),
    )
    assert len(findings) == 1
    assert findings[0].missing_bars == 1
    with pytest.raises(ValueError, match="Unsupported interval"):
        check_cache_gaps(cache, ["SPCX"], "1wk", days=1)


def test_gap_check_cli_exits_nonzero_for_missing_bars(
    monkeypatch, tmp_path, capsys
) -> None:
    config = tmp_path / "collector.json"
    config.write_text(
        json.dumps({"tickers": ["SPCX"], "interval": "1m", "cache_dir": str(tmp_path)})
    )
    monkeypatch.setattr(cache_gap_check, "create_cache", lambda _: ReadOnlyCache({}))

    result = cache_gap_check.main(
        ["--config", str(config), "--days", "1"],
        now=datetime(2026, 10, 31, 12, 0, tzinfo=ZoneInfo("America/New_York")),
    )

    assert result == 1
    assert "SPCX 2026-10-30 1m: missing 390/390 bars" in capsys.readouterr().out


def test_gap_check_cli_distinguishes_cache_read_failure(
    monkeypatch, tmp_path, capsys
) -> None:
    config = tmp_path / "collector.json"
    config.write_text(
        json.dumps({"tickers": ["SPCX"], "interval": "1m", "cache_dir": str(tmp_path)})
    )

    class BrokenCache(ReadOnlyCache):
        def load(self, key: CacheKey) -> pd.DataFrame | None:
            raise RuntimeError("archive unavailable")

    monkeypatch.setattr(cache_gap_check, "create_cache", lambda _: BrokenCache({}))
    result = cache_gap_check.main(
        ["--config", str(config), "--days", "1"],
        now=datetime(2026, 10, 31, 12, 0, tzinfo=ZoneInfo("America/New_York")),
    )

    assert result == 2
    assert "Gap audit failed: archive unavailable" in capsys.readouterr().err
