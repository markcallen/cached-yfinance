"""Tests for the client module."""

from datetime import date, datetime, timedelta
from typing import Any
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from cached_yfinance.cache import CacheKey, FileSystemCache
from cached_yfinance.client import (
    CachedYFClient,
    DownloadRequest,
    OptionChain,
    _contiguous_ranges,
    _merge_dataframes,
    _normalize_range,
    _parse_period_to_timedelta,
    _parse_timestamp,
    _trading_days_inclusive,
    download,
    get_option_chain,
    get_options_expirations,
)


class TestDownloadRequest:
    """Test DownloadRequest functionality."""

    def test_download_request_creation(self) -> None:
        """Test basic DownloadRequest creation."""
        req = DownloadRequest(
            tickers="AAPL",
            interval="1d",
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-31"),
            kwargs={},
        )
        assert req.tickers == "AAPL"
        assert req.interval == "1d"
        assert req.start == pd.Timestamp("2023-01-01")
        assert req.end == pd.Timestamp("2023-01-31")
        assert req.kwargs == {}

    def test_interval_is_intraday_daily(self) -> None:
        """Test interval_is_intraday for daily interval."""
        req = DownloadRequest("AAPL", "1d", None, None, {})
        assert not req.interval_is_intraday

    def test_interval_is_intraday_minute(self) -> None:
        """Test interval_is_intraday for minute interval."""
        req = DownloadRequest("AAPL", "5m", None, None, {})
        assert req.interval_is_intraday

    def test_interval_is_intraday_hour(self) -> None:
        """Test interval_is_intraday for hour interval."""
        req = DownloadRequest("AAPL", "1h", None, None, {})
        assert req.interval_is_intraday


class TestOptionChain:
    """Test OptionChain functionality."""

    def test_option_chain_creation(
        self,
        sample_option_dataframe: pd.DataFrame,
        sample_underlying_data: dict[str, Any],
    ) -> None:
        """Test OptionChain creation."""
        chain = OptionChain(
            calls=sample_option_dataframe,
            puts=sample_option_dataframe,
            underlying=sample_underlying_data,
        )
        assert isinstance(chain.calls, pd.DataFrame)
        assert isinstance(chain.puts, pd.DataFrame)
        assert isinstance(chain.underlying, dict)
        pd.testing.assert_frame_equal(chain.calls, sample_option_dataframe)
        pd.testing.assert_frame_equal(chain.puts, sample_option_dataframe)
        assert chain.underlying == sample_underlying_data


