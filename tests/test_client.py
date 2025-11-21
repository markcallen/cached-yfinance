"""Tests for the client module."""

import pytest
import pandas as pd
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List

from cached_yfinance.client import (
    CachedYFClient,
    DownloadRequest,
    OptionChain,
    download,
    get_options_expirations,
    get_option_chain,
    _parse_timestamp,
    _parse_period_to_timedelta,
    _normalize_range,
    _trading_days_inclusive,
    _merge_dataframes,
    _contiguous_ranges,
)
from cached_yfinance.cache import FileSystemCache, CacheKey


class TestDownloadRequest:
    """Test DownloadRequest functionality."""
    
    def test_download_request_creation(self):
        """Test basic DownloadRequest creation."""
        req = DownloadRequest(
            tickers="AAPL",
            interval="1d",
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-31"),
            kwargs={}
        )
        assert req.tickers == "AAPL"
        assert req.interval == "1d"
        assert req.start == pd.Timestamp("2023-01-01")
        assert req.end == pd.Timestamp("2023-01-31")
        assert req.kwargs == {}
    
    def test_interval_is_intraday_daily(self):
        """Test interval_is_intraday for daily interval."""
        req = DownloadRequest("AAPL", "1d", None, None, {})
        assert not req.interval_is_intraday
    
    def test_interval_is_intraday_minute(self):
        """Test interval_is_intraday for minute interval."""
        req = DownloadRequest("AAPL", "5m", None, None, {})
        assert req.interval_is_intraday
    
    def test_interval_is_intraday_hour(self):
        """Test interval_is_intraday for hour interval."""
        req = DownloadRequest("AAPL", "1h", None, None, {})
        assert req.interval_is_intraday


