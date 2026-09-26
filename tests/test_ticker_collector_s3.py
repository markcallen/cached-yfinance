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
                {"Close": [100.0]}, index=pd.DatetimeIndex(["2026-09-25 09:30"])
            )

    client = StubClient()
    logger = ticker_collector.setup_logging()

    stats = ticker_collector.collect_1m_data("IWM", client, 7, "1m", logger)

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
