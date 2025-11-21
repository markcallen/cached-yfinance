#!/usr/bin/env python3
"""
Tool to download historical data for a specific ticker with configurable interval.

This tool uses the cached-yfinance library to efficiently download and cache
historical data for a given ticker symbol at various intervals. The data is automatically
cached to disk for faster subsequent access.

Usage:
    python download_data.py TICKER [--interval INTERVAL] [--days DAYS] [--cache-dir CACHE_DIR]

Examples:
    python download_data.py IWM --interval 1m --days 30
    python download_data.py AAPL --interval 1h --days 90
    python download_data.py TSLA --interval 1d --days 365
    python download_data.py MSFT --interval 5m --days 7 --cache-dir ~/my_cache
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path


# Add the parent directory to the path so we can import cached_yfinance
sys.path.insert(0, str(Path(__file__).parent.parent))

import cached_yfinance as cyf
from cached_yfinance import FileSystemCache


def download_data(
    ticker: str, interval: str = "1d", days: int = 60, cache_dir: str = None
) -> None:
    """
    Download historical data for a ticker going back the specified number of days.

    Args:
        ticker: Stock ticker symbol (e.g., 'IWM', 'AAPL')
        interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        days: Number of days to go back (default: 60)
        cache_dir: Custom cache directory path (optional)

    Raises:
        ValueError: If days > 60 for intraday intervals (intervals ending with 'm' or 'h')
    """
    # Check if this is an intraday interval (ends with 'm' or 'h')
    is_intraday = any(interval.endswith(suffix) for suffix in ("m", "h"))

    # Validate days for intraday intervals
    if is_intraday and days > 60:
        raise ValueError(
            f"❌ Error: Days cannot exceed 60 for intraday intervals. Got {days} days for interval '{interval}'."
        )

    # Yahoo Finance limits intraday data to approximately 30 days
    if is_intraday and days > 30:
        max_days_for_intraday = 29  # Be conservative to avoid edge cases
        print(
            f"⚠️  Warning: Yahoo Finance limits intraday data to ~30 days. Adjusting from {days} to {max_days_for_intraday} days."
        )
        days = max_days_for_intraday

    print(f"📈 Downloading {days}-day {interval} data for {ticker.upper()}...")

    # Initialize cache
    if cache_dir:
        cache = FileSystemCache(cache_dir)
        client = cyf.CachedYFClient(cache)
        print(f"📁 Using custom cache directory: {cache_dir}")
    else:
        client = cyf.CachedYFClient()
        print("📁 Using default cache directory: ~/.cache/yfinance")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(
        f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    try:
        # Download the data
        data = client.download(
            ticker.upper(),
            start=start_date,
            end=end_date,
            interval=interval,
            progress=True,
        )

        if data.empty:
            print(f"⚠️  No data found for {ticker.upper()}")
            return

        # Display summary statistics
        print(f"\n✅ Successfully downloaded data for {ticker.upper()}")
        print(f"📊 Data points: {len(data):,}")
        print(
            f"📅 Date range: {data.index[0].strftime('%Y-%m-%d %H:%M')} to {data.index[-1].strftime('%Y-%m-%d %H:%M')}"
        )
        print(
            f"💰 Price range: ${data['Low'].min().item():.2f} - ${data['High'].max().item():.2f}"
        )
        print(f"📈 Latest close: ${data['Close'].iloc[-1].item():.2f}")

        # Show recent data sample
        print("\n📋 Last 5 data points:")
        print(data.tail().round(2))

        # Cache statistics
        if hasattr(client.cache, "root"):
            cache_path = client.cache.root / ticker.upper() / interval
            if cache_path.exists():
                cache_files = list(cache_path.rglob("*.parquet"))
                print("\n💾 Cache info:")
                print(f"   Location: {cache_path}")
                print(f"   Files: {len(cache_files)} parquet files")

    except Exception as e:
        print(f"❌ Error downloading data for {ticker.upper()}: {e}")
        sys.exit(1)


def main():
    """Main entry point for the command-line tool."""
    parser = argparse.ArgumentParser(
        description="Download historical data for a ticker with configurable interval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s IWM                                    # Download 60 days of daily IWM data
  %(prog)s AAPL --interval 1m --days 30          # Download 30 days of 1-minute AAPL data
  %(prog)s TSLA --interval 1h --days 90          # Download 90 days of hourly TSLA data
  %(prog)s MSFT --interval 1d --days 365         # Download 365 days of daily MSFT data
  %(prog)s GOOGL --cache-dir ~/my_cache          # Use custom cache directory
        """,
    )

    parser.add_argument("ticker", help="Stock ticker symbol (e.g., IWM, AAPL, TSLA)")

    parser.add_argument(
        "--interval",
        default="1d",
        help="Data interval: 1m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo, 3mo (default: 1d)",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=60,
        help="Number of days to go back (default: 60, max 60 for intraday intervals)",
    )

    parser.add_argument(
        "--cache-dir", help="Custom cache directory path (default: ~/.cache/yfinance)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s 1.0.0 (cached-yfinance {cyf.__version__})",
    )

    args = parser.parse_args()

    # Validate ticker
    if not args.ticker or not args.ticker.strip():
        print("❌ Error: Ticker symbol cannot be empty")
        sys.exit(1)

    # Validate interval
    valid_intervals = ["1m", "5m", "15m", "30m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    if args.interval not in valid_intervals:
        print(
            f"❌ Error: Invalid interval '{args.interval}'. Valid intervals: {', '.join(valid_intervals)}"
        )
        sys.exit(1)

    # Validate days
    if args.days <= 0:
        print("❌ Error: Number of days must be positive")
        sys.exit(1)

    # Check intraday interval limits
    is_intraday = any(args.interval.endswith(suffix) for suffix in ("m", "h"))
    if is_intraday and args.days > 60:
        print(
            f"❌ Error: Days cannot exceed 60 for intraday intervals. Got {args.days} days for interval '{args.interval}'."
        )
        sys.exit(1)

    if is_intraday and args.days > 30:
        print(
            "⚠️  Warning: Yahoo Finance limits intraday data to ~30 days. Data may be incomplete for older dates."
        )

    # Run the download
    try:
        download_data(args.ticker, args.interval, args.days, args.cache_dir)
    except ValueError as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