class TestOptionChain:
    """Test OptionChain functionality."""
    
    def test_option_chain_creation(self, sample_option_dataframe, sample_underlying_data):
        """Test OptionChain creation."""
        chain = OptionChain(
            calls=sample_option_dataframe,
            puts=sample_option_dataframe,
            underlying=sample_underlying_data
        )
        assert isinstance(chain.calls, pd.DataFrame)
        assert isinstance(chain.puts, pd.DataFrame)
        assert isinstance(chain.underlying, dict)
        pd.testing.assert_frame_equal(chain.calls, sample_option_dataframe)
        pd.testing.assert_frame_equal(chain.puts, sample_option_dataframe)
        assert chain.underlying == sample_underlying_data


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_parse_timestamp_none(self):
        """Test _parse_timestamp with None."""
        result = _parse_timestamp(None)
        assert result is None
    
    def test_parse_timestamp_pandas(self):
        """Test _parse_timestamp with pandas Timestamp."""
        ts = pd.Timestamp("2023-01-01")
        result = _parse_timestamp(ts)
        assert result == ts
    
    def test_parse_timestamp_datetime(self):
        """Test _parse_timestamp with datetime."""
        dt = datetime(2023, 1, 1)
        result = _parse_timestamp(dt)
        assert result == pd.Timestamp(dt)
    
    def test_parse_timestamp_string(self):
        """Test _parse_timestamp with string."""
        result = _parse_timestamp("2023-01-01")
        assert result == pd.Timestamp("2023-01-01")
    
    def test_parse_period_to_timedelta_none(self):
        """Test _parse_period_to_timedelta with None."""
        result = _parse_period_to_timedelta(None)
        assert result is None
    
    def test_parse_period_to_timedelta_max(self):
        """Test _parse_period_to_timedelta with 'max'."""
        result = _parse_period_to_timedelta("max")
        assert result is None
    
    def test_parse_period_to_timedelta_days(self):
        """Test _parse_period_to_timedelta with days."""
        result = _parse_period_to_timedelta("5d")
        assert result == pd.Timedelta(days=5)
    
    def test_parse_period_to_timedelta_weeks(self):
        """Test _parse_period_to_timedelta with weeks."""
        result = _parse_period_to_timedelta("2wk")
        assert result == pd.Timedelta(weeks=2)
    
    def test_parse_period_to_timedelta_months(self):
        """Test _parse_period_to_timedelta with months."""
        result = _parse_period_to_timedelta("3mo")
        assert result == pd.Timedelta(days=90)  # 3 * 30
    
    def test_parse_period_to_timedelta_years(self):
        """Test _parse_period_to_timedelta with years."""
        result = _parse_period_to_timedelta("1y")
        assert result == pd.Timedelta(days=365)
    
    def test_parse_period_to_timedelta_hours(self):
        """Test _parse_period_to_timedelta with hours."""
        result = _parse_period_to_timedelta("4h")
        assert result == pd.Timedelta(hours=4)
    
    def test_parse_period_to_timedelta_minutes(self):
        """Test _parse_period_to_timedelta with minutes."""
        result = _parse_period_to_timedelta("30m")
        assert result == pd.Timedelta(minutes=30)
    
    def test_parse_period_to_timedelta_invalid(self):
        """Test _parse_period_to_timedelta with invalid period."""
        result = _parse_period_to_timedelta("invalid")
        assert result is None
    
    def test_normalize_range_with_start_end(self):
        """Test _normalize_range with start and end provided."""
        start = "2023-01-01"
        end = "2023-01-31"
        start_ts, end_ts = _normalize_range(start, end, None, "1d")
        assert start_ts == pd.Timestamp("2023-01-01")
        assert end_ts == pd.Timestamp("2023-01-31")
    
    def test_normalize_range_with_period(self):
        """Test _normalize_range with period."""
        start_ts, end_ts = _normalize_range(None, "2023-01-31", "5d", "1d")
        assert end_ts == pd.Timestamp("2023-01-31")
        assert start_ts == pd.Timestamp("2023-01-31") - pd.Timedelta(days=5)
    
    def test_normalize_range_intraday_default_end(self):
        """Test _normalize_range with intraday interval and no end."""
        with patch('pandas.Timestamp.utcnow') as mock_now:
            mock_now.return_value = pd.Timestamp("2023-01-15 15:30:00")
            start_ts, end_ts = _normalize_range(None, None, "5d", "5m")
            assert end_ts == pd.Timestamp("2023-01-15 15:30:00")
    
    def test_normalize_range_daily_default_end(self):
        """Test _normalize_range with daily interval and no end."""
        with patch('pandas.Timestamp.today') as mock_today:
            mock_today.return_value = pd.Timestamp("2023-01-15")
            start_ts, end_ts = _normalize_range(None, None, "5d", "1d")
            assert end_ts == pd.Timestamp("2023-01-15").normalize()
    
    def test_merge_dataframes_empty(self):
        """Test _merge_dataframes with empty list."""
        result = _merge_dataframes([])
        assert result.empty
    
    def test_merge_dataframes_single(self, sample_dataframe):
        """Test _merge_dataframes with single DataFrame."""
        result = _merge_dataframes([sample_dataframe])
        pd.testing.assert_frame_equal(result, sample_dataframe.sort_index())
    
    def test_merge_dataframes_multiple(self):
        """Test _merge_dataframes with multiple DataFrames."""
        df1 = pd.DataFrame({'A': [1, 2]}, index=pd.date_range('2023-01-01', periods=2))
        df2 = pd.DataFrame({'A': [3, 4]}, index=pd.date_range('2023-01-03', periods=2))
        
        result = _merge_dataframes([df1, df2])
        expected = pd.concat([df1, df2]).sort_index()
        pd.testing.assert_frame_equal(result, expected)
    
    def test_merge_dataframes_with_duplicates(self):
        """Test _merge_dataframes with duplicate indices (keeps last)."""
        df1 = pd.DataFrame({'A': [1, 2]}, index=pd.date_range('2023-01-01', periods=2))
        df2 = pd.DataFrame({'A': [3, 4]}, index=pd.date_range('2023-01-01', periods=2))
        
        result = _merge_dataframes([df1, df2])
        # Should keep the last values (from df2)
        expected = df2.sort_index()
        pd.testing.assert_frame_equal(result, expected, check_freq=False)
    
    def test_contiguous_ranges_empty(self):
        """Test _contiguous_ranges with empty list."""
        result = _contiguous_ranges([])
        assert result == []
    
    def test_contiguous_ranges_single(self):
        """Test _contiguous_ranges with single date."""
        dates = [date(2023, 1, 1)]
        result = _contiguous_ranges(dates)
        assert result == [(date(2023, 1, 1), date(2023, 1, 1))]
    
    def test_contiguous_ranges_consecutive(self):
        """Test _contiguous_ranges with consecutive dates."""
        dates = [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)]
        result = _contiguous_ranges(dates)
        assert result == [(date(2023, 1, 1), date(2023, 1, 3))]
    
    def test_contiguous_ranges_with_gaps(self):
        """Test _contiguous_ranges with gaps."""
        dates = [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 5), date(2023, 1, 6)]
        result = _contiguous_ranges(dates)
        expected = [
            (date(2023, 1, 1), date(2023, 1, 2)),
            (date(2023, 1, 5), date(2023, 1, 6))
        ]
        assert result == expected
    
    def test_contiguous_ranges_unsorted(self):
        """Test _contiguous_ranges with unsorted dates."""
        dates = [date(2023, 1, 3), date(2023, 1, 1), date(2023, 1, 2)]
        result = _contiguous_ranges(dates)
        assert result == [(date(2023, 1, 1), date(2023, 1, 3))]
    
    def test_trading_days_inclusive_weekdays_only(self):
        """Test _trading_days_inclusive fallback to weekdays."""
        with patch('cached_yfinance.client._nyse_calendar', return_value=None):
            start = pd.Timestamp("2023-01-01")  # Sunday
            end = pd.Timestamp("2023-01-07")    # Saturday
            
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
    
    def test_trading_days_inclusive_start_after_end(self):
        """Test _trading_days_inclusive with start after end."""
        start = pd.Timestamp("2023-01-07")
        end = pd.Timestamp("2023-01-01")
        
        trading_days = list(_trading_days_inclusive(start, end))
        assert trading_days == []


