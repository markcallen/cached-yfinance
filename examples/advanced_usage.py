#!/usr/bin/env python3
"""
Advanced usage example for cached-yfinance.

This example demonstrates more advanced features including:
- Custom cache configuration
- Using the CachedYFClient class directly
- Cache inspection and management
"""

from pathlib import Path

from cached_yfinance import CachedYFClient, FileSystemCache


def main():
    """Demonstrate advanced usage of cached-yfinance."""
    print("=== Advanced Usage Example ===\n")

    # Example 1: Custom cache location
    print("1. Using a custom cache location...")
    custom_cache_dir = Path.home() / "my_finance_cache"
    cache = FileSystemCache(custom_cache_dir)
    client = CachedYFClient(cache)

    data = client.download("AAPL", period="5d")
    print(f"   Downloaded {len(data)} rows to custom cache at: {custom_cache_dir}")
    print(f"   Cache directory exists: {custom_cache_dir.exists()}")
    print()

    # Example 2: Inspecting cached data
    print("2. Inspecting cached data...")
    cached_days = list(cache.iter_cached_days("AAPL", "1d"))
    print(f"   Cached days for AAPL (1d interval): {len(cached_days)} days")
    if cached_days:
        print(f"   First cached day: {cached_days[0]}")
        print(f"   Last cached day: {cached_days[-1]}")
    print()

    # Example 3: Multiple intervals for the same symbol
    print("3. Caching multiple intervals for the same symbol...")
    symbols = ["MSFT"]
    intervals = ["1d", "1h", "5m"]

    for symbol in symbols:
        for interval in intervals:
            print(f"   Downloading {symbol} with {interval} interval...")
            try:
                data = client.download(symbol, period="2d", interval=interval)
                cached_days = list(cache.iter_cached_days(symbol, interval))
                print(f"     Cached {len(cached_days)} days for {symbol} ({interval})")
            except Exception as e:
                print(f"     Error with {interval}: {e}")
    print()

    # Example 4: Cache key usage
    print("4. Working with cache keys...")
    from datetime import date

    from cached_yfinance import CacheKey

    # Create a cache key for a specific day
    key = CacheKey(symbol="AAPL", interval="1d", day=date.today())
    print(f"   Cache key: {key}")
    print(f"   Cache has this key: {cache.has(key)}")

    if cache.has(key):
        cached_data = cache.load(key)
        if cached_data is not None:
            print(f"   Cached data shape: {cached_data.shape}")
    print()

    # Example 5: Performance comparison with different cache sizes
    print("5. Performance comparison...")
    import time

    # Test with a symbol that likely has some cached data
    test_symbol = "SPY"
    test_period = "10d"

    print(f"   Testing performance for {test_symbol} over {test_period}...")

    # Time the cached version
    start_time = time.time()
    cached_data = client.download(test_symbol, period=test_period)
    cached_time = time.time() - start_time

    print(f"   Cached download took: {cached_time:.3f} seconds")
    print(f"   Retrieved {len(cached_data)} rows")
    print()

    # Example 6: Cache statistics
    print("6. Cache statistics...")
    cache_root = cache.root
    if cache_root.exists():
        total_files = sum(1 for _ in cache_root.rglob("*.parquet"))
        total_size = sum(f.stat().st_size for f in cache_root.rglob("*.parquet"))
        print(f"   Cache location: {cache_root}")
        print(f"   Total cached files: {total_files}")
        print(f"   Total cache size: {total_size / 1024 / 1024:.2f} MB")

        # Show cached symbols
        symbols_cached = set()
        for symbol_dir in cache_root.iterdir():
            if symbol_dir.is_dir():
                symbols_cached.add(symbol_dir.name)
        print(f"   Cached symbols: {sorted(symbols_cached)}")
    print()


if __name__ == "__main__":
    main()
