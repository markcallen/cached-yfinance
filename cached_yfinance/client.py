from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Tuple, Union, NamedTuple

import pandas as pd
import yfinance as yf

try:  # pragma: no cover - optional dependency
    import pandas_market_calendars as mcal
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    mcal = None

from .cache import CacheKey, FileSystemCache, OptionCacheKey


TickerInput = Union[str, List[str]]


class OptionChain(NamedTuple):
    """Option chain data structure matching yfinance.ticker.Options"""

    calls: pd.DataFrame
    puts: pd.DataFrame
    underlying: dict


@dataclass
class DownloadRequest:
    tickers: str
    interval: str
    start: Optional[pd.Timestamp]
    end: Optional[pd.Timestamp]
    kwargs: Dict[str, object]

    @property
    def interval_is_intraday(self) -> bool:
        return any(self.interval.endswith(suffix) for suffix in ("m", "h"))


def _parse_timestamp(
    value: Optional[Union[str, datetime, pd.Timestamp]],
) -> Optional[pd.Timestamp]:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value
    return pd.to_datetime(value)


def _parse_period_to_timedelta(period: Optional[str]) -> Optional[pd.Timedelta]:
    if period is None:
        return None
    period = period.strip().lower()
    if period == "max":
        return None
    suffix_map = {
        "d": "days",
        "wk": "weeks",
        "mo": "days",  # approximate 30-day month
        "y": "days",
        "h": "hours",
        "m": "minutes",
    }
    for suffix, unit in suffix_map.items():
        if period.endswith(suffix):
            try:
                value = float(period.replace(suffix, ""))
            except ValueError:
                return None
            if unit == "days" and suffix == "mo":
                value *= 30
            elif unit == "days" and suffix == "y":
                value *= 365
            kwargs = {unit: value}
            return pd.Timedelta(**kwargs)
    try:
        return pd.to_timedelta(period)
    except Exception:
        return None


def _normalize_range(
    start: Optional[pd.Timestamp],
    end: Optional[pd.Timestamp],
    period: Optional[str],
    interval: str,
) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    end_ts = _parse_timestamp(end)
    start_ts = _parse_timestamp(start)

    if end_ts is None:
        end_ts = (
            pd.Timestamp.utcnow()
            if any(interval.endswith(s) for s in ("m", "h"))
            else pd.Timestamp.today().normalize()
        )

    if start_ts is None and period:
        delta = _parse_period_to_timedelta(period)
        if delta is not None:
            start_ts = end_ts - delta

    return start_ts, end_ts


@lru_cache(maxsize=1)
def _nyse_calendar():
    if mcal is None:
        return None
    try:  # pragma: no cover - relies on optional dependency
        return mcal.get_calendar("NYSE")
    except Exception:  # pragma: no cover - defensive, optional dependency
        return None


def _trading_days_inclusive(start: pd.Timestamp, end: pd.Timestamp) -> Iterable[date]:
    start = start.normalize()
    end = end.normalize()
    if start > end:
        return []

    calendar = _nyse_calendar()
    if calendar is not None:
        schedule = calendar.schedule(start.date().isoformat(), end.date().isoformat())
        if not schedule.empty:
            # schedule index represents trading sessions
            return [ts.date() for ts in schedule.index]

    # Fallback: weekdays only (Mon-Fri)
    current = start.date()
    end_date = end.date()
    trading_days: List[date] = []
    while current <= end_date:
        if current.weekday() < 5:
            trading_days.append(current)
        current = current + timedelta(days=1)
    return trading_days