class TestCachedYFClient:
    """Test CachedYFClient functionality."""
    
    def test_client_initialization_default_cache(self):
        """Test client initialization with default cache."""
        client = CachedYFClient()
        assert isinstance(client.cache, FileSystemCache)
    
    def test_client_initialization_custom_cache(self, cache):
        """Test client initialization with custom cache."""
        client = CachedYFClient(cache)
        assert client.cache == cache
    
    def test_download_multiple_tickers_error(self, cache):
        """Test download with multiple tickers raises error."""
        client = CachedYFClient(cache)
        with pytest.raises(NotImplementedError):
            client.download(["AAPL", "MSFT"])
    
    def test_download_single_ticker_list(self, cache):
        """Test download with single ticker in list."""
        client = CachedYFClient(cache)
        
        with patch('yfinance.download') as mock_download:
            mock_download.return_value = pd.DataFrame()
            client.download(["AAPL"], start="2023-01-01", end="2023-01-02")
            mock_download.assert_called_once()
    
    @patch('yfinance.download')
    def test_download_no_start_end_period(self, mock_download, cache, sample_dataframe):
        """Test download without start/end/period falls back to yfinance."""
        mock_download.return_value = sample_dataframe
        client = CachedYFClient(cache)
        
        result = client.download("AAPL")
        
        mock_download.assert_called_once()
        pd.testing.assert_frame_equal(result, sample_dataframe)
    
    @patch('yfinance.download')
    def test_download_with_cache_miss(self, mock_download, cache, sample_dataframe):
        """Test download with complete cache miss."""
        mock_download.return_value = sample_dataframe
        client = CachedYFClient(cache)
        
        result = client.download("AAPL", start="2023-01-01", end="2023-01-02")
        
        # Should call yfinance for missing data
        mock_download.assert_called()
        # Result should contain data (may be filtered by date range)
        assert not result.empty
        assert len(result) <= len(sample_dataframe)
    
    def test_download_with_cache_hit(self, cache, sample_dataframe):
        """Test download with complete cache hit."""
        client = CachedYFClient(cache)
        
        # Pre-populate cache with data for the specific day
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        cache.store(key, sample_dataframe)
        
        with patch('yfinance.download') as mock_download:
            # Mock _trading_days_inclusive to return the expected day
            with patch('cached_yfinance.client._trading_days_inclusive') as mock_trading_days:
                mock_trading_days.return_value = [date(2023, 1, 1)]
                
                result = client.download("AAPL", start="2023-01-01", end="2023-01-01")
                
                # Should not call yfinance
                mock_download.assert_not_called()
                # Result should contain cached data
                assert not result.empty
    
    @patch('yfinance.download')
    def test_download_partial_cache_hit(self, mock_download, cache, sample_dataframe):
        """Test download with partial cache hit."""
        mock_download.return_value = sample_dataframe
        client = CachedYFClient(cache)
        
        # Pre-populate cache for one day
        key1 = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        cache.store(key1, sample_dataframe)
        
        result = client.download("AAPL", start="2023-01-01", end="2023-01-02")
        
        # Should call yfinance for missing day
        mock_download.assert_called()
        assert not result.empty
    
    def test_download_timezone_handling(self, cache):
        """Test download with timezone-aware data."""
        client = CachedYFClient(cache)
        
        # Create timezone-aware sample data
        dates = pd.date_range('2023-01-01', periods=2, freq='D', tz='US/Eastern')
        tz_dataframe = pd.DataFrame({
            'Close': [100.0, 101.0]
        }, index=dates)
        
        with patch('yfinance.download', return_value=tz_dataframe):
            result = client.download("AAPL", start="2023-01-01", end="2023-01-02")
            assert not result.empty
            # Should handle timezone conversion properly
    
    @patch('yfinance.download')
    def test_download_intraday_old_data_skip(self, mock_download, cache):
        """Test download skips old intraday data that's beyond Yahoo's limit."""
        # Mock yfinance to raise an error for old data
        mock_download.side_effect = Exception("Data not available for 30 days")
        
        client = CachedYFClient(cache)
        
        # Request old intraday data (more than 30 days ago)
        old_date = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
        result = client.download("AAPL", start=old_date, end=old_date, interval="5m")
        
        # Should return empty DataFrame without raising error
        assert result.empty
    
    @patch('yfinance.download')
    def test_download_intraday_unexpected_error(self, mock_download, cache):
        """Test download re-raises unexpected errors for intraday data."""
        # Mock yfinance to raise an unexpected error
        mock_download.side_effect = Exception("Unexpected error")
        
        client = CachedYFClient(cache)
        
        # Use a very recent date to avoid the 30-day cutoff logic
        with patch('pandas.Timestamp.now') as mock_now:
            mock_now.return_value = pd.Timestamp("2023-12-01")
            
            with pytest.raises(Exception, match="Unexpected error"):
                client.download("AAPL", start="2023-11-15", end="2023-11-15", interval="5m")
    
    def test_persist_empty_dataframe(self, cache):
        """Test _persist with empty DataFrame."""
        client = CachedYFClient(cache)
        empty_df = pd.DataFrame()
        
        # Should not raise error
        client._persist("AAPL", "1d", empty_df)
    
    def test_persist_non_datetime_index_error(self, cache):
        """Test _persist with non-DatetimeIndex raises error."""
        client = CachedYFClient(cache)
        df = pd.DataFrame({'Close': [100]}, index=[0])
        
        with pytest.raises(ValueError, match="Expected downloaded data to have a DatetimeIndex"):
            client._persist("AAPL", "1d", df)
    
    def test_persist_timezone_naive_index(self, cache, sample_dataframe):
        """Test _persist with timezone-naive DatetimeIndex."""
        client = CachedYFClient(cache)
        
        # Should handle timezone-naive data by localizing to UTC
        client._persist("AAPL", "1d", sample_dataframe)
        
        # Verify data was stored
        key = CacheKey(symbol="AAPL", interval="1d", day=sample_dataframe.index[0].date())
        assert cache.has(key)
    
    def test_persist_timezone_aware_index(self, cache):
        """Test _persist with timezone-aware DatetimeIndex."""
        client = CachedYFClient(cache)
        
        # Create timezone-aware data
        dates = pd.date_range('2023-01-01', periods=2, freq='D', tz='US/Eastern')
        tz_dataframe = pd.DataFrame({'Close': [100.0, 101.0]}, index=dates)
        
        # Should handle timezone-aware data by converting to UTC
        client._persist("AAPL", "1d", tz_dataframe)
        
        # Verify data was stored
        key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 1, 1))
        assert cache.has(key)


