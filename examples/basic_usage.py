#!/usr/bin/env python3
"""
Basic usage example for cached-yfinance.

This example demonstrates the simplest way to use cached-yfinance
as a drop-in replacement for yfinance.download().
"""


import cached_yfinance as cyf


def main():
    """Demonstrate basic usage of cached-yfinance."""
    print("=== Basic Usage Example ===\n")

    # Example 1: Simple download (drop-in replacement for yfinance.download)
    print("1. Downloading Apple stock data for the last 30 days...")
    data = cyf.download("AAPL", period="30d")
    print(f"   Downloaded {len(data)} rows of data")
    print(f"   Date range: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"   Columns: {list(data.columns)}")
    print()

    # Example 2: Using specific date range
    print("2. Downloading Tesla data for a specific date range...")
    data = cyf.download("TSLA", start="2024-01-01", end="2024-01-31")
    print(f"   Downloaded {len(data)} rows of data")
    print(f"   Date range: {data.index[0].date()} to {data.index[-1].date()}")
    print()

    # Example 3: Intraday data
    print("3. Downloading Microsoft intraday data (1-hour intervals)...")
    data = cyf.download("MSFT", period="5d", interval="1h")
    print(f"   Downloaded {len(data)} rows of hourly data")
    print(f"   Date range: {data.index[0]} to {data.index[-1]}")
    print()

    # Example 4: Show caching benefit - second call should be much faster
    print("4. Demonstrating caching benefit...")
    print("   First call (may need to fetch from Yahoo Finance)...")
    import time

    start_time = time.time()
    data1 = cyf.download("GOOGL", period="7d")
    first_call_time = time.time() - start_time

    print("   Second call (should use cached data)...")
    start_time = time.time()
    data2 = cyf.download("GOOGL", period="7d")
    second_call_time = time.time() - start_time

    print(f"   First call took: {first_call_time:.2f} seconds")
    print(f"   Second call took: {second_call_time:.2f} seconds")
    print(f"   Speedup: {first_call_time / second_call_time:.1f}x faster")
    print(f"   Data identical: {data1.equals(data2)}")
    print()


if __name__ == "__main__":
    main()
