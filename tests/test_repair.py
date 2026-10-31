import json
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from cached_yfinance.cache import CacheKey
from cached_yfinance.repair import repair_gap
from tools import cache_gap_check, cache_gap_repair


class MemoryCache:
    def __init__(self, frames: dict[CacheKey, pd.DataFrame]) -> None:
        self.frames = frames
        self.stores = 0

    def load(self, key: CacheKey) -> pd.DataFrame | None:
        return self.frames.get(key)

    def store(self, key: CacheKey, frame: pd.DataFrame) -> None:
        self.stores += 1
        self.frames[key] = frame


def test_repair_fills_only_missing_bar_and_preserves_archive() -> None:
    day = date(2026, 10, 30)
    key = CacheKey("SPCX", "1m", day)
    times = pd.date_range(
        "2026-10-30 09:30", periods=390, freq="min", tz="America/New_York"
    )
    existing = pd.DataFrame({"Close": [100.0] * 389}, index=times.delete(123))
    fetched = pd.DataFrame({"Close": [101.0]}, index=times[[123]])
    cache = MemoryCache({key: existing})

    outcome = repair_gap(cache, "SPCX", day, "1m", lambda *_: fetched)

    assert (outcome.before_missing, outcome.after_missing, outcome.error) == (
        1,
        0,
        None,
    )
    assert cache.stores == 1
    assert len(cache.load(key)) == 390
    assert cache.load(key).loc[times[0], "Close"] == 100.0
    assert cache.load(key).loc[times[123], "Close"] == 101.0


def test_repair_keeps_archive_when_provider_has_no_improvement() -> None:
    day = date(2026, 10, 30)
    key = CacheKey("SPCX", "1m", day)
    partial = pd.DataFrame(
        {"Close": [100.0]},
        index=pd.DatetimeIndex(["2026-10-30 09:30"], tz="America/New_York"),
    )
    cache = MemoryCache({key: partial})

    outcome = repair_gap(cache, "SPCX", day, "1m", lambda *_: partial)

    assert (outcome.before_missing, outcome.after_missing) == (389, 389)
    assert cache.stores == 0
    pd.testing.assert_frame_equal(cache.load(key), partial)


def test_repair_preserves_non_null_fields_on_overlapping_rows() -> None:
    day = date(2026, 10, 30)
    key = CacheKey("SPCX", "1m", day)
    times = pd.DatetimeIndex(
        ["2026-10-30 09:30", "2026-10-30 09:31"], tz="America/New_York"
    )
    existing = pd.DataFrame(
        {"Open": [99.0], "Close": [100.0], "Volume": [10.0]}, index=times[:1]
    )
    fetched = pd.DataFrame(
        {
            "Open": [float("nan"), 100.0],
            "Close": [101.0, 102.0],
            "Volume": [float("nan"), 20.0],
        },
        index=times,
    )
    cache = MemoryCache({key: existing})

    outcome = repair_gap(cache, "SPCX", day, "1m", lambda *_: fetched)

    assert outcome.after_missing == outcome.before_missing - 1
    repaired = cache.load(key)
    assert repaired.loc[times[0], "Open"] == 99.0
    assert repaired.loc[times[0], "Close"] == 100.0
    assert repaired.loc[times[0], "Volume"] == 10.0
    assert repaired.loc[times[1], "Close"] == 102.0


def test_repair_accepts_reordered_compatible_columns() -> None:
    day = date(2026, 10, 30)
    key = CacheKey("SPCX", "1m", day)
    times = pd.DatetimeIndex(
        ["2026-10-30 09:30", "2026-10-30 09:31"], tz="America/New_York"
    )
    existing = pd.DataFrame({"Open": [99.0], "Close": [100.0]}, index=times[:1])
    fetched = pd.DataFrame({"Close": [101.0], "Open": [100.0]}, index=times[1:])
    cache = MemoryCache({key: existing})

    outcome = repair_gap(cache, "SPCX", day, "1m", lambda *_: fetched)

    assert outcome.after_missing == outcome.before_missing - 1
    assert cache.stores == 1
    assert list(cache.load(key).columns) == ["Open", "Close"]


def test_repair_merges_utc_naive_and_aware_indexes() -> None:
    day = date(2026, 10, 30)
    key = CacheKey("SPCX", "1m", day)
    existing = pd.DataFrame(
        {"Close": [100.0]}, index=pd.DatetimeIndex(["2026-10-30 13:30"])
    )
    fetched = pd.DataFrame(
        {"Close": [101.0]},
        index=pd.DatetimeIndex(["2026-10-30 09:31"], tz="America/New_York"),
    )
    cache = MemoryCache({key: existing})

    outcome = repair_gap(cache, "SPCX", day, "1m", lambda *_: fetched)

    assert outcome.after_missing == outcome.before_missing - 1
    assert len(cache.load(key)) == 2
    assert str(cache.load(key).index.tz) == "UTC"


