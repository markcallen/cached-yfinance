from __future__ import annotations

import hashlib
from datetime import date

import pandas as pd

from cached_yfinance import CacheKey, OptionCacheKey, S3Cache


class NotFoundError(Exception):
    def __init__(self) -> None:
        self.response = {
            "ResponseMetadata": {"HTTPStatusCode": 404},
            "Error": {"Code": "NoSuchKey"},
        }


class MissingBucketError(Exception):
    def __init__(self) -> None:
        self.response = {
            "ResponseMetadata": {"HTTPStatusCode": 404},
            "Error": {"Code": "NoSuchBucket"},
        }


class PreconditionFailedError(Exception):
    def __init__(self) -> None:
        self.response = {
            "ResponseMetadata": {"HTTPStatusCode": 412},
            "Error": {"Code": "PreconditionFailed"},
        }


class FakeBody:
    def __init__(self, value: bytes) -> None:
        self.value = value

    def read(self) -> bytes:
        return self.value


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    def head_object(self, *, Bucket: str, Key: str) -> dict:
        if Key not in self.objects:
            raise NotFoundError()
        return {}

    def get_object(self, *, Bucket: str, Key: str) -> dict:
        if Key not in self.objects:
            raise NotFoundError()
        return {
            "Body": FakeBody(self.objects[Key]),
            "ETag": f'"{hashlib.md5(self.objects[Key]).hexdigest()}"',
        }

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,
        IfMatch: str | None = None,
        IfNoneMatch: str | None = None,
    ) -> dict:
        if IfNoneMatch == "*" and Key in self.objects:
            raise PreconditionFailedError()
        if IfMatch is not None and (
            Key not in self.objects
            or IfMatch != f'"{hashlib.md5(self.objects[Key]).hexdigest()}"'
        ):
            raise PreconditionFailedError()
        self.objects[Key] = Body
        self.content_types[Key] = ContentType
        return {}

    def list_objects_v2(self, **kwargs) -> dict:
        prefix = kwargs.get("Prefix", "")
        contents = [
            {"Key": key} for key in sorted(self.objects) if key.startswith(prefix)
        ]
        return {"Contents": contents, "IsTruncated": False}


def test_market_data_round_trip() -> None:
    s3 = FakeS3()
    cache = S3Cache("market-data", prefix="yfinance", s3_client=s3)
    key = CacheKey(symbol="IWM", interval="1d", day=date(2026, 8, 27))
    frame = pd.DataFrame(
        {"Close": [223.5], "Volume": [123456]},
        index=pd.to_datetime(["2026-08-27"]),
    )

    cache.store(key, frame)

    assert cache.has(key)
    loaded = cache.load(key)
    assert loaded is not None
    pd.testing.assert_frame_equal(loaded, frame)
    assert "yfinance/IWM/1d/2026/08/2026-08-27-1d.parquet" in s3.objects
    assert "yfinance/IWM/1d/2026/08/2026-08-27-1d.json" in s3.objects
    assert list(cache.iter_cached_days("IWM", "1d")) == [date(2026, 8, 27)]


def test_conditional_update_retries_after_concurrent_writer() -> None:
    s3 = FakeS3()
    cache = S3Cache("market-data", s3_client=s3)
    key = CacheKey("SPCX", "1m", date(2026, 10, 30))
    times = pd.date_range("2026-10-30 09:30", periods=3, freq="min", tz="UTC")
    cache.store(key, pd.DataFrame({"Close": [100.0]}, index=times[:1]))
    interleaved = False

    def updater(current):
        nonlocal interleaved
        if not interleaved:
            interleaved = True
            cache.store(key, pd.DataFrame({"Close": [100.0, 101.0]}, index=times[:2]))
        return pd.concat(
            [current, pd.DataFrame({"Close": [102.0]}, index=times[2:])]
        ).sort_index()

    result = cache.update_price_frame(key, updater)

    assert interleaved
    assert list(result["Close"]) == [100.0, 101.0, 102.0]
    assert list(cache.load(key)["Close"]) == [100.0, 101.0, 102.0]