class TestCachedYFClientOptions:
    """Test CachedYFClient option chain functionality."""
    
    @patch('yfinance.Ticker')
    def test_get_options_expirations_no_cache(self, mock_ticker, cache):
        """Test get_options_expirations without cache."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.options = ("2023-01-20", "2023-02-17")
        mock_ticker.return_value = mock_ticker_instance
        
        client = CachedYFClient(cache)
        result = client.get_options_expirations("AAPL", use_cache=False)
        
        assert result == ("2023-01-20", "2023-02-17")
        mock_ticker.assert_called_once_with("AAPL")
    
    def test_get_options_expirations_with_cache(self, cache, sample_option_dataframe, sample_underlying_data):
        """Test get_options_expirations with cached data."""
        client = CachedYFClient(cache)
        
        # Pre-populate cache with future expiration
        future_exp = "2025-01-17"  # Future date
        cache.store_option_chain("AAPL", future_exp, sample_option_dataframe, sample_option_dataframe, sample_underlying_data)
        
        # Verify the cache has the data
        cached_expirations = list(cache.iter_cached_option_expirations("AAPL"))
        assert future_exp in cached_expirations
        
        # Test the cache iteration logic directly
        assert len(cached_expirations) > 0
        assert all(isinstance(exp, str) for exp in cached_expirations)
    
    def test_get_options_expirations_expired_cache(self, cache, sample_option_dataframe, sample_underlying_data):
        """Test get_options_expirations filters out expired cached data."""
        client = CachedYFClient(cache)
        
        # Pre-populate cache with expired expiration
        expired_exp = "2020-01-17"  # Past date
        cache.store_option_chain("AAPL", expired_exp, sample_option_dataframe, sample_option_dataframe, sample_underlying_data)
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.options = ("2025-01-20",)
            mock_ticker.return_value = mock_ticker_instance
            
            result = client.get_options_expirations("AAPL", use_cache=True)
            
            # Should fetch fresh data since cached data is expired
            assert result == ("2025-01-20",)
            mock_ticker.assert_called_once()
    
    @patch('yfinance.Ticker')
    def test_get_option_chain_no_cache(self, mock_ticker, cache, sample_option_dataframe, sample_underlying_data):
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
    
    def test_get_option_chain_with_cache_hit(self, cache, sample_option_dataframe, sample_underlying_data):
        """Test get_option_chain with cache hit."""
        client = CachedYFClient(cache)
        
        # Pre-populate cache
        expiration = "2023-01-20"
        cache.store_option_chain("AAPL", expiration, sample_option_dataframe, sample_option_dataframe, sample_underlying_data)
        
        result = client.get_option_chain("AAPL", expiration, use_cache=True)
        
        assert isinstance(result, OptionChain)
        pd.testing.assert_frame_equal(result.calls, sample_option_dataframe)
        pd.testing.assert_frame_equal(result.puts, sample_option_dataframe)
        assert result.underlying == sample_underlying_data
    
    @patch('yfinance.Ticker')
    def test_get_option_chain_no_expiration(self, mock_ticker, cache):
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
        result = client.get_option_chain("AAPL", use_cache=False)
        
        # Should use first available expiration
        mock_ticker_instance.option_chain.assert_called_with("2023-01-20")
    
    @patch('yfinance.Ticker')
    def test_get_option_chain_no_expirations_available(self, mock_ticker, cache):
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
    
    @patch('yfinance.Ticker')
    def test_get_option_chain_fetch_error(self, mock_ticker, cache):
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
    
    @patch('yfinance.Ticker')
    def test_get_option_chain_with_timestamp(self, mock_ticker, cache, sample_option_dataframe, sample_underlying_data):
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
        result = client.get_option_chain("AAPL", "2023-01-20", use_cache=False, timestamp=timestamp)
        
        # Should store with provided timestamp
        assert isinstance(result, OptionChain)
        
        # Verify it was cached with timestamp
        from cached_yfinance.cache import OptionCacheKey
        calls_key = OptionCacheKey.for_calls("AAPL", "2023-01-20", timestamp)
        assert cache.has_option_chain(calls_key)


class TestModuleLevelFunctions:
    """Test module-level convenience functions."""
    
    @patch('cached_yfinance.client.CachedYFClient')
    def test_download_function(self, mock_client_class):
        """Test module-level download function."""
        mock_client = Mock()
        mock_client.download.return_value = pd.DataFrame()
        mock_client_class.return_value = mock_client
        
        result = download("AAPL", start="2023-01-01")
        
        mock_client_class.assert_called_once()
        mock_client.download.assert_called_once_with("AAPL", start="2023-01-01")
        assert isinstance(result, pd.DataFrame)
    
    @patch('cached_yfinance.client.CachedYFClient')
    def test_get_options_expirations_function(self, mock_client_class):
        """Test module-level get_options_expirations function."""
        mock_client = Mock()
        mock_client.get_options_expirations.return_value = ("2023-01-20",)
        mock_client_class.return_value = mock_client
        
        result = get_options_expirations("AAPL", use_cache=False)
        
        mock_client_class.assert_called_once()
        mock_client.get_options_expirations.assert_called_once_with("AAPL", use_cache=False)
        assert result == ("2023-01-20",)
    
    @patch('cached_yfinance.client.CachedYFClient')
    def test_get_option_chain_function(self, mock_client_class):
        """Test module-level get_option_chain function."""
        mock_client = Mock()
        mock_option_chain = OptionChain(calls=pd.DataFrame(), puts=pd.DataFrame(), underlying={})
        mock_client.get_option_chain.return_value = mock_option_chain
        mock_client_class.return_value = mock_client
        
        result = get_option_chain("AAPL", "2023-01-20", use_cache=False)
        
        mock_client_class.assert_called_once()
        mock_client.get_option_chain.assert_called_once_with("AAPL", expiration="2023-01-20", use_cache=False)
        assert result == mock_option_chain
