#!/usr/bin/env python3
"""
Tool to download 1-minute data for a specific ticker going back 60 days.

This tool uses the cached-yfinance library to efficiently download and cache
1-minute historical data for a given ticker symbol. The data is automatically
cached to disk for faster subsequent access.

Usage:
    python download_1m_data.py TICKER [--days DAYS] [--cache-dir CACHE_DIR]

Examples:
    python download_1m_data.py IWM
    python download_1m_data.py AAPL --days 30
    python download_1m_data.py TSLA --cache-dir ~/my_cache
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path so we can import cached_yfinance
sys.path.insert(0, str(Path(__file__).parent.parent))

import cached_yfinance as cyf
from cached_yfinance import FileSystemCache


def download_1m_data(ticker: str, days: int = 60, cache_dir: str = None) -> None:
    """
    Download 1-minute data for a ticker going back the specified number of days.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'IWM', 'AAPL')
        days: Number of days to go back (default: 60, but limited by Yahoo's ~30-day restriction)
        cache_dir: Custom cache directory path (optional)
    """
    # Yahoo Finance limits 1-minute data to approximately 30 days
    max_days_for_1m = 29  # Be conservative to avoid edge cases
    if days > max_days_for_1m:
        print(f"⚠️  Warning: Yahoo Finance limits 1-minute data to ~30 days. Adjusting from {days} to {max_days_for_1m} days.")
        days = max_days_for_1m
    
    print(f"📈 Downloading {days}-day 1-minute data for {ticker.upper()}...")
    
    # Initialize cache
    if cache_dir:
        cache = FileSystemCache(cache_dir)
        client = cyf.CachedYFClient(cache)
        print(f"📁 Using custom cache directory: {cache_dir}")
    else:
        client = cyf.CachedYFClient()
        print(f"📁 Using default cache directory: ~/.cache/yfinance")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        # Download the data
        data = client.download(
            ticker.upper(),
            start=start_date,
            end=end_date,
            interval="1m",
            progress=True
        )
        
        if data.empty:
            print(f"⚠️  No data found for {ticker.upper()}")
            return
        
        # Display summary statistics
        print(f"\n✅ Successfully downloaded data for {ticker.upper()}")
        print(f"📊 Data points: {len(data):,}")
        print(f"📅 Date range: {data.index[0].strftime('%Y-%m-%d %H:%M')} to {data.index[-1].strftime('%Y-%m-%d %H:%M')}")
        print(f"💰 Price range: ${data['Low'].min().item():.2f} - ${data['High'].max().item():.2f}")
        print(f"📈 Latest close: ${data['Close'].iloc[-1].item():.2f}")
        
        # Show recent data sample
        print(f"\n📋 Last 5 data points:")
        print(data.tail().round(2))
        
        # Cache statistics
        if hasattr(client.cache, 'root'):
            cache_path = client.cache.root / ticker.upper() / "1m"
            if cache_path.exists():
                cache_files = list(cache_path.rglob("*.parquet"))
                print(f"\n💾 Cache info:")
                print(f"   Location: {cache_path}")
                print(f"   Files: {len(cache_files)} parquet files")
        
    except Exception as e:
        print(f"❌ Error downloading data for {ticker.upper()}: {e}")
        sys.exit(1)


def main():
    """Main entry point for the command-line tool."""
    parser = argparse.ArgumentParser(
        description="Download 1-minute data for a ticker (limited to ~30 days by Yahoo Finance)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s IWM                           # Download 29 days of IWM data
  %(prog)s AAPL --days 20               # Download 20 days of AAPL data
  %(prog)s TSLA --cache-dir ~/my_cache  # Use custom cache directory
        """
    )
    
    parser.add_argument(
        "ticker",
        help="Stock ticker symbol (e.g., IWM, AAPL, TSLA)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=29,
        help="Number of days to go back (default: 29, max ~30 due to Yahoo Finance limits for 1m data)"
    )
    
    parser.add_argument(
        "--cache-dir",
        help="Custom cache directory path (default: ~/.cache/yfinance)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s 1.0.0 (cached-yfinance {cyf.__version__})"
    )
    
    args = parser.parse_args()
    
    # Validate ticker
    if not args.ticker or not args.ticker.strip():
        print("❌ Error: Ticker symbol cannot be empty")
        sys.exit(1)
    
    # Validate days
    if args.days <= 0:
        print("❌ Error: Number of days must be positive")
        sys.exit(1)
    
    if args.days > 30:
        print("⚠️  Warning: Yahoo Finance limits 1-minute data to ~30 days. Data may be incomplete for older dates.")
    
    # Run the download
    download_1m_data(args.ticker, args.days, args.cache_dir)


if __name__ == "__main__":
    main()
