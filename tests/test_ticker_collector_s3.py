from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pandas as pd

from tools import ticker_collector


def test_ticker_collector_selects_direct_s3_cache(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class StubS3Cache:
        def __init__(self, bucket: str, **kwargs: object) -> None:
            captured["bucket"] = bucket
            captured.update(kwargs)

    monkeypatch.setattr(ticker_collector, "S3Cache", StubS3Cache)

    cache = ticker_collector.create_cache(
        {
            "s3_bucket": "market-data",
            "s3_prefix": "cached-yfinance",
            "s3_endpoint_url": "https://objects.example.com",
            "s3_region": "us-east-1",
            "cache_dir": "/cache",
        }
    )

    assert isinstance(cache, StubS3Cache)
    assert captured == {
        "bucket": "market-data",
        "prefix": "cached-yfinance",
        "endpoint_url": "https://objects.example.com",
        "region_name": "us-east-1",
    }


def test_one_minute_collection_refreshes_current_session() -> None:
    class StubClient:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def download(self, ticker: str, **kwargs: object) -> pd.DataFrame:
            self.calls.append({"ticker": ticker, **kwargs})
            return pd.DataFrame(
                {"Close": [100.0]},
                index=pd.DatetimeIndex(["2026-09-29 14:25:00+00:00"]),
            )

    client = StubClient()
    logger = ticker_collector.setup_logging()

    stats = ticker_collector.collect_1m_data(
        "IWM",
        client,
        7,
        "1m",
        logger,
        session_date=date(2026, 9, 29),
        freshness_cutoff=datetime(
            2026, 9, 29, 10, 0, tzinfo=ZoneInfo("America/New_York")
        ),
        timezone="America/New_York",
    )

    assert stats["success"] is True
    assert stats["data_points"] == 1
    assert client.calls == [
        {
            "ticker": "IWM",
            "period": "1d",
            "interval": "1m",
            "progress": False,
        }
    ]


def test_one_minute_collection_rejects_previous_session() -> None:
    class StubClient:
        def download(self, ticker: str, **kwargs: object) -> pd.DataFrame:
            return pd.DataFrame(
                {"Close": [100.0]},
                index=pd.DatetimeIndex(["2026-09-28 19:59:00+00:00"]),
            )

    stats = ticker_collector.collect_1m_data(
        "IWM",
        StubClient(),
        1,
        "1m",
        ticker_collector.setup_logging(),
        session_date=date(2026, 9, 29),
        freshness_cutoff=datetime(
            2026, 9, 29, 10, 0, tzinfo=ZoneInfo("America/New_York")
        ),
        timezone="America/New_York",
    )

    assert stats["success"] is False
    assert "current session" in stats["error"]


def test_one_minute_collection_rejects_stale_current_session() -> None:
    class StubClient:
        def download(self, ticker: str, **kwargs: object) -> pd.DataFrame:
            return pd.DataFrame(
                {"Close": [100.0]},
                index=pd.DatetimeIndex(["2026-09-29 13:30:00+00:00"]),
            )

    stats = ticker_collector.collect_1m_data(
        "IWM",
        StubClient(),
        1,
        "1m",
        ticker_collector.setup_logging(),
        session_date=date(2026, 9, 29),
        freshness_cutoff=datetime(
            2026, 9, 29, 10, 0, tzinfo=ZoneInfo("America/New_York")
        ),
        timezone="America/New_York",
    )

    assert stats["success"] is False
    assert "Stale" in stats["error"]


def test_one_minute_collection_counts_only_current_session_rows() -> None:
    class StubClient:
        def download(self, ticker: str, **kwargs: object) -> pd.DataFrame:
            return pd.DataFrame(
                {"Close": [100.0, 101.0]},
                index=pd.DatetimeIndex(
                    ["2026-09-28 19:59:00+00:00", "2026-09-29 14:25:00+00:00"]
                ),
            )

    stats = ticker_collector.collect_1m_data(
        "IWM",
        StubClient(),
        1,
        "1m",
        ticker_collector.setup_logging(),
        session_date=date(2026, 9, 29),
        freshness_cutoff=datetime(
            2026, 9, 29, 10, 0, tzinfo=ZoneInfo("America/New_York")
        ),
        timezone="America/New_York",
    )

    assert stats["success"] is True
    assert stats["data_points"] == 1
    assert stats["date_range"] == "2026-09-29 10:25 to 2026-09-29 10:25"


def test_nyse_session_skips_holiday_and_honors_early_close() -> None:
    eastern = ZoneInfo("America/New_York")
    assert (
        ticker_collector.current_nyse_session(
            datetime(2026, 12, 25, 14, 0, tzinfo=eastern), "America/New_York"
        )
        is None
    )
    session = ticker_collector.current_nyse_session(
        datetime(2026, 11, 27, 14, 0, tzinfo=eastern), "America/New_York"
    )
    assert session == (
        date(2026, 11, 27),
        datetime(2026, 11, 27, 12, 30, tzinfo=eastern),
    )


def test_price_collector_main_fails_when_all_tickers_return_no_data(
    monkeypatch,
) -> None:
    class StubClient:
        def __init__(self, cache: object) -> None:
            pass

        def download(self, ticker: str, **kwargs: object) -> pd.DataFrame:
            return pd.DataFrame()

    monkeypatch.setattr(
        ticker_collector,
        "load_config",
        lambda *_: {
            **ticker_collector.DEFAULT_CONFIG,
            "tickers": ["IWM"],
        },
    )
    monkeypatch.setattr(ticker_collector, "create_cache", lambda *_: object())
    monkeypatch.setattr(ticker_collector.cyf, "CachedYFClient", StubClient)
    monkeypatch.setattr(ticker_collector.sys, "argv", ["ticker_collector.py"])

    with patch.object(ticker_collector, "datetime") as fixed_datetime:
        fixed_datetime.now.return_value = datetime(
            2026, 9, 29, 14, 30, tzinfo=ZoneInfo("America/New_York")
        )
        assert ticker_collector.main() == 1
