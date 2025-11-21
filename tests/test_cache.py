"""Tests for the cache module."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from cached_yfinance.cache import (
    CacheKey,
    FileSystemCache,
    OptionCacheKey,
    _ensure_datetime,
    _sanitize_symbol,
)


class TestCacheKey:
    """Test CacheKey functionality."""

    def test_cache_key_creation(self) -> None:
        """Test basic CacheKey creation."""
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        assert key.symbol == "AAPL"
        assert key.interval == "1d"
        assert key.day == date(2023, 1, 1)

    def test_cache_key_from_timestamp_datetime(self) -> None:
        """Test CacheKey creation from datetime."""
        dt = datetime(2023, 1, 1, 15, 30, 0)
        key = CacheKey.from_timestamp("AAPL", "1d", dt)
        assert key.symbol == "AAPL"
        assert key.interval == "1d"
        assert key.day == date(2023, 1, 1)

    def test_cache_key_from_timestamp_pandas(self) -> None:
        """Test CacheKey creation from pandas Timestamp."""
        ts = pd.Timestamp("2023-01-01 15:30:00")
        key = CacheKey.from_timestamp("AAPL", "1d", ts)
        assert key.symbol == "AAPL"
        assert key.interval == "1d"
        assert key.day == date(2023, 1, 1)

    def test_cache_key_from_timestamp_with_timezone(self) -> None:
        """Test CacheKey creation with timezone-aware timestamp."""
        ts = pd.Timestamp("2023-01-01 15:30:00", tz="US/Eastern")
        key = CacheKey.from_timestamp("AAPL", "1d", ts)
        assert key.symbol == "AAPL"
        assert key.interval == "1d"
        # Should convert to UTC date
        assert key.day == date(2023, 1, 1)

    def test_cache_key_frozen(self) -> None:
        """Test that CacheKey is immutable."""
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        with pytest.raises(AttributeError):
            key.symbol = "MSFT"


class TestOptionCacheKey:
    """Test OptionCacheKey functionality."""

    def test_option_cache_key_creation(self) -> None:
        """Test basic OptionCacheKey creation."""
        key = OptionCacheKey(
            symbol="AAPL", expiration_date="2023-01-20", data_type="calls"
        )
        assert key.symbol == "AAPL"
        assert key.expiration_date == "2023-01-20"
        assert key.data_type == "calls"
        assert key.timestamp is None

    def test_option_cache_key_with_timestamp(self) -> None:
        """Test OptionCacheKey creation with timestamp."""
        timestamp = "2023-01-01T15:30:00"
        key = OptionCacheKey(
            symbol="AAPL",
            expiration_date="2023-01-20",
            data_type="calls",
            timestamp=timestamp,
        )
        assert key.timestamp == timestamp

    def test_option_cache_key_for_calls(self) -> None:
        """Test OptionCacheKey.for_calls class method."""
        key = OptionCacheKey.for_calls("AAPL", "2023-01-20")
        assert key.symbol == "AAPL"
        assert key.expiration_date == "2023-01-20"
        assert key.data_type == "calls"
        assert key.timestamp is None

    def test_option_cache_key_for_puts(self) -> None:
        """Test OptionCacheKey.for_puts class method."""
        key = OptionCacheKey.for_puts("AAPL", "2023-01-20", "2023-01-01T15:30:00")
        assert key.symbol == "AAPL"
        assert key.expiration_date == "2023-01-20"
        assert key.data_type == "puts"
        assert key.timestamp == "2023-01-01T15:30:00"

    def test_option_cache_key_for_underlying(self) -> None:
        """Test OptionCacheKey.for_underlying class method."""
        key = OptionCacheKey.for_underlying("AAPL", "2023-01-20")
        assert key.symbol == "AAPL"
        assert key.expiration_date == "2023-01-20"
        assert key.data_type == "underlying"
        assert key.timestamp is None


class TestUtilityFunctions:
    """Test utility functions."""

    def test_sanitize_symbol(self) -> None:
        """Test symbol sanitization."""
        assert _sanitize_symbol("AAPL") == "AAPL"
        assert _sanitize_symbol("aapl") == "AAPL"
        assert _sanitize_symbol("BRK/A") == "BRK_A"
        assert _sanitize_symbol("BRK A") == "BRK_A"
        assert _sanitize_symbol("brk/a test") == "BRK_A_TEST"

    def test_ensure_datetime_pandas(self) -> None:
        """Test _ensure_datetime with pandas Timestamp."""
        ts = pd.Timestamp("2023-01-01")
        result = _ensure_datetime(ts)
        assert isinstance(result, pd.Timestamp)
        assert result == ts

    def test_ensure_datetime_datetime(self) -> None:
        """Test _ensure_datetime with datetime."""
        dt = datetime(2023, 1, 1)
        result = _ensure_datetime(dt)
        assert isinstance(result, pd.Timestamp)
        assert result == pd.Timestamp(dt)


class TestFileSystemCache:
    """Test FileSystemCache functionality."""

    def test_cache_initialization_default(self) -> None:
        """Test cache initialization with default path."""
        cache = FileSystemCache()
        expected_path = Path.home() / ".cache" / "yfinance"
        assert cache.root == expected_path

    def test_cache_initialization_custom(self, temp_cache_dir: Path) -> None:
        """Test cache initialization with custom path."""
        cache = FileSystemCache(temp_cache_dir)
        assert cache.root == temp_cache_dir

    def test_cache_initialization_string_path(self, temp_cache_dir: Path) -> None:
        """Test cache initialization with string path."""
        cache = FileSystemCache(str(temp_cache_dir))
        assert cache.root == temp_cache_dir

    def test_base_dir_path(self, cache: FileSystemCache) -> None:
        """Test _base_dir path generation."""
        base_dir = cache._base_dir("AAPL", "1d", date(2023, 1, 15))
        expected = cache.root / "AAPL" / "1d" / "2023" / "01"
        assert base_dir == expected

    def test_base_dir_path_sanitized_symbol(self, cache: FileSystemCache) -> None:
        """Test _base_dir path generation with symbol sanitization."""
        base_dir = cache._base_dir("BRK/A", "1d", date(2023, 1, 15))
        expected = cache.root / "BRK_A" / "1d" / "2023" / "01"
        assert base_dir == expected

    def test_data_path(self, cache: FileSystemCache) -> None:
        """Test _data_path generation."""
        data_path = cache._data_path("AAPL", "1d", date(2023, 1, 15))
        expected = cache.root / "AAPL" / "1d" / "2023" / "01" / "2023-01-15-1d.parquet"
        assert data_path == expected

    def test_meta_path(self, cache: FileSystemCache) -> None:
        """Test _meta_path generation."""
        meta_path = cache._meta_path("AAPL", "1d", date(2023, 1, 15))
        expected = cache.root / "AAPL" / "1d" / "2023" / "01" / "2023-01-15-1d.json"
        assert meta_path == expected

    def test_has_cache_miss(self, cache: FileSystemCache) -> None:
        """Test has() method with cache miss."""
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        assert not cache.has(key)

    def test_load_cache_miss(self, cache: FileSystemCache) -> None:
        """Test load() method with cache miss."""
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        result = cache.load(key)
        assert result is None

    def test_store_and_load_dataframe(self, cache: FileSystemCache, sample_dataframe: pd.DataFrame) -> None:
        """Test storing and loading a DataFrame."""
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))

        # Store the DataFrame
        cache.store(key, sample_dataframe)

        # Check that it exists
        assert cache.has(key)

        # Load and verify
        loaded = cache.load(key)
        assert loaded is not None
        # The cache stores the entire DataFrame as-is
        pd.testing.assert_frame_equal(loaded, sample_dataframe, check_freq=False)

    def test_store_empty_dataframe(self, cache: FileSystemCache) -> None:
        """Test storing an empty DataFrame (should be skipped)."""
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        empty_df = pd.DataFrame()

        cache.store(key, empty_df)
        assert not cache.has(key)

    def test_store_creates_metadata(self, cache: FileSystemCache, sample_dataframe: pd.DataFrame) -> None:
        """Test that storing creates metadata file."""
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        cache.store(key, sample_dataframe)

        meta_path = cache._meta_path(key.symbol, key.interval, key.day)
        assert meta_path.exists()

        with open(meta_path, "r") as f:
            metadata = json.load(f)

        assert metadata["symbol"] == "AAPL"
        assert metadata["interval"] == "1d"
        assert metadata["day"] == "2023-01-01"
        assert metadata["rows"] == len(sample_dataframe)
        assert metadata["columns"] == list(sample_dataframe.columns)

    def test_iter_cached_days_empty(self, cache: FileSystemCache) -> None:
        """Test iter_cached_days with no cached data."""
        days = list(cache.iter_cached_days("AAPL", "1d"))
        assert days == []

    def test_iter_cached_days_with_data(self, cache: FileSystemCache, sample_dataframe: pd.DataFrame) -> None:
        """Test iter_cached_days with cached data."""
        dates = [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)]

        for d in dates:
            key = CacheKey(symbol="AAPL", interval="1d", day=d)
            cache.store(key, sample_dataframe)

        cached_days = list(cache.iter_cached_days("AAPL", "1d"))
        assert sorted(cached_days) == sorted(dates)


class TestFileSystemCacheOptions:
    """Test FileSystemCache option chain functionality."""

    def test_option_base_dir_current(self, cache: FileSystemCache) -> None:
        """Test _option_base_dir for current data."""
        base_dir = cache._option_base_dir("AAPL", "2023-01-20")
        expected = cache.root / "AAPL" / "options" / "2023-01-20"
        assert base_dir == expected

    def test_option_base_dir_historical(self, cache: FileSystemCache) -> None:
        """Test _option_base_dir for historical data."""
        timestamp = "2023-01-01T15:30:00"
        base_dir = cache._option_base_dir("AAPL", "2023-01-20", timestamp)
        expected = (
            cache.root / "AAPL" / "options" / "2023-01-20" / "historical" / "2023-01-01"
        )
        assert base_dir == expected

    def test_option_data_path_current(self, cache: FileSystemCache) -> None:
        """Test _option_data_path for current data."""
        path = cache._option_data_path("AAPL", "2023-01-20", "calls")
        expected = cache.root / "AAPL" / "options" / "2023-01-20" / "calls.parquet"
        assert path == expected

    def test_option_data_path_historical(self, cache: FileSystemCache) -> None:
        """Test _option_data_path for historical data."""
        timestamp = "2023-01-01T15:30:00"
        path = cache._option_data_path("AAPL", "2023-01-20", "calls", timestamp)
        expected = (
            cache.root
            / "AAPL"
            / "options"
            / "2023-01-20"
            / "historical"
            / "2023-01-01"
            / "calls_153000.parquet"
        )
        assert path == expected

    def test_option_meta_path_current(self, cache: FileSystemCache) -> None:
        """Test _option_meta_path for current data."""
        path = cache._option_meta_path("AAPL", "2023-01-20")
        expected = cache.root / "AAPL" / "options" / "2023-01-20" / "metadata.json"
        assert path == expected

    def test_option_meta_path_historical(self, cache: FileSystemCache) -> None:
        """Test _option_meta_path for historical data."""
        timestamp = "2023-01-01T15:30:00"
        path = cache._option_meta_path("AAPL", "2023-01-20", timestamp)
        expected = (
            cache.root
            / "AAPL"
            / "options"
            / "2023-01-20"
            / "historical"
            / "2023-01-01"
            / "metadata_153000.json"
        )
        assert path == expected

    def test_has_option_chain_calls_miss(self, cache: FileSystemCache) -> None:
        """Test has_option_chain for calls with cache miss."""
        key = OptionCacheKey.for_calls("AAPL", "2023-01-20")
        assert not cache.has_option_chain(key)

    def test_has_option_chain_puts_miss(self, cache: FileSystemCache) -> None:
        """Test has_option_chain for puts with cache miss."""
        key = OptionCacheKey.for_puts("AAPL", "2023-01-20")
        assert not cache.has_option_chain(key)

    def test_has_option_chain_underlying_miss(self, cache: FileSystemCache) -> None:
        """Test has_option_chain for underlying with cache miss."""
        key = OptionCacheKey.for_underlying("AAPL", "2023-01-20")
        assert not cache.has_option_chain(key)

    def test_load_option_chain_calls_miss(self, cache: FileSystemCache) -> None:
        """Test load_option_chain for calls with cache miss."""
        key = OptionCacheKey.for_calls("AAPL", "2023-01-20")
        result = cache.load_option_chain(key)
        assert result is None

    def test_load_option_chain_puts_miss(self, cache: FileSystemCache) -> None:
        """Test load_option_chain for puts with cache miss."""
        key = OptionCacheKey.for_puts("AAPL", "2023-01-20")
        result = cache.load_option_chain(key)
        assert result is None

    def test_load_option_chain_underlying_miss(self, cache: FileSystemCache) -> None:
        """Test load_option_chain for underlying with cache miss."""
        key = OptionCacheKey.for_underlying("AAPL", "2023-01-20")
        result = cache.load_option_chain(key)
        assert result is None

    def test_store_and_load_option_chain(
        self, cache: FileSystemCache, sample_option_dataframe: pd.DataFrame, sample_underlying_data: dict[str, Any]
    ) -> None:
        """Test storing and loading complete option chain."""
        symbol = "AAPL"
        expiration = "2023-01-20"

        # Store option chain
        cache.store_option_chain(
            symbol,
            expiration,
            sample_option_dataframe,  # calls
            sample_option_dataframe,  # puts (using same data for simplicity)
            sample_underlying_data,
        )

        # Test has_option_chain
        calls_key = OptionCacheKey.for_calls(symbol, expiration)
        puts_key = OptionCacheKey.for_puts(symbol, expiration)
        underlying_key = OptionCacheKey.for_underlying(symbol, expiration)

        assert cache.has_option_chain(calls_key)
        assert cache.has_option_chain(puts_key)
        assert cache.has_option_chain(underlying_key)

        # Test load_option_chain
        loaded_calls = cache.load_option_chain(calls_key)
        loaded_puts = cache.load_option_chain(puts_key)
        loaded_underlying = cache.load_option_chain(underlying_key)

        assert loaded_calls is not None
        assert loaded_puts is not None
        assert loaded_underlying is not None

        pd.testing.assert_frame_equal(loaded_calls, sample_option_dataframe)
        pd.testing.assert_frame_equal(loaded_puts, sample_option_dataframe)
        assert loaded_underlying == sample_underlying_data

    def test_store_option_chain_with_timestamp(
        self, cache: FileSystemCache, sample_option_dataframe: pd.DataFrame, sample_underlying_data: dict[str, Any]
    ) -> None:
        """Test storing option chain with timestamp."""
        symbol = "AAPL"
        expiration = "2023-01-20"
        timestamp = "2023-01-01T15:30:00"

        cache.store_option_chain(
            symbol,
            expiration,
            sample_option_dataframe,
            sample_option_dataframe,
            sample_underlying_data,
            timestamp,
        )

        # Test with timestamp
        calls_key = OptionCacheKey.for_calls(symbol, expiration, timestamp)
        assert cache.has_option_chain(calls_key)

        loaded_calls = cache.load_option_chain(calls_key)
        pd.testing.assert_frame_equal(loaded_calls, sample_option_dataframe)

    def test_store_option_chain_empty_dataframes(self, cache: FileSystemCache, sample_underlying_data: dict[str, Any]) -> None:
        """Test storing option chain with empty DataFrames."""
        symbol = "AAPL"
        expiration = "2023-01-20"
        empty_df = pd.DataFrame()

        cache.store_option_chain(
            symbol,
            expiration,
            empty_df,  # empty calls
            empty_df,  # empty puts
            sample_underlying_data,
        )

        # Should still create metadata for underlying
        underlying_key = OptionCacheKey.for_underlying(symbol, expiration)
        assert cache.has_option_chain(underlying_key)

        # But not for calls/puts
        calls_key = OptionCacheKey.for_calls(symbol, expiration)
        puts_key = OptionCacheKey.for_puts(symbol, expiration)
        assert not cache.has_option_chain(calls_key)
        assert not cache.has_option_chain(puts_key)

    def test_iter_cached_option_expirations_empty(self, cache: FileSystemCache) -> None:
        """Test iter_cached_option_expirations with no data."""
        expirations = list(cache.iter_cached_option_expirations("AAPL"))
        assert expirations == []

    def test_iter_cached_option_expirations_with_data(
        self, cache: FileSystemCache, sample_option_dataframe: pd.DataFrame, sample_underlying_data: dict[str, Any]
    ) -> None:
        """Test iter_cached_option_expirations with cached data."""
        symbol = "AAPL"
        expirations = ["2023-01-20", "2023-02-17", "2023-03-17"]

        for exp in expirations:
            cache.store_option_chain(
                symbol,
                exp,
                sample_option_dataframe,
                sample_option_dataframe,
                sample_underlying_data,
            )

        cached_expirations = list(cache.iter_cached_option_expirations(symbol))
        assert sorted(cached_expirations) == sorted(expirations)

    def test_iter_cached_option_timestamps_empty(self, cache: FileSystemCache) -> None:
        """Test iter_cached_option_timestamps with no data."""
        timestamps = list(cache.iter_cached_option_timestamps("AAPL", "2023-01-20"))
        assert timestamps == []

    def test_iter_cached_option_timestamps_with_data(
        self, cache: FileSystemCache, sample_option_dataframe: pd.DataFrame, sample_underlying_data: dict[str, Any]
    ) -> None:
        """Test iter_cached_option_timestamps with cached data."""
        symbol = "AAPL"
        expiration = "2023-01-20"
        timestamps = ["2023-01-01T15:30:00", "2023-01-01T16:00:00"]

        for ts in timestamps:
            cache.store_option_chain(
                symbol,
                expiration,
                sample_option_dataframe,
                sample_option_dataframe,
                sample_underlying_data,
                ts,
            )

        cached_timestamps = list(
            cache.iter_cached_option_timestamps(symbol, expiration)
        )
        assert sorted(cached_timestamps) == sorted(timestamps)