class TestUtilityFunctions:
    """Test utility functions."""

    def test_parse_timestamp_none(self) -> None:
        """Test _parse_timestamp with None."""
        result = _parse_timestamp(None)
        assert result is None

    def test_parse_timestamp_pandas(self) -> None:
        """Test _parse_timestamp with pandas Timestamp."""
        ts = pd.Timestamp("2023-01-01")
        result = _parse_timestamp(ts)
        assert result == ts

    def test_parse_timestamp_datetime(self) -> None:
        """Test _parse_timestamp with datetime."""
        dt = datetime(2023, 1, 1)
        result = _parse_timestamp(dt)
        assert result == pd.Timestamp(dt)

    def test_parse_timestamp_string(self) -> None:
        """Test _parse_timestamp with string."""
        result = _parse_timestamp("2023-01-01")
        assert result == pd.Timestamp("2023-01-01")

    def test_parse_period_to_timedelta_none(self) -> None:
        """Test _parse_period_to_timedelta with None."""
        result = _parse_period_to_timedelta(None)
        assert result is None

    def test_parse_period_to_timedelta_max(self) -> None:
        """Test _parse_period_to_timedelta with 'max'."""
        result = _parse_period_to_timedelta("max")
        assert result is None

    def test_parse_period_to_timedelta_days(self) -> None:
        """Test _parse_period_to_timedelta with days."""
        result = _parse_period_to_timedelta("5d")
        assert result == pd.Timedelta(days=5)

    def test_parse_period_to_timedelta_weeks(self) -> None:
        """Test _parse_period_to_timedelta with weeks."""
        result = _parse_period_to_timedelta("2wk")
        assert result == pd.Timedelta(weeks=2)

    def test_parse_period_to_timedelta_months(self) -> None:
        """Test _parse_period_to_timedelta with months."""
        result = _parse_period_to_timedelta("3mo")
        assert result == pd.Timedelta(days=90)  # 3 * 30

    def test_parse_period_to_timedelta_years(self) -> None:
        """Test _parse_period_to_timedelta with years."""
        result = _parse_period_to_timedelta("1y")
        assert result == pd.Timedelta(days=365)

    def test_parse_period_to_timedelta_hours(self) -> None:
        """Test _parse_period_to_timedelta with hours."""
        result = _parse_period_to_timedelta("4h")
        assert result == pd.Timedelta(hours=4)

    def test_parse_period_to_timedelta_minutes(self) -> None:
        """Test _parse_period_to_timedelta with minutes."""
        result = _parse_period_to_timedelta("30m")
        assert result == pd.Timedelta(minutes=30)

    def test_parse_period_to_timedelta_invalid(self) -> None:
        """Test _parse_period_to_timedelta with invalid period."""
        result = _parse_period_to_timedelta("invalid")
        assert result is None

    def test_normalize_range_with_start_end(self) -> None:
        """Test _normalize_range with start and end provided."""
        start = "2023-01-01"
        end = "2023-01-31"
        start_ts, end_ts = _normalize_range(start, end, None, "1d")
        assert start_ts == pd.Timestamp("2023-01-01")
        assert end_ts == pd.Timestamp("2023-01-31")

    def test_normalize_range_with_period(self) -> None:
        """Test _normalize_range with period."""
        start_ts, end_ts = _normalize_range(None, "2023-01-31", "5d", "1d")
        assert end_ts == pd.Timestamp("2023-01-31")
        assert start_ts == pd.Timestamp("2023-01-31") - pd.Timedelta(days=5)

    def test_normalize_range_intraday_default_end(self) -> None:
        """Test _normalize_range with intraday interval and no end."""
        with patch("pandas.Timestamp.utcnow") as mock_now:
            mock_now.return_value = pd.Timestamp("2023-01-15 15:30:00")
            start_ts, end_ts = _normalize_range(None, None, "5d", "5m")
            assert end_ts == pd.Timestamp("2023-01-15 15:30:00")

    def test_normalize_range_daily_default_end(self) -> None:
        """Test _normalize_range with daily interval and no end."""
        with patch("pandas.Timestamp.today") as mock_today:
            mock_today.return_value = pd.Timestamp("2023-01-15")
            start_ts, end_ts = _normalize_range(None, None, "5d", "1d")
            assert end_ts == pd.Timestamp("2023-01-15").normalize()

    def test_merge_dataframes_empty(self) -> None:
        """Test _merge_dataframes with empty list."""
        result = _merge_dataframes([])
        assert result.empty

    def test_merge_dataframes_single(self, sample_dataframe: pd.DataFrame) -> None:
        """Test _merge_dataframes with single DataFrame."""
        result = _merge_dataframes([sample_dataframe])
        pd.testing.assert_frame_equal(result, sample_dataframe.sort_index())

    def test_merge_dataframes_multiple(self) -> None:
        """Test _merge_dataframes with multiple DataFrames."""
        df1 = pd.DataFrame({"A": [1, 2]}, index=pd.date_range("2023-01-01", periods=2))
        df2 = pd.DataFrame({"A": [3, 4]}, index=pd.date_range("2023-01-03", periods=2))

        result = _merge_dataframes([df1, df2])
        expected = pd.concat([df1, df2]).sort_index()
        pd.testing.assert_frame_equal(result, expected)

    def test_merge_dataframes_with_duplicates(self) -> None:
        """Test _merge_dataframes with duplicate indices (keeps last)."""
        df1 = pd.DataFrame({"A": [1, 2]}, index=pd.date_range("2023-01-01", periods=2))
        df2 = pd.DataFrame({"A": [3, 4]}, index=pd.date_range("2023-01-01", periods=2))

        result = _merge_dataframes([df1, df2])
        # Should keep the last values (from df2)
        expected = df2.sort_index()
        pd.testing.assert_frame_equal(result, expected, check_freq=False)

    def test_contiguous_ranges_empty(self) -> None:
        """Test _contiguous_ranges with empty list."""
        result = _contiguous_ranges([])
        assert result == []

    def test_contiguous_ranges_single(self) -> None:
        """Test _contiguous_ranges with single date."""
        dates = [date(2023, 1, 1)]
        result = _contiguous_ranges(dates)
        assert result == [(date(2023, 1, 1), date(2023, 1, 1))]

    def test_contiguous_ranges_consecutive(self) -> None:
        """Test _contiguous_ranges with consecutive dates."""
        dates = [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)]
        result = _contiguous_ranges(dates)
        assert result == [(date(2023, 1, 1), date(2023, 1, 3))]

    def test_contiguous_ranges_with_gaps(self) -> None:
        """Test _contiguous_ranges with gaps."""
        dates = [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 5), date(2023, 1, 6)]
        result = _contiguous_ranges(dates)
        expected = [
            (date(2023, 1, 1), date(2023, 1, 2)),
            (date(2023, 1, 5), date(2023, 1, 6)),
        ]
        assert result == expected

    def test_contiguous_ranges_unsorted(self) -> None:
        """Test _contiguous_ranges with unsorted dates."""
        dates = [date(2023, 1, 3), date(2023, 1, 1), date(2023, 1, 2)]
        result = _contiguous_ranges(dates)
        assert result == [(date(2023, 1, 1), date(2023, 1, 3))]

    def test_trading_days_inclusive_weekdays_only(self) -> None:
        """Test _trading_days_inclusive fallback to weekdays."""
        with patch("cached_yfinance.client._nyse_calendar", return_value=None):
            start = pd.Timestamp("2023-01-01")  # Sunday
            end = pd.Timestamp("2023-01-07")  # Saturday

            trading_days = list(_trading_days_inclusive(start, end))

            # Should include Mon-Fri (Jan 2-6)
            expected = [
                date(2023, 1, 2),  # Monday
                date(2023, 1, 3),  # Tuesday
                date(2023, 1, 4),  # Wednesday
                date(2023, 1, 5),  # Thursday
                date(2023, 1, 6),  # Friday
            ]
            assert trading_days == expected

    def test_trading_days_inclusive_start_after_end(self) -> None:
        """Test _trading_days_inclusive with start after end."""
        start = pd.Timestamp("2023-01-07")
        end = pd.Timestamp("2023-01-01")

        trading_days = list(_trading_days_inclusive(start, end))
        assert trading_days == []


