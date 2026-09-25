from datetime import date

import pandas as pd

from cached_yfinance import FileSystemCache, S3Cache
from tools import options_collector


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, **_: object) -> None:
        self.objects[Key] = Body

    def list_objects_v2(self, *, Bucket: str, Prefix: str, **_: object) -> dict:
        return {
            "Contents": [
                {"Key": key} for key in self.objects if key.startswith(Prefix)
            ],
            "IsTruncated": False,
        }

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        del self.objects[Key]


def test_s3_option_history_retention_only_removes_expired_snapshot_dates() -> None:
    s3 = FakeS3()
    cache = S3Cache("market-data", prefix="yfinance", s3_client=s3)
    calls = pd.DataFrame({"strike": [100.0]})
    puts = pd.DataFrame({"strike": [90.0]})

    cache.store_option_chain(
        "IWM", "2026-10-16", calls, puts, {}, "2026-08-20T14:30:00"
    )
    cache.store_option_chain(
        "IWM", "2026-10-16", calls, puts, {}, "2026-08-26T14:30:00"
    )
    cache.store_option_chain(
        "IWM", "2026-10-16", calls, puts, {}, "2026-08-27T14:30:00"
    )

    deleted = cache.prune_option_history("IWM", 30, today=date(2026, 9, 25))

    assert deleted == 3
    assert all("2026-08-20" not in key for key in s3.objects)
    assert any("2026-08-26" in key for key in s3.objects)
    assert any("2026-08-27" in key for key in s3.objects)


def test_filesystem_option_history_retention_only_removes_expired_snapshots(
    tmp_path,
) -> None:
    cache = FileSystemCache(tmp_path)
    calls = pd.DataFrame({"strike": [100.0]})
    puts = pd.DataFrame({"strike": [90.0]})

    cache.store_option_chain(
        "IWM", "2026-10-16", calls, puts, {}, "2026-08-20T14:30:00"
    )
    cache.store_option_chain(
        "IWM", "2026-10-16", calls, puts, {}, "2026-08-26T14:30:00"
    )

    deleted = cache.prune_option_history("IWM", 30, today=date(2026, 9, 25))

    assert deleted == 3
    assert not (tmp_path / "IWM/options/2026-10-16/historical/2026-08-20").exists()
    assert (tmp_path / "IWM/options/2026-10-16/historical/2026-08-26").exists()


def test_collector_selects_direct_s3_cache(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class StubS3Cache:
        def __init__(self, bucket: str, **kwargs: object) -> None:
            captured["bucket"] = bucket
            captured.update(kwargs)

    monkeypatch.setattr(options_collector, "S3Cache", StubS3Cache)

    cache = options_collector.create_cache(
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