def test_repair_reports_partial_progress_and_provider_error() -> None:
    day = date(2026, 10, 30)
    key = CacheKey("SPCX", "1m", day)
    first = pd.DataFrame(
        {"Close": [100.0]},
        index=pd.DatetimeIndex(["2026-10-30 09:30"], tz="America/New_York"),
    )
    cache = MemoryCache({})

    progress = repair_gap(cache, "SPCX", day, "1m", lambda *_: first)
    failed = repair_gap(
        cache,
        "SPCX",
        day,
        "1m",
        lambda *_: (_ for _ in ()).throw(RuntimeError("provider down")),
    )

    assert (progress.before_missing, progress.after_missing) == (390, 389)
    assert failed.after_missing == 389
    assert failed.error == "provider down"
    assert cache.stores == 1
    assert len(cache.load(key)) == 1


def test_cli_consumes_fresh_audit_report_and_repairs(
    monkeypatch, tmp_path, capsys
) -> None:
    now = datetime(2026, 10, 31, 12, 0, tzinfo=ZoneInfo("America/New_York"))
    config = tmp_path / "collector.json"
    report = tmp_path / "gaps.json"
    config.write_text(
        json.dumps({"tickers": ["SPCX"], "interval": "1d", "cache_dir": str(tmp_path)})
    )
    cache = MemoryCache({})
    monkeypatch.setattr(cache_gap_check, "create_cache", lambda _: cache)
    monkeypatch.setattr(cache_gap_repair, "create_cache", lambda _: cache)
    monkeypatch.setattr(
        cache_gap_repair,
        "fetch_yahoo_session",
        lambda *_: pd.DataFrame(
            {"Close": [100.0]}, index=pd.DatetimeIndex(["2026-10-30"])
        ),
    )

    audit_status = cache_gap_check.main(
        ["--config", str(config), "--days", "1", "--json-output", str(report)], now=now
    )
    repair_status = cache_gap_repair.main(
        ["--config", str(config), "--report", str(report)], now=now
    )

    assert audit_status == 1
    assert repair_status == 0
    assert cache.stores == 1
    assert json.loads(report.read_text())["findings"] == [
        {"symbol": "SPCX", "day": "2026-10-30"}
    ]
    assert "missing 1 -> 0 bars" in capsys.readouterr().out


def test_repair_cli_rejects_stale_report(monkeypatch, tmp_path, capsys) -> None:
    config = tmp_path / "collector.json"
    report = tmp_path / "gaps.json"
    config.write_text(
        json.dumps({"tickers": ["SPCX"], "interval": "1m", "cache_dir": str(tmp_path)})
    )
    report.write_text(
        json.dumps(
            {
                "schema": 1,
                "generated_at": "2026-10-30T12:00:00+00:00",
                "days": 30,
                "calendar": "NYSE",
                "timezone": "America/New_York",
                "interval": "1m",
                "tickers": ["SPCX"],
                "findings": [{"symbol": "SPCX", "day": "2026-10-30"}],
            }
        )
    )
    monkeypatch.setattr(cache_gap_repair, "create_cache", lambda _: MemoryCache({}))

    status = cache_gap_repair.main(
        ["--config", str(config), "--report", str(report)],
        now=datetime(2026, 10, 31, 16, 0, tzinfo=timezone.utc),
    )

    assert status == 2
    assert "report is stale" in capsys.readouterr().err


def test_commands_accept_collector_defaults(monkeypatch, tmp_path) -> None:
    now = datetime(2026, 10, 31, 12, 0, tzinfo=ZoneInfo("America/New_York"))
    config = tmp_path / "collector.json"
    report = tmp_path / "gaps.json"
    config.write_text(json.dumps({"tickers": ["SPCX"]}))
    cache = MemoryCache({})
    monkeypatch.setattr(cache_gap_check, "create_cache", lambda _: cache)
    monkeypatch.setattr(cache_gap_repair, "create_cache", lambda _: cache)
    monkeypatch.setattr(
        cache_gap_repair,
        "fetch_yahoo_session",
        lambda *_: pd.DataFrame(
            {"Close": [100.0] * 390},
            index=pd.date_range(
                "2026-10-30 09:30", periods=390, freq="min", tz="America/New_York"
            ),
        ),
    )

    assert (
        cache_gap_check.main(
            ["--config", str(config), "--days", "1", "--json-output", str(report)],
            now=now,
        )
        == 1
    )
    assert (
        cache_gap_repair.main(
            ["--config", str(config), "--report", str(report)], now=now
        )
        == 0
    )
    assert cache.stores == 1