def test_s3_cache_initializes_filesystem_base_state() -> None:
    cache = S3Cache("market-data", s3_client=FakeS3())

    assert cache.root is not None


def test_timestamped_option_chain_round_trip() -> None:
    s3 = FakeS3()
    cache = S3Cache("market-data", prefix="yfinance", s3_client=s3)
    expiration = "2026-09-18"
    timestamp = "2026-08-27T14:30:00+00:00"
    calls = pd.DataFrame({"strike": [220.0, 225.0], "lastPrice": [6.1, 3.8]})
    puts = pd.DataFrame({"strike": [220.0, 225.0], "lastPrice": [2.4, 4.9]})
    underlying = {"regularMarketPrice": 223.5}

    cache.store_option_chain(
        "IWM", expiration, calls, puts, underlying, timestamp=timestamp
    )

    calls_key = OptionCacheKey.for_calls("IWM", expiration, timestamp)
    puts_key = OptionCacheKey.for_puts("IWM", expiration, timestamp)
    underlying_key = OptionCacheKey.for_underlying("IWM", expiration, timestamp)

    assert cache.has_option_chain(calls_key)
    assert cache.has_option_chain(puts_key)
    assert cache.has_option_chain(underlying_key)
    pd.testing.assert_frame_equal(cache.load_option_chain(calls_key), calls)
    pd.testing.assert_frame_equal(cache.load_option_chain(puts_key), puts)
    assert cache.load_option_chain(underlying_key) == underlying

    base = "yfinance/IWM/options/2026-09-18/historical/2026-08-27"
    assert f"{base}/calls_143000.parquet" in s3.objects
    assert f"{base}/puts_143000.parquet" in s3.objects
    assert f"{base}/metadata_143000.json" in s3.objects
    assert list(cache.iter_cached_option_expirations("IWM")) == [expiration]
    assert list(cache.iter_cached_option_timestamps("IWM", expiration)) == [
        "2026-08-27T14:30:00"
    ]


def test_missing_objects_return_false_or_none() -> None:
    cache = S3Cache("market-data", s3_client=FakeS3())
    key = CacheKey(symbol="IWM", interval="1d", day=date(2026, 8, 27))

    assert cache.has(key) is False
    assert cache.load(key) is None


def test_missing_bucket_error_is_not_treated_as_cache_miss() -> None:
    class MissingBucketS3(FakeS3):
        def head_object(self, *, Bucket: str, Key: str) -> dict:
            raise MissingBucketError()

    cache = S3Cache("missing-bucket", s3_client=MissingBucketS3())
    key = CacheKey(symbol="IWM", interval="1d", day=date(2026, 8, 27))

    try:
        cache.has(key)
    except MissingBucketError:
        pass
    else:
        raise AssertionError("Expected missing bucket errors to propagate")


def test_option_listing_is_sorted_and_unique() -> None:
    s3 = FakeS3()
    cache = S3Cache("market-data", prefix="cache", s3_client=s3)
    s3.objects.update(
        {
            "cache/IWM/options/2026-10-16/metadata.json": b"{}",
            "cache/IWM/options/2026-09-18/metadata.json": b"{}",
            "cache/IWM/options/2026-10-16/calls.parquet": b"x",
        }
    )

    assert list(cache.iter_cached_option_expirations("IWM")) == [
        "2026-09-18",
        "2026-10-16",
    ]


def test_market_data_listing_is_sorted_and_unique() -> None:
    cache = S3Cache("market-data", prefix="cache", s3_client=FakeS3())

    def unsorted_keys(prefix: str) -> list[str]:
        return [
            f"{prefix}2026/08/2026-08-28-1d.parquet",
            f"{prefix}2026/08/2026-08-27-1d.json",
            f"{prefix}2026/08/2026-08-27-1d.parquet",
            f"{prefix}2026/08/2026-08-28-1d.parquet",
            f"{prefix}invalid.parquet",
        ]

    cache._list_keys = unsorted_keys

    assert list(cache.iter_cached_days("IWM", "1d")) == [
        date(2026, 8, 27),
        date(2026, 8, 28),
    ]