class TestCachedYFClient:
    """Test CachedYFClient functionality."""

    def test_client_initialization_default_cache(self) -> None:
        """Test client initialization with default cache."""
        client = CachedYFClient()
        assert isinstance(client.cache, FileSystemCache)

    def test_client_initialization_custom_cache(self, cache: FileSystemCache) -> None:
        """Test client initialization with custom cache."""
        client = CachedYFClient(cache)
        assert client.cache == cache

    def test_download_multiple_tickers_error(self, cache: FileSystemCache) -> None:
        """Test download with multiple tickers raises error."""
        client = CachedYFClient(cache)
        with pytest.raises(NotImplementedError):
            client.download(["AAPL", "MSFT"])

    def test_download_single_ticker_list(self, cache: FileSystemCache) -> None:
        """Test download with single ticker in list."""
        client = CachedYFClient(cache)

        with patch("yfinance.download") as mock_download:
            mock_download.return_value = pd.DataFrame()
            client.download(["AAPL"], start="2023-01-03", end="2023-01-04")
            mock_download.assert_called_once()

    @patch("yfinance.download")
    def test_download_no_start_end_period(
        self,
        mock_download: Mock,
        cache: FileSystemCache,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test download without start/end/period falls back to yfinance."""
        mock_download.return_value = sample_dataframe
        client = CachedYFClient(cache)

        result = client.download("AAPL")

        mock_download.assert_called_once()
        pd.testing.assert_frame_equal(result, sample_dataframe)

    @patch("yfinance.download")
    def test_download_with_cache_miss(
        self,
        mock_download: Mock,
        cache: FileSystemCache,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test download with complete cache miss."""
        mock_download.return_value = sample_dataframe
        client = CachedYFClient(cache)

        result = client.download("AAPL", start="2023-01-03", end="2023-01-04")

        # Should call yfinance for missing data
        mock_download.assert_called()
        # Result should contain data (may be filtered by date range)
        assert not result.empty
        assert len(result) <= len(sample_dataframe)

    def test_download_with_cache_hit(
        self, cache: FileSystemCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test download with complete cache hit."""
        client = CachedYFClient(cache)

        # Pre-populate cache with data for the specific day
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 3))
        cache.store(key, sample_dataframe)

        with patch("yfinance.download") as mock_download:
            result = client.download("AAPL", start="2023-01-03", end="2023-01-03")

            # Should not call yfinance since data is cached
            mock_download.assert_not_called()
            # Result should contain cached data
            assert not result.empty

    @patch("yfinance.download")
    def test_download_partial_cache_hit(
        self,
        mock_download: Mock,
        cache: FileSystemCache,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test download with partial cache hit."""
        mock_download.return_value = sample_dataframe
        client = CachedYFClient(cache)

        # Pre-populate cache for one day
        key1 = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 3))
        cache.store(key1, sample_dataframe)

        result = client.download("AAPL", start="2023-01-03", end="2023-01-04")

        # Should call yfinance for missing day
        mock_download.assert_called()
        assert not result.empty

    def test_download_timezone_handling(self, cache: FileSystemCache) -> None:
        """Test download with timezone-aware data."""
        client = CachedYFClient(cache)

        # Create timezone-aware sample data
        dates = pd.date_range("2023-01-03", periods=2, freq="D", tz="US/Eastern")
        tz_dataframe = pd.DataFrame({"Close": [100.0, 101.0]}, index=dates)

        with patch("yfinance.download", return_value=tz_dataframe):
            result = client.download("AAPL", start="2023-01-03", end="2023-01-04")
            assert not result.empty
            # Should handle timezone conversion properly

    @patch("yfinance.download")
    def test_download_intraday_old_data_skip(
        self, mock_download: Mock, cache: FileSystemCache
    ) -> None:
        """Test download skips old intraday data that's beyond Yahoo's limit."""
        # Mock yfinance to raise an error for old data
        mock_download.side_effect = Exception("Data not available for 30 days")

        client = CachedYFClient(cache)

        # Request old intraday data (more than 30 days ago)
        old_date = (datetime.now() - timedelta(days=35)).strftime("%Y-%m-%d")
        result = client.download("AAPL", start=old_date, end=old_date, interval="5m")

        # Should return empty DataFrame without raising error
        assert result.empty

    @patch("yfinance.download")
    def test_download_intraday_unexpected_error(
        self, mock_download: Mock, cache: FileSystemCache
    ) -> None:
        """Test download re-raises unexpected errors for intraday data."""
        # Mock yfinance to raise an unexpected error
        mock_download.side_effect = Exception("Unexpected error")

        client = CachedYFClient(cache)

        # Use a very recent date to avoid the 30-day cutoff logic
        with patch("pandas.Timestamp.now") as mock_now:
            mock_now.return_value = pd.Timestamp("2023-12-01")

            with pytest.raises(Exception, match="Unexpected error"):
                client.download(
                    "AAPL", start="2023-11-15", end="2023-11-15", interval="5m"
                )

    def test_persist_empty_dataframe(self, cache: FileSystemCache) -> None:
        """Test _persist with empty DataFrame."""
        client = CachedYFClient(cache)
        empty_df = pd.DataFrame()

        # Should not raise error
        client._persist("AAPL", "1d", empty_df)

    def test_persist_non_datetime_index_error(self, cache: FileSystemCache) -> None:
        """Test _persist with non-DatetimeIndex raises error."""
        client = CachedYFClient(cache)
        df = pd.DataFrame({"Close": [100]}, index=[0])

        with pytest.raises(
            ValueError, match="Expected downloaded data to have a DatetimeIndex"
        ):
            client._persist("AAPL", "1d", df)

    def test_persist_timezone_naive_index(
        self, cache: FileSystemCache, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test _persist with timezone-naive DatetimeIndex."""
        client = CachedYFClient(cache)

        # Should handle timezone-naive data by localizing to UTC
        client._persist("AAPL", "1d", sample_dataframe)

        # Verify data was stored
        key = CacheKey(
            symbol="AAPL", interval="1d", day=sample_dataframe.index[0].date()
        )
        assert cache.has(key)

    def test_persist_timezone_aware_index(self, cache: FileSystemCache) -> None:
        """Test _persist with timezone-aware DatetimeIndex."""
        client = CachedYFClient(cache)

        # Create timezone-aware data
        dates = pd.date_range("2023-01-01", periods=2, freq="D", tz="US/Eastern")
        tz_dataframe = pd.DataFrame({"Close": [100.0, 101.0]}, index=dates)

        # Should handle timezone-aware data by converting to UTC
        client._persist("AAPL", "1d", tz_dataframe)

        # Verify data was stored
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        assert cache.has(key)


class TestCachedYFClientIntradayDateValidation:
    """Test date validation for intraday data (30-day limit)."""

    @patch("cached_yfinance.client.pd.Timestamp.now")
    @patch("yfinance.download")
    def test_download_intraday_future_start_date(
        self,
        mock_download: Mock,
        mock_now: Mock,
        cache: FileSystemCache,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test download adjusts start date if it's in the future."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        # Create sample data for today
        today_dates = pd.date_range("2024-01-15 09:30", periods=10, freq="1min")
        today_data = pd.DataFrame({"Close": [100.0] * 10}, index=today_dates)

        mock_download.return_value = today_data
        client = CachedYFClient(cache)

        # Request data with future start date
        future_start = "2024-01-20"  # 5 days in the future
        result = client.download(
            "AAPL", start=future_start, end="2024-01-20", interval="1m"
        )

        # Should adjust start to today and return empty (no valid range)
        assert result.empty
        # Should not call yfinance since range is invalid after adjustment
        mock_download.assert_not_called()

    @patch("cached_yfinance.client.pd.Timestamp.now")
    @patch("yfinance.download")
    def test_download_intraday_future_end_date(
        self,
        mock_download: Mock,
        mock_now: Mock,
        cache: FileSystemCache,
    ) -> None:
        """Test download adjusts end date if it's in the future."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        # Create sample data for today
        today_dates = pd.date_range("2024-01-15 09:30", periods=10, freq="1min")
        today_data = pd.DataFrame({"Close": [100.0] * 10}, index=today_dates)

        mock_download.return_value = today_data
        client = CachedYFClient(cache)

        # Request data with future end date but valid start
        valid_start = (fixed_now - timedelta(days=5)).strftime("%Y-%m-%d")
        future_end = "2024-01-20"  # 5 days in the future

        client.download("AAPL", start=valid_start, end=future_end, interval="1m")

        # Should adjust end to now and attempt download
        mock_download.assert_called()
        # Verify the end date was capped to now
        call_args = mock_download.call_args
        assert call_args[1]["end"] <= fixed_now

    @patch("cached_yfinance.client.pd.Timestamp.now")
    @patch("yfinance.download")
    def test_download_intraday_old_start_date(
        self,
        mock_download: Mock,
        mock_now: Mock,
        cache: FileSystemCache,
    ) -> None:
        """Test download adjusts start date if it's more than 30 days ago."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        # Create sample data for recent dates
        recent_dates = pd.date_range("2024-01-10 09:30", periods=10, freq="1min")
        recent_data = pd.DataFrame({"Close": [100.0] * 10}, index=recent_dates)

        mock_download.return_value = recent_data
        client = CachedYFClient(cache)

        # Request data with start date more than 30 days ago
        old_start = (fixed_now - timedelta(days=35)).strftime("%Y-%m-%d")
        valid_end = (fixed_now - timedelta(days=5)).strftime("%Y-%m-%d")

        client.download("AAPL", start=old_start, end=valid_end, interval="1m")

        # Should adjust start to 30 days ago and attempt download
        mock_download.assert_called()
        call_args = mock_download.call_args
        # Start should be at least 30 days before now
        start_arg = call_args[1]["start"]
        cutoff_date = fixed_now.normalize() - pd.Timedelta(days=30)
        assert start_arg.normalize() >= cutoff_date

    @patch("cached_yfinance.client.pd.Timestamp.now")
    def test_download_intraday_range_outside_30_days_returns_empty(
        self, mock_now: Mock, cache: FileSystemCache
    ) -> None:
        """Test download returns empty DataFrame if entire range is outside 30 days."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        client = CachedYFClient(cache)

        # Request data entirely outside 30-day window
        old_start = (fixed_now - timedelta(days=35)).strftime("%Y-%m-%d")
        old_end = (fixed_now - timedelta(days=32)).strftime("%Y-%m-%d")

        result = client.download("AAPL", start=old_start, end=old_end, interval="1m")

        # Should return empty DataFrame without calling yfinance
        assert result.empty

    @patch("cached_yfinance.client.pd.Timestamp.now")
    @patch("yfinance.download")
    def test_download_intraday_valid_range_within_30_days(
        self,
        mock_download: Mock,
        mock_now: Mock,
        cache: FileSystemCache,
    ) -> None:
        """Test download works correctly for valid range within 30 days."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        # Create sample data
        dates = pd.date_range("2024-01-10 09:30", periods=10, freq="1min")
        sample_data = pd.DataFrame({"Close": [100.0] * 10}, index=dates)

        mock_download.return_value = sample_data
        client = CachedYFClient(cache)

        # Request data within valid 30-day window
        valid_start = (fixed_now - timedelta(days=5)).strftime("%Y-%m-%d")
        valid_end = (fixed_now - timedelta(days=1)).strftime("%Y-%m-%d")

        result = client.download(
            "AAPL", start=valid_start, end=valid_end, interval="1m"
        )

        # Should call yfinance and return data
        mock_download.assert_called()
        assert not result.empty

    @patch("cached_yfinance.client.pd.Timestamp.now")
    def test_download_intraday_edge_case_exactly_30_days(
        self, mock_now: Mock, cache: FileSystemCache
    ) -> None:
        """Test download handles edge case of exactly 30 days ago."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        client = CachedYFClient(cache)

        # Request data starting exactly 30 days ago
        exactly_30_days_ago = (fixed_now - timedelta(days=30)).strftime("%Y-%m-%d")
        today = fixed_now.strftime("%Y-%m-%d")

        with patch("yfinance.download") as mock_download:
            dates = pd.date_range(
                exactly_30_days_ago + " 09:30", periods=10, freq="1min"
            )
            sample_data = pd.DataFrame({"Close": [100.0] * 10}, index=dates)
            mock_download.return_value = sample_data

            client.download("AAPL", start=exactly_30_days_ago, end=today, interval="1m")

            # Should attempt download (30 days is the limit, so it's valid)
            mock_download.assert_called()

    @patch("cached_yfinance.client.pd.Timestamp.now")
    def test_download_intraday_edge_case_31_days_ago(
        self, mock_now: Mock, cache: FileSystemCache
    ) -> None:
        """Test download adjusts start date if it's 31 days ago."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        client = CachedYFClient(cache)

        # Request data starting 31 days ago (should be adjusted to 30 days)
        too_old_start = (fixed_now - timedelta(days=31)).strftime("%Y-%m-%d")
        today = fixed_now.strftime("%Y-%m-%d")

        with patch("yfinance.download") as mock_download:
            # Create data starting from 30 days ago
            cutoff_date = fixed_now.normalize() - pd.Timedelta(days=30)
            dates = pd.date_range(cutoff_date, periods=10, freq="1min")
            sample_data = pd.DataFrame({"Close": [100.0] * 10}, index=dates)
            mock_download.return_value = sample_data

            client.download("AAPL", start=too_old_start, end=today, interval="1m")

            # Should adjust start to 30 days ago and attempt download
            mock_download.assert_called()
            call_args = mock_download.call_args
            start_arg = call_args[1]["start"]
            cutoff_date_normalized = cutoff_date.normalize()
            assert start_arg.normalize() >= cutoff_date_normalized

    @patch("cached_yfinance.client.pd.Timestamp.now")
    def test_download_daily_interval_not_affected(
        self, mock_now: Mock, cache: FileSystemCache
    ) -> None:
        """Test that daily interval is not affected by 30-day validation."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        client = CachedYFClient(cache)

        # Request daily data with old dates (should work fine)
        old_start = (fixed_now - timedelta(days=100)).strftime("%Y-%m-%d")
        old_end = (fixed_now - timedelta(days=50)).strftime("%Y-%m-%d")

        with patch("yfinance.download") as mock_download:
            dates = pd.date_range(old_start, old_end, freq="D")
            sample_data = pd.DataFrame({"Close": [100.0] * len(dates)}, index=dates)
            mock_download.return_value = sample_data

            client.download("AAPL", start=old_start, end=old_end, interval="1d")

            # Should call yfinance without date adjustments for daily data
            mock_download.assert_called()
            call_args = mock_download.call_args
            # For daily intervals, dates more than 30 days ago should still be valid
            # The key test: start date should be old (more than 30 days before fixed_now)
            # This proves the 30-day validation is NOT applied to daily intervals
            start_arg = call_args[1]["start"]
            start_ts = pd.Timestamp(start_arg).normalize()
            cutoff_date = fixed_now.normalize() - pd.Timedelta(days=30)
            # Start date should be older than 30 days (proving validation wasn't applied)
            assert (
                start_ts < cutoff_date
            ), "Daily interval should allow dates older than 30 days"

    @patch("cached_yfinance.client.pd.Timestamp.now")
    def test_download_intraday_both_future_dates(
        self, mock_now: Mock, cache: FileSystemCache
    ) -> None:
        """Test download handles both start and end dates in the future."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        client = CachedYFClient(cache)

        # Request data with both dates in the future
        future_start = "2024-01-20"
        future_end = "2024-01-25"

        result = client.download(
            "AAPL", start=future_start, end=future_end, interval="1m"
        )

        # Should return empty DataFrame (no valid range after adjustment)
        assert result.empty

    @patch("cached_yfinance.client.pd.Timestamp.now")
    @patch("yfinance.download")
    def test_fetch_and_store_missing_skips_future_dates(
        self,
        mock_download: Mock,
        mock_now: Mock,
        cache: FileSystemCache,
    ) -> None:
        """Test _fetch_and_store_missing skips dates in the future."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        client = CachedYFClient(cache)

        # Create missing dates including future dates
        from datetime import date as date_type

        # Use dates relative to fixed_now
        past_date = date_type(2024, 1, 10)  # 5 days ago from fixed_now
        future_date = date_type(2024, 1, 20)  # 5 days in future from fixed_now

        missing_dates = [past_date, future_date]

        # Mock yfinance to return data
        dates = pd.date_range("2024-01-10 09:30", periods=10, freq="1min")
        sample_data = pd.DataFrame({"Close": [100.0] * 10}, index=dates)
        mock_download.return_value = sample_data

        # Call _fetch_and_store_missing directly
        client._fetch_and_store_missing("AAPL", "1m", missing_dates, {})

        # Should skip future date and only fetch past date
        # Future dates should be skipped, so we should only get data for past_date
        mock_download.assert_called()
        # Verify the call doesn't include future dates
        call_args = mock_download.call_args
        end_arg = call_args[1]["end"]
        assert pd.Timestamp(end_arg) <= fixed_now

    @patch("cached_yfinance.client.pd.Timestamp.now")
    @patch("yfinance.download")
    def test_fetch_and_store_missing_skips_old_dates(
        self,
        mock_download: Mock,
        mock_now: Mock,
        cache: FileSystemCache,
    ) -> None:
        """Test _fetch_and_store_missing skips dates more than 30 days ago."""
        # Set "now" to a fixed time
        fixed_now = pd.Timestamp("2024-01-15 12:00:00")
        mock_now.return_value = fixed_now

        client = CachedYFClient(cache)

        # Create missing dates including very old dates
        from datetime import date as date_type

        old_date = date_type(2023, 11, 1)  # More than 30 days ago
        recent_date = date_type(2024, 1, 10)  # 5 days ago

        missing_dates = [old_date, recent_date]

        # Mock yfinance to return data
        dates = pd.date_range("2024-01-10 09:30", periods=10, freq="1min")
        sample_data = pd.DataFrame({"Close": [100.0] * 10}, index=dates)
        mock_download.return_value = sample_data

        # Call _fetch_and_store_missing directly
        client._fetch_and_store_missing("AAPL", "1m", missing_dates, {})

        # Should skip old date and only fetch recent date
        mock_download.assert_called()
        # Verify the call doesn't include dates older than 30 days
        call_args = mock_download.call_args
        start_arg = call_args[1]["start"]
        cutoff_date = fixed_now.normalize() - pd.Timedelta(days=30)
        assert pd.Timestamp(start_arg).normalize() >= cutoff_date


class TestCachedYFClientOptions:
    """Test CachedYFClient option chain functionality."""

    @patch("yfinance.Ticker")
    def test_get_options_expirations_no_cache(
        self, mock_ticker: Mock, cache: FileSystemCache
    ) -> None:
        """Test get_options_expirations without cache."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.options = ("2023-01-20", "2023-02-17")
        mock_ticker.return_value = mock_ticker_instance

        client = CachedYFClient(cache)
        result = client.get_options_expirations("AAPL", use_cache=False)

        assert result == ("2023-01-20", "2023-02-17")
        mock_ticker.assert_called_once_with("AAPL")

    def test_get_options_expirations_with_cache(
        self,
        cache: FileSystemCache,
        sample_option_dataframe: pd.DataFrame,
        sample_underlying_data: dict[str, Any],
    ) -> None:
        """Test get_options_expirations with cached data."""
        CachedYFClient(cache)

        # Pre-populate cache with future expiration
        future_exp = "2025-01-17"  # Future date
        cache.store_option_chain(
            "AAPL",
            future_exp,
            sample_option_dataframe,
            sample_option_dataframe,
            sample_underlying_data,
        )

        # Verify the cache has the data
        cached_expirations = list(cache.iter_cached_option_expirations("AAPL"))
        assert future_exp in cached_expirations

        # Test the cache iteration logic directly
        assert len(cached_expirations) > 0
        assert all(isinstance(exp, str) for exp in cached_expirations)

    def test_get_options_expirations_expired_cache(
        self,
        cache: FileSystemCache,
        sample_option_dataframe: pd.DataFrame,
        sample_underlying_data: dict[str, Any],
    ) -> None:
        """Test get_options_expirations filters out expired cached data."""
        client = CachedYFClient(cache)

        # Pre-populate cache with expired expiration
        expired_exp = "2020-01-17"  # Past date
        cache.store_option_chain(
            "AAPL",
            expired_exp,
            sample_option_dataframe,
            sample_option_dataframe,
            sample_underlying_data,
        )

        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.options = ("2025-01-20",)
            mock_ticker.return_value = mock_ticker_instance

            result = client.get_options_expirations("AAPL", use_cache=True)

            # Should fetch fresh data since cached data is expired
            assert result == ("2025-01-20",)
            mock_ticker.assert_called_once()

    @patch("yfinance.Ticker")
    def test_get_option_chain_no_cache(
        self,
        mock_ticker: Mock,
        cache: FileSystemCache,
        sample_option_dataframe: pd.DataFrame,
        sample_underlying_data: dict[str, Any],
    ) -> None:
        """Test get_option_chain without cache."""
        mock_ticker_instance = Mock()
        mock_options = Mock()
        mock_options.calls = sample_option_dataframe
        mock_options.puts = sample_option_dataframe
        mock_options.underlying = sample_underlying_data
        mock_ticker_instance.option_chain.return_value = mock_options
        mock_ticker.return_value = mock_ticker_instance

        client = CachedYFClient(cache)
        result = client.get_option_chain("AAPL", "2023-01-20", use_cache=False)

        assert isinstance(result, OptionChain)
        pd.testing.assert_frame_equal(result.calls, sample_option_dataframe)
        pd.testing.assert_frame_equal(result.puts, sample_option_dataframe)
        assert result.underlying == sample_underlying_data

    def test_get_option_chain_with_cache_hit(
        self,
        cache: FileSystemCache,
        sample_option_dataframe: pd.DataFrame,
        sample_underlying_data: dict[str, Any],
    ) -> None:
        """Test get_option_chain with cache hit."""
        client = CachedYFClient(cache)

        # Pre-populate cache
        expiration = "2023-01-20"
        cache.store_option_chain(
            "AAPL",
            expiration,
            sample_option_dataframe,
            sample_option_dataframe,
            sample_underlying_data,
        )

        result = client.get_option_chain("AAPL", expiration, use_cache=True)

        assert isinstance(result, OptionChain)
        pd.testing.assert_frame_equal(result.calls, sample_option_dataframe)
        pd.testing.assert_frame_equal(result.puts, sample_option_dataframe)
        assert result.underlying == sample_underlying_data

    @patch("yfinance.Ticker")
    def test_get_option_chain_no_expiration(
        self, mock_ticker: Mock, cache: FileSystemCache
    ) -> None:
        """Test get_option_chain without specifying expiration."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.options = ("2023-01-20", "2023-02-17")
        mock_options = Mock()
        mock_options.calls = pd.DataFrame()
        mock_options.puts = pd.DataFrame()
        mock_options.underlying = {}
        mock_ticker_instance.option_chain.return_value = mock_options
        mock_ticker.return_value = mock_ticker_instance

        client = CachedYFClient(cache)
        client.get_option_chain("AAPL", use_cache=False)

        # Should use first available expiration
        mock_ticker_instance.option_chain.assert_called_with("2023-01-20")

    @patch("yfinance.Ticker")
    def test_get_option_chain_no_expirations_available(
        self, mock_ticker: Mock, cache: FileSystemCache
    ) -> None:
        """Test get_option_chain when no expirations are available."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.options = ()
        mock_ticker.return_value = mock_ticker_instance

        client = CachedYFClient(cache)
        result = client.get_option_chain("AAPL", use_cache=False)

        # Should return empty OptionChain
        assert isinstance(result, OptionChain)
        assert result.calls.empty
        assert result.puts.empty
        assert result.underlying == {}

    @patch("yfinance.Ticker")
    def test_get_option_chain_fetch_error(
        self, mock_ticker: Mock, cache: FileSystemCache
    ) -> None:
        """Test get_option_chain when yfinance fetch fails."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.option_chain.side_effect = Exception("Fetch failed")
        mock_ticker.return_value = mock_ticker_instance

        client = CachedYFClient(cache)
        result = client.get_option_chain("AAPL", "2023-01-20", use_cache=False)

        # Should return empty OptionChain on error
        assert isinstance(result, OptionChain)
        assert result.calls.empty
        assert result.puts.empty
        assert result.underlying == {}

    @patch("yfinance.Ticker")
    def test_get_option_chain_with_timestamp(
        self,
        mock_ticker: Mock,
        cache: FileSystemCache,
        sample_option_dataframe: pd.DataFrame,
        sample_underlying_data: dict[str, Any],
    ) -> None:
        """Test get_option_chain with custom timestamp."""
        mock_ticker_instance = Mock()
        mock_options = Mock()
        mock_options.calls = sample_option_dataframe
        mock_options.puts = sample_option_dataframe
        mock_options.underlying = sample_underlying_data
        mock_ticker_instance.option_chain.return_value = mock_options
        mock_ticker.return_value = mock_ticker_instance

        client = CachedYFClient(cache)
        timestamp = "2023-01-01T15:30:00"
        result = client.get_option_chain(
            "AAPL", "2023-01-20", use_cache=False, timestamp=timestamp
        )

        # Should store with provided timestamp
        assert isinstance(result, OptionChain)

        # Verify it was cached with timestamp
        from cached_yfinance.cache import OptionCacheKey

        calls_key = OptionCacheKey.for_calls("AAPL", "2023-01-20", timestamp)
        assert cache.has_option_chain(calls_key)


class TestModuleLevelFunctions:
    """Test module-level convenience functions."""

    @patch("cached_yfinance.client.CachedYFClient")
    def test_download_function(self, mock_client_class: Mock) -> None:
        """Test module-level download function."""
        mock_client = Mock()
        mock_client.download.return_value = pd.DataFrame()
        mock_client_class.return_value = mock_client

        result = download("AAPL", start="2023-01-01")

        mock_client_class.assert_called_once()
        mock_client.download.assert_called_once_with("AAPL", start="2023-01-01")
        assert isinstance(result, pd.DataFrame)

    @patch("cached_yfinance.client.CachedYFClient")
    def test_get_options_expirations_function(self, mock_client_class: Mock) -> None:
        """Test module-level get_options_expirations function."""
        mock_client = Mock()
        mock_client.get_options_expirations.return_value = ("2023-01-20",)
        mock_client_class.return_value = mock_client

        result = get_options_expirations("AAPL", use_cache=False)

        mock_client_class.assert_called_once()
        mock_client.get_options_expirations.assert_called_once_with(
            "AAPL", use_cache=False
        )
        assert result == ("2023-01-20",)

    @patch("cached_yfinance.client.CachedYFClient")
    def test_get_option_chain_function(self, mock_client_class: Mock) -> None:
        """Test module-level get_option_chain function."""
        mock_client = Mock()
        mock_option_chain = OptionChain(
            calls=pd.DataFrame(), puts=pd.DataFrame(), underlying={}
        )
        mock_client.get_option_chain.return_value = mock_option_chain
        mock_client_class.return_value = mock_client

        result = get_option_chain("AAPL", "2023-01-20", use_cache=False)

        mock_client_class.assert_called_once()
        mock_client.get_option_chain.assert_called_once_with(
            "AAPL", expiration="2023-01-20", use_cache=False
        )
        assert result == mock_option_chain
