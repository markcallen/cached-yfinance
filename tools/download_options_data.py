#!/usr/bin/env python3
"""
Tool to download option chain data for a specific ticker.

This tool uses the cached-yfinance library to efficiently download and cache
option chain data for a given ticker symbol. The data is automatically
cached to disk for faster subsequent access.

Usage:
    python download_options_data.py TICKER [--expiration EXPIRATION] [--cache-dir CACHE_DIR] [--all-expirations]

Examples:
    python download_options_data.py AAPL                           # Download nearest expiration (with timestamp)
    python download_options_data.py AAPL --expiration 2024-01-19  # Download specific expiration (with timestamp)
    python download_options_data.py TSLA --all-expirations        # Download all available expirations (with timestamps)
    python download_options_data.py IWM --cache-dir ~/my_cache    # Use custom cache directory

Note: All downloads automatically include timestamps for historical data tracking.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


# Add the parent directory to the path so we can import cached_yfinance
sys.path.insert(0, str(Path(__file__).parent.parent))

import cached_yfinance as cyf
from cached_yfinance import FileSystemCache


def download_option_chain(
    ticker: str, expiration: Optional[str] = None, cache_dir: str = None
) -> None:
    """
    Download option chain data for a ticker and expiration date.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        expiration: Specific expiration date in YYYY-MM-DD format (optional)
        cache_dir: Custom cache directory path (optional)

    Note: Timestamps are automatically included in filenames for historical tracking.
    """
    print(f"📊 Downloading option chain data for {ticker.upper()}...")

    # Initialize cache
    if cache_dir:
        cache = FileSystemCache(cache_dir)
        client = cyf.CachedYFClient(cache)
        print(f"📁 Using custom cache directory: {cache_dir}")
    else:
        client = cyf.CachedYFClient()
        print("📁 Using default cache directory: ~/.cache/yfinance")

    try:
        # Get option chain data (timestamps are automatically generated)
        option_chain = client.get_option_chain(ticker.upper(), expiration=expiration)

        if option_chain.calls.empty and option_chain.puts.empty:
            print(f"⚠️  No option data found for {ticker.upper()}")
            if expiration:
                print(f"   Expiration: {expiration}")
            return

        # Display summary statistics
        print(f"\n✅ Successfully downloaded option chain for {ticker.upper()}")
        if expiration:
            print(f"📅 Expiration: {expiration}")
        print(f"🕒 Timestamp: {pd.Timestamp.now().isoformat()}")

        # Underlying stock info
        underlying_price = option_chain.underlying.get("regularMarketPrice")
        if underlying_price:
            print(f"💰 Underlying price: ${underlying_price:.2f}")

        # Calls summary
        if not option_chain.calls.empty:
            calls_df = option_chain.calls
            print(f"\n📈 Call Options: {len(calls_df):,} contracts")
            print(
                f"   Strike range: ${calls_df['strike'].min():.2f} - ${calls_df['strike'].max():.2f}"
            )

            # Active calls (with volume > 0)
            active_calls = calls_df[calls_df["volume"] > 0]
            if not active_calls.empty:
                print(f"   Active contracts: {len(active_calls):,} (with volume > 0)")
                print(f"   Total volume: {active_calls['volume'].sum():,}")
                print(f"   Total open interest: {active_calls['openInterest'].sum():,}")

                # Show top 5 by volume
                print("\n📋 Top 5 calls by volume:")
                top_calls = active_calls.nlargest(5, "volume")[
                    [
                        "strike",
                        "lastPrice",
                        "bid",
                        "ask",
                        "volume",
                        "openInterest",
                        "impliedVolatility",
                    ]
                ]
                print(top_calls.round(4))

        # Puts summary
        if not option_chain.puts.empty:
            puts_df = option_chain.puts
            print(f"\n📉 Put Options: {len(puts_df):,} contracts")
            print(
                f"   Strike range: ${puts_df['strike'].min():.2f} - ${puts_df['strike'].max():.2f}"
            )

            # Active puts (with volume > 0)
            active_puts = puts_df[puts_df["volume"] > 0]
            if not active_puts.empty:
                print(f"   Active contracts: {len(active_puts):,} (with volume > 0)")
                print(f"   Total volume: {active_puts['volume'].sum():,}")
                print(f"   Total open interest: {active_puts['openInterest'].sum():,}")

                # Show top 5 by volume
                print("\n📋 Top 5 puts by volume:")
                top_puts = active_puts.nlargest(5, "volume")[
                    [
                        "strike",
                        "lastPrice",
                        "bid",
                        "ask",
                        "volume",
                        "openInterest",
                        "impliedVolatility",
                    ]
                ]
                print(top_puts.round(4))

        # At-the-money analysis
        if (
            underlying_price
            and not option_chain.calls.empty
            and not option_chain.puts.empty
        ):
            print(
                f"\n🎯 At-the-Money Analysis (current price: ${underlying_price:.2f}):"
            )

            # Find closest strikes to current price
            calls_df = option_chain.calls.copy()
            puts_df = option_chain.puts.copy()

            calls_df["distance_from_atm"] = abs(calls_df["strike"] - underlying_price)
            puts_df["distance_from_atm"] = abs(puts_df["strike"] - underlying_price)

            if not calls_df.empty:
                atm_call = calls_df.loc[calls_df["distance_from_atm"].idxmin()]
                print(
                    f"   ATM Call (${atm_call['strike']:.2f}): ${atm_call['lastPrice']:.2f}, IV: {atm_call['impliedVolatility']:.4f}"
                )

            if not puts_df.empty:
                atm_put = puts_df.loc[puts_df["distance_from_atm"].idxmin()]
                print(
                    f"   ATM Put (${atm_put['strike']:.2f}): ${atm_put['lastPrice']:.2f}, IV: {atm_put['impliedVolatility']:.4f}"
                )

        # Cache statistics
        if hasattr(client.cache, "root"):
            cache_path = client.cache.root / ticker.upper() / "options"
            if cache_path.exists():
                cache_files = list(cache_path.rglob("*.parquet"))
                print("\n💾 Cache info:")
                print(f"   Location: {cache_path}")
                print(f"   Files: {len(cache_files)} parquet files")

    except Exception as e:
        print(f"❌ Error downloading option data for {ticker.upper()}: {e}")
        sys.exit(1)


def download_all_expirations(ticker: str, cache_dir: str = None) -> None:
    """
    Download option chain data for all available expiration dates using direct yfinance approach.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        cache_dir: Custom cache directory path (optional)

    Note: Timestamps are automatically included in filenames for historical tracking.
    """
    print(f"📊 Downloading ALL option expirations for {ticker.upper()}...")

    # Initialize cache
    if cache_dir:
        cache = FileSystemCache(cache_dir)
        client = cyf.CachedYFClient(cache)
        print(f"📁 Using custom cache directory: {cache_dir}")
    else:
        client = cyf.CachedYFClient()
        print("📁 Using default cache directory: ~/.cache/yfinance")

    try:
        # Get all available expiration dates directly from yfinance
        import yfinance as yf

        yf_ticker = yf.Ticker(ticker.upper())
        expirations = yf_ticker.options

        if not expirations:
            print(f"⚠️  No expiration dates found for {ticker.upper()}")
            return

        print(
            f"📅 Found {len(expirations)} expiration dates: {expirations[:5]}{'...' if len(expirations) > 5 else ''}"
        )

        total_calls = 0
        total_puts = 0
        successful_downloads = 0

        for i, expiry in enumerate(expirations, 1):
            print(f"\n[{i}/{len(expirations)}] Processing expiration: {expiry}")

            try:
                # Get option chain directly from yfinance
                option_chain = yf_ticker.option_chain(expiry)
                calls = option_chain.calls
                puts = option_chain.puts

                calls_count = len(calls) if not calls.empty else 0
                puts_count = len(puts) if not puts.empty else 0

                if calls_count > 0 or puts_count > 0:
                    print(f"   ✅ Calls: {calls_count:,}, Puts: {puts_count:,}")

                    # Store in cache using the client's cache system
                    timestamp = pd.Timestamp.now().isoformat()
                    underlying = getattr(option_chain, "underlying", {})
                    client.cache.store_option_chain(
                        ticker.upper(), expiry, calls, puts, underlying, timestamp
                    )

                    total_calls += calls_count
                    total_puts += puts_count
                    successful_downloads += 1
                else:
                    print("   ⚠️  No data available")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        # Summary
        print("\n🎉 Download Summary:")
        print(f"   Successful expirations: {successful_downloads}/{len(expirations)}")
        print(f"   Total call contracts: {total_calls:,}")
        print(f"   Total put contracts: {total_puts:,}")
        print(f"   Total contracts: {total_calls + total_puts:,}")

        # Cache statistics
        if hasattr(client.cache, "root"):
            cache_path = client.cache.root / ticker.upper() / "options"
            if cache_path.exists():
                cache_files = list(cache_path.rglob("*.parquet"))
                print("\n💾 Cache info:")
                print(f"   Location: {cache_path}")
                print(f"   Files: {len(cache_files)} parquet files")

    except Exception as e:
        print(f"❌ Error downloading option data for {ticker.upper()}: {e}")
        sys.exit(1)


def list_expirations(ticker: str, cache_dir: str = None) -> None:
    """
    List all available expiration dates for a ticker using direct yfinance approach.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        cache_dir: Custom cache directory path (optional)
    """
    print(f"📅 Available expiration dates for {ticker.upper()}:")

    try:
        # Get expiration dates directly from yfinance (raw ticker.options result)
        import yfinance as yf

        yf_ticker = yf.Ticker(ticker.upper())
        expirations = yf_ticker.options

        if not expirations:
            print(f"⚠️  No expiration dates found for {ticker.upper()}")
            return

        print(
            f"\nFound {len(expirations)} expiration dates (raw ticker.options result):"
        )
        for i, exp in enumerate(expirations, 1):
            # Calculate days until expiration
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d")
                days_until = (exp_date - datetime.now()).days
                if days_until < 0:
                    status = f"expired ({abs(days_until)} days ago)"
                elif days_until == 0:
                    status = "expires today"
                else:
                    status = f"{days_until} days"
            except:
                status = "unknown"

            print(f"  {i:2d}. {exp} ({status})")

    except Exception as e:
        print(f"❌ Error getting expiration dates for {ticker.upper()}: {e}")
        sys.exit(1)


def main():
    """Main entry point for the command-line tool."""
    parser = argparse.ArgumentParser(
        description="Download option chain data for a ticker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s AAPL                           # Download nearest expiration (with timestamp)
  %(prog)s AAPL --expiration 2024-01-19  # Download specific expiration (with timestamp)
  %(prog)s TSLA --all-expirations        # Download all available expirations (with timestamps)
  %(prog)s IWM --list-expirations        # List available expiration dates
  %(prog)s AAPL --cache-dir ~/my_cache   # Use custom cache directory

All downloads automatically include timestamps for historical data tracking.
        """,
    )

    parser.add_argument("ticker", help="Stock ticker symbol (e.g., AAPL, TSLA, IWM)")

    parser.add_argument(
        "--expiration",
        help="Specific expiration date in YYYY-MM-DD format (default: nearest expiration)",
    )

    parser.add_argument(
        "--all-expirations",
        action="store_true",
        help="Download option chains for all available expiration dates",
    )

    parser.add_argument(
        "--list-expirations",
        action="store_true",
        help="List all available expiration dates (no download)",
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

    # Validate expiration format if provided
    if args.expiration:
        try:
            datetime.strptime(args.expiration, "%Y-%m-%d")
        except ValueError:
            print("❌ Error: Expiration date must be in YYYY-MM-DD format")
            sys.exit(1)

    # Check for conflicting options
    if args.all_expirations and args.expiration:
        print("❌ Error: Cannot specify both --expiration and --all-expirations")
        sys.exit(1)

    if args.list_expirations and (args.expiration or args.all_expirations):
        print("❌ Error: --list-expirations cannot be used with other download options")
        sys.exit(1)

    # Execute the appropriate action
    if args.list_expirations:
        list_expirations(args.ticker, args.cache_dir)
    elif args.all_expirations:
        download_all_expirations(args.ticker, args.cache_dir)
    else:
        download_option_chain(args.ticker, args.expiration, args.cache_dir)


if __name__ == "__main__":
    main()