def _merge_dataframes(frames: List[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df


def _contiguous_ranges(dates: List[date]) -> List[Tuple[date, date]]:
    if not dates:
        return []
    dates = sorted(dates)
    ranges: List[Tuple[date, date]] = []
    start = prev = dates[0]
    for current in dates[1:]:
        if current == prev + timedelta(days=1):
            prev = current
            continue
        ranges.append((start, prev))
        start = prev = current
    ranges.append((start, prev))
    return ranges


class CachedYFClient:
    """
    Wrapper around yfinance.download that persists responses to disk.
    """

    def __init__(self, cache: Optional[FileSystemCache] = None):
        self.cache = cache or FileSystemCache()

    def download(
        self,
        tickers: TickerInput,
        start: Optional[Union[str, datetime, pd.Timestamp]] = None,
        end: Optional[Union[str, datetime, pd.Timestamp]] = None,
        period: Optional[str] = None,
        interval: str = "1d",
        **kwargs,
    ) -> pd.DataFrame:
        if isinstance(tickers, list):
            if len(tickers) != 1:
                raise NotImplementedError(
                    "CachedYFClient currently supports a single ticker per download request."
                )
            tickers = tickers[0]

        tickers = tickers.strip()
        req = DownloadRequest(tickers, interval, None, None, kwargs)
        start_ts, end_ts = _normalize_range(start, end, period, interval)
        req.start = start_ts
        req.end = end_ts

        if start_ts is None or end_ts is None:
            fetched = yf.download(
                tickers,
                start=start,
                end=end,
                period=period,
                interval=interval,
                auto_adjust=False,
                **kwargs,
            )
            self._persist(tickers, interval, fetched)
            return fetched

        cached_frames, missing_dates = self._load_from_cache(
            tickers, interval, start_ts, end_ts
        )

        if missing_dates:
            new_frames = self._fetch_and_store_missing(
                tickers, interval, missing_dates, kwargs
            )
            cached_frames.extend(new_frames)

        merged = _merge_dataframes(cached_frames)
        if merged.empty:
            return merged

        if req.start is not None:
            # Ensure timezone consistency for comparison
            start_tz = req.start
            if merged.index.tz is not None and start_tz.tz is None:
                start_tz = start_tz.tz_localize(merged.index.tz)
            elif merged.index.tz is None and start_tz.tz is not None:
                start_tz = start_tz.tz_localize(None)
            merged = merged[merged.index >= start_tz]
        if req.end is not None:
            # Ensure timezone consistency for comparison
            end_tz = req.end
            if merged.index.tz is not None and end_tz.tz is None:
                end_tz = end_tz.tz_localize(merged.index.tz)
            elif merged.index.tz is None and end_tz.tz is not None:
                end_tz = end_tz.tz_localize(None)
            merged = merged[merged.index <= end_tz]

        if kwargs.get("progress", None) is False:
            # yfinance default sorts already; ensure same behavior here.
            merged.sort_index(inplace=True)
        return merged

    def _load_from_cache(
        self,
        ticker: str,
        interval: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> Tuple[List[pd.DataFrame], List[date]]:
        frames: List[pd.DataFrame] = []
        missing: List[date] = []
        for day in _trading_days_inclusive(start, end):
            key = CacheKey(symbol=ticker, interval=interval, day=day)
            frame = self.cache.load(key)
            if frame is None:
                missing.append(day)
            else:
                frames.append(frame)
        return frames, missing

    def _fetch_and_store_missing(
        self,
        ticker: str,
        interval: str,
        missing_dates: List[date],
        downloads_kwargs: Dict[str, object],
    ) -> List[pd.DataFrame]:
        frames: List[pd.DataFrame] = []
        for start_day, end_day in _contiguous_ranges(missing_dates):
            fetch_start = pd.Timestamp(start_day)
            fetch_end = pd.Timestamp(end_day + timedelta(days=1))

            # Check if this is intraday data and if the date range exceeds Yahoo's limits
            is_intraday = any(interval.endswith(suffix) for suffix in ("m", "h"))
            if is_intraday:
                # Yahoo Finance has a ~30-day limit for intraday data
                days_requested = (end_day - start_day).days + 1
                cutoff_date = pd.Timestamp.now().normalize() - pd.Timedelta(days=30)

                if fetch_start.normalize() < cutoff_date:
                    # Skip dates that are too old for intraday data
                    continue

            try:
                fetched = yf.download(
                    ticker,
                    start=fetch_start,
                    end=fetch_end,
                    interval=interval,
                    auto_adjust=False,
                    **downloads_kwargs,
                )
                if fetched.empty:
                    continue
                frames.append(fetched)
                self._persist(ticker, interval, fetched)
            except Exception as e:
                # Log the error but continue with other date ranges
                error_msg = str(e)
                if "not available" in error_msg.lower() or "30 days" in error_msg:
                    # This is expected for old intraday data, skip silently
                    continue
                else:
                    # Re-raise unexpected errors
                    raise
        return frames

    def _persist(self, ticker: str, interval: str, frame: pd.DataFrame) -> None:
        if frame.empty:
            return
        index = frame.index
        if not isinstance(index, pd.DatetimeIndex):
            raise ValueError("Expected downloaded data to have a DatetimeIndex.")
        if index.tz is None:
            index_utc = index.tz_localize("UTC")
        else:
            index_utc = index.tz_convert("UTC")

        days = index_utc.normalize().unique()
        one_day = pd.Timedelta(days=1)

        for day in days:
            mask = (index_utc >= day) & (index_utc < day + one_day)
            day_frame = frame.loc[mask]
            if day_frame.empty:
                continue
            key = CacheKey(symbol=ticker, interval=interval, day=day.date())
            self.cache.store(key, day_frame)

    def get_options_expirations(
        self, ticker: str, use_cache: bool = True
    ) -> Tuple[str, ...]:
        """
        Get available option expiration dates for a ticker.

        Args:
            ticker: Stock symbol
            use_cache: Whether to use cached data if available

        Returns:
            Tuple of expiration date strings (YYYY-MM-DD format)
        """
        ticker = ticker.strip().upper()

        if use_cache:
            # Check if we have any cached option data
            cached_expirations = list(self.cache.iter_cached_option_expirations(ticker))
            if cached_expirations:
                # Filter out expired dates (keep current and future dates)
                from datetime import datetime

                today = datetime.now().date()
                valid_expirations = []
                for exp_str in cached_expirations:
                    try:
                        exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
                        if (
                            exp_date >= today
                        ):  # Keep current and future dates (>= includes today)
                            valid_expirations.append(exp_str)
                    except ValueError:
                        # Skip invalid date formats
                        continue

                # If we have valid cached expirations, return them
                if valid_expirations:
                    return tuple(sorted(valid_expirations))
                # If all cached expirations are expired, fall through to fetch fresh data

        # Fetch from yfinance
        yf_ticker = yf.Ticker(ticker)
        return yf_ticker.options

    def get_option_chain(
        self,
        ticker: str,
        expiration: Optional[str] = None,
        use_cache: bool = True,
        timestamp: Optional[str] = None,
    ) -> OptionChain:
        """
        Get option chain data for a ticker and expiration date.

        Args:
            ticker: Stock symbol
            expiration: Expiration date in YYYY-MM-DD format. If None, uses nearest expiration.
            use_cache: Whether to use cached data if available
            timestamp: Optional timestamp for historical data storage/retrieval. If None, generates current timestamp for new data.

        Returns:
            OptionChain with calls, puts DataFrames and underlying data
        """
        ticker = ticker.strip().upper()

        # Get expiration date
        if expiration is None:
            expirations = self.get_options_expirations(ticker, use_cache=use_cache)
            if not expirations:
                return OptionChain(
                    calls=pd.DataFrame(), puts=pd.DataFrame(), underlying={}
                )
            expiration = expirations[0]

        # Try to load from cache first
        if use_cache:
            calls_key = OptionCacheKey.for_calls(ticker, expiration, timestamp)
            puts_key = OptionCacheKey.for_puts(ticker, expiration, timestamp)
            underlying_key = OptionCacheKey.for_underlying(
                ticker, expiration, timestamp
            )

            if (
                self.cache.has_option_chain(calls_key)
                and self.cache.has_option_chain(puts_key)
                and self.cache.has_option_chain(underlying_key)
            ):

                calls = self.cache.load_option_chain(calls_key)
                puts = self.cache.load_option_chain(puts_key)
                underlying = self.cache.load_option_chain(underlying_key)

                if calls is not None and puts is not None and underlying is not None:
                    return OptionChain(calls=calls, puts=puts, underlying=underlying)

        # Fetch from yfinance
        yf_ticker = yf.Ticker(ticker)
        try:
            options = yf_ticker.option_chain(expiration)

            # Generate timestamp if not provided (for new data)
            if timestamp is None:
                timestamp = pd.Timestamp.now().isoformat()

            # Store in cache
            self.cache.store_option_chain(
                ticker,
                expiration,
                options.calls,
                options.puts,
                options.underlying,
                timestamp,
            )

            return OptionChain(
                calls=options.calls, puts=options.puts, underlying=options.underlying
            )

        except Exception as e:
            # Return empty option chain if fetch fails
            return OptionChain(calls=pd.DataFrame(), puts=pd.DataFrame(), underlying={})


def download(*args, **kwargs) -> pd.DataFrame:
    """
    Module-level convenience wrapper mirroring yfinance.download while leveraging the default cache.
    """
    client = CachedYFClient()
    return client.download(*args, **kwargs)


def get_options_expirations(ticker: str, use_cache: bool = True) -> Tuple[str, ...]:
    """
    Module-level convenience wrapper for getting option expiration dates.
    """
    client = CachedYFClient()
    return client.get_options_expirations(ticker, use_cache=use_cache)


def get_option_chain(
    ticker: str, expiration: Optional[str] = None, use_cache: bool = True
) -> OptionChain:
    """
    Module-level convenience wrapper for getting option chain data.
    """
    client = CachedYFClient()
    return client.get_option_chain(ticker, expiration=expiration, use_cache=use_cache)
