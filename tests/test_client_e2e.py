from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pandas as pd

from cached_yfinance import CachedYFClient, FileSystemCache, OptionCacheKey


def test_e2e_download_populates_filesystem_cache_then_serves_cache_hit(
    temp_cache_dir,
) -> None:
    cache = FileSystemCache(temp_cache_dir)
    client = CachedYFClient(cache)
    upstream_frame = pd.DataFrame(
        {
            "Open": [220.0, 221.0],
            "High": [224.0, 225.0],
            "Low": [219.0, 220.5],
            "Close": [223.5, 224.25],
            "Volume": [123456, 234567],
        },
        index=pd.to_datetime(["2026-08-24", "2026-08-25"]),
    )

    with patch("yfinance.download", return_value=upstream_frame) as yf_download:
        first_result = client.download(
            "iwm",
            start="2026-08-24",
            end="2026-08-25",
            progress=False,
        )

    assert yf_download.call_count == 1
    pd.testing.assert_frame_equal(first_result, upstream_frame)

    cached_files = sorted(temp_cache_dir.rglob("*"))
    assert temp_cache_dir / "IWM/1d/2026/08/2026-08-24-1d.parquet" in cached_files
    assert temp_cache_dir / "IWM/1d/2026/08/2026-08-24-1d.json" in cached_files
    assert temp_cache_dir / "IWM/1d/2026/08/2026-08-25-1d.parquet" in cached_files
    assert temp_cache_dir / "IWM/1d/2026/08/2026-08-25-1d.json" in cached_files

    with patch("yfinance.download") as yf_download:
        cached_result = client.download(
            "IWM",
            start="2026-08-24",
            end="2026-08-25",
            progress=False,
        )

    yf_download.assert_not_called()
    pd.testing.assert_frame_equal(cached_result, upstream_frame)


def test_e2e_option_chain_populates_filesystem_cache_then_reloads_by_timestamp(
    temp_cache_dir,
) -> None:
    cache = FileSystemCache(temp_cache_dir)
    client = CachedYFClient(cache)
    expiration = "2026-09-18"
    timestamp = "2026-08-27T14:30:00"
    calls = pd.DataFrame({"strike": [220.0, 225.0], "lastPrice": [6.1, 3.8]})
    puts = pd.DataFrame({"strike": [220.0, 225.0], "lastPrice": [2.4, 4.9]})
    underlying: dict[str, Any] = {"regularMarketPrice": 223.5, "currency": "USD"}
    option_response = Mock(calls=calls, puts=puts, underlying=underlying)
    ticker = Mock()
    ticker.option_chain.return_value = option_response

    with patch("yfinance.Ticker", return_value=ticker) as yf_ticker:
        first_chain = client.get_option_chain(
            " iwm ",
            expiration,
            use_cache=False,
            timestamp=timestamp,
        )

    yf_ticker.assert_called_once_with("IWM")
    ticker.option_chain.assert_called_once_with(expiration)
    pd.testing.assert_frame_equal(first_chain.calls, calls)
    pd.testing.assert_frame_equal(first_chain.puts, puts)
    assert first_chain.underlying == underlying

    assert cache.has_option_chain(
        OptionCacheKey.for_calls("IWM", expiration, timestamp)
    )
    assert cache.has_option_chain(OptionCacheKey.for_puts("IWM", expiration, timestamp))
    assert cache.has_option_chain(
        OptionCacheKey.for_underlying("IWM", expiration, timestamp)
    )

    with patch("yfinance.Ticker") as yf_ticker:
        cached_chain = client.get_option_chain(
            "IWM",
            expiration,
            use_cache=True,
            timestamp=timestamp,
        )

    yf_ticker.assert_not_called()
    pd.testing.assert_frame_equal(cached_chain.calls, calls)
    pd.testing.assert_frame_equal(cached_chain.puts, puts)
    assert cached_chain.underlying == underlying
    assert list(cache.iter_cached_option_expirations("IWM")) == [expiration]
    assert list(cache.iter_cached_option_timestamps("IWM", expiration)) == [timestamp]
