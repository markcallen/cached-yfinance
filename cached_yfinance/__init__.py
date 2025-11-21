"""
Cached YFinance - A caching wrapper around yfinance for improved performance.

This package provides a drop-in replacement for yfinance.download() that caches
historical data to disk, significantly improving performance for repeated requests.
"""

from .cache import CacheKey, FileSystemCache, OptionCacheKey
from .client import (
    CachedYFClient,
    OptionChain,
    download,
    get_option_chain,
    get_options_expirations,
)


__version__ = "0.1.0"
__all__ = [
    "CacheKey",
    "FileSystemCache",
    "OptionCacheKey",
    "CachedYFClient",
    "download",
    "get_options_expirations",
    "get_option_chain",
    "OptionChain",
]
