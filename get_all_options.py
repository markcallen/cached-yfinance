#!/usr/bin/env python3
"""
Get All Options Data Script

This script provides functionality to:
1. Get a list of upcoming expiration dates for options
2. Download options data for all available expiration dates

Usage:
    python get_all_options.py TICKER [--list-only] [--cache-dir PATH]

Examples:
    python get_all_options.py AAPL                    # Download all AAPL options
    python get_all_options.py TSLA --list-only        # Just list TSLA expirations
    python get_all_options.py MSFT --cache-dir /tmp   # Custom cache directory
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


# Add the current directory to the path so we can import cached_yfinance
sys.path.insert(0, str(Path(__file__).parent))

import cached_yfinance as cyf
from cached_yfinance import FileSystemCache


def get_upcoming_expirations(
    ticker: str, client: cyf.CachedYFClient, days_ahead: int = 365
) -> List[Tuple[str, int]]:
    """
    Get upcoming expiration dates for options.

    Args:
        ticker: Stock ticker symbol
        client: CachedYFClient instance
        days_ahead: Only include expirations within this many days (default: 365)

    Returns:
        List of tuples (expiration_date, days_until_expiration)
    """
    print(f"📅 Getting upcoming expiration dates for {ticker.upper()}...")

    try:
        # Get all available expiration dates (try cache first, then fresh if needed)
        all_expirations = client.get_options_expirations(ticker.upper(), use_cache=True)

        # If no expirations found or all are expired, try fresh fetch
        if not all_expirations:
            print("   No cached expirations found, fetching fresh data...")
            all_expirations = client.get_options_expirations(
                ticker.upper(), use_cache=False
            )

        if not all_expirations:
            print(f"⚠️  No expiration dates found for {ticker.upper()}")
            return []

        # Filter for upcoming expirations only
        upcoming = []
        current_date = (
            datetime.now().date()
        )  # Use date() to compare dates only, not time

        for exp_str in all_expirations:
            try:
                exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
                days_until = (exp_date - current_date).days

                # Include current day (0) and future expirations within the specified range
                if 0 <= days_until <= days_ahead:
                    upcoming.append((exp_str, days_until))

            except ValueError:
                # Skip invalid date formats
                continue

        # Sort by days until expiration
        upcoming.sort(key=lambda x: x[1])

        return upcoming

    except Exception as e:
        print(f"❌ Error getting expiration dates for {ticker.upper()}: {e}")
        return []


def display_expirations(expirations: List[Tuple[str, int]], ticker: str) -> None:
    """Display expiration dates in a formatted table."""
    if not expirations:
        print(f"⚠️  No upcoming expiration dates found for {ticker.upper()}")
        return

    print(
        f"\n📊 Found {len(expirations)} upcoming expiration dates for {ticker.upper()}:"
    )
    print("-" * 60)
    print(f"{'#':<3} {'Expiration':<12} {'Days Until':<12} {'Status'}")
    print("-" * 60)

    for i, (exp_date, days_until) in enumerate(expirations, 1):
        if days_until == 0:
            status = "Expires today!"
        elif days_until == 1:
            status = "Expires tomorrow"
        elif days_until <= 7:
            status = "This week"
        elif days_until <= 30:
            status = "This month"
        elif days_until <= 90:
            status = "Next 3 months"
        else:
            status = "Long term"

        print(f"{i:<3} {exp_date:<12} {days_until:<12} {status}")


def download_all_options_data(
    ticker: str, client: cyf.CachedYFClient, expirations: List[Tuple[str, int]]
) -> dict:
    """
    Download options data for all expiration dates.

    Args:
        ticker: Stock ticker symbol
        client: CachedYFClient instance
        expirations: List of (expiration_date, days_until) tuples

    Returns:
        Dictionary with download statistics
    """
    if not expirations:
        print(f"⚠️  No expirations to download for {ticker.upper()}")
        return {"total": 0, "successful": 0, "failed": 0}

    print(
        f"\n🚀 Starting download of options data for {len(expirations)} expirations..."
    )
    print("=" * 70)

    stats = {
        "total": len(expirations),
        "successful": 0,
        "failed": 0,
        "total_calls": 0,
        "total_puts": 0,
    }

    for i, (expiration, days_until) in enumerate(expirations, 1):
        print(
            f"\n📈 [{i}/{len(expirations)}] Processing {expiration} ({days_until} days until expiration)"
        )

        try:
            # Download option chain data
            option_chain = client.get_option_chain(
                ticker.upper(), expiration, use_cache=False
            )

            if option_chain.calls.empty and option_chain.puts.empty:
                print(f"   ⚠️  No options data available for {expiration}")
                stats["failed"] += 1
                continue

            # Count contracts
            calls_count = len(option_chain.calls)
            puts_count = len(option_chain.puts)

            stats["successful"] += 1
            stats["total_calls"] += calls_count
            stats["total_puts"] += puts_count

            # Get underlying price for context
            underlying_price = option_chain.underlying.get("regularMarketPrice", "N/A")

            print(f"   ✅ Downloaded: {calls_count} calls, {puts_count} puts")
            print(f"   📊 Underlying price: ${underlying_price}")

            # Show some sample strikes for context
            if not option_chain.calls.empty:
                strikes = sorted(option_chain.calls["strike"].unique())
                sample_strikes = (
                    strikes[:3] + ["..."] + strikes[-3:]
                    if len(strikes) > 6
                    else strikes
                )
                print(f"   🎯 Strike range: {sample_strikes}")

        except Exception as e:
            print(f"   ❌ Error downloading {expiration}: {e}")
            stats["failed"] += 1
            continue

    return stats


def print_summary(stats: dict, ticker: str) -> None:
    """Print download summary statistics."""
    print("\n" + "=" * 70)
    print(f"📊 DOWNLOAD SUMMARY for {ticker.upper()}")
    print("=" * 70)
    print(f"Total expirations processed: {stats['total']}")
    print(f"Successful downloads: {stats['successful']}")
    print(f"Failed downloads: {stats['failed']}")
    print(f"Total call contracts: {stats['total_calls']:,}")
    print(f"Total put contracts: {stats['total_puts']:,}")
    print(f"Total contracts: {stats['total_calls'] + stats['total_puts']:,}")

    if stats["total"] > 0:
        success_rate = (stats["successful"] / stats["total"]) * 100
        print(f"Success rate: {success_rate:.1f}%")

    print("\n💾 Data has been cached and is ready for analysis!")
    print("💡 Use the cached_yfinance library to access the downloaded data.")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Get upcoming option expiration dates and download all options data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s AAPL                    # Download all AAPL options
  %(prog)s TSLA --list-only        # Just list TSLA expirations  
  %(prog)s MSFT --cache-dir /tmp   # Use custom cache directory
  %(prog)s SPY --days-ahead 90     # Only expirations in next 90 days
        """,
    )

    parser.add_argument("ticker", help="Stock ticker symbol (e.g., AAPL, TSLA, SPY)")

    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list expiration dates, don't download data",
    )

    parser.add_argument(
        "--cache-dir",
        type=str,
        help="Custom cache directory path (default: ~/.cache/yfinance)",
    )

    parser.add_argument(
        "--days-ahead",
        type=int,
        default=365,
        help="Only include expirations within this many days (default: 365)",
    )

    args = parser.parse_args()

    # Validate ticker
    if not args.ticker or not args.ticker.strip():
        print("❌ Error: Ticker symbol cannot be empty")
        sys.exit(1)

    ticker = args.ticker.strip().upper()

    # Initialize cache and client
    if args.cache_dir:
        cache = FileSystemCache(args.cache_dir)
        client = cyf.CachedYFClient(cache)
        print(f"📁 Using custom cache directory: {args.cache_dir}")
    else:
        client = cyf.CachedYFClient()
        print("📁 Using default cache directory: ~/.cache/yfinance")

    print(f"🎯 Target ticker: {ticker}")
    print(f"📅 Looking ahead: {args.days_ahead} days")

    # Get upcoming expiration dates
    expirations = get_upcoming_expirations(ticker, client, args.days_ahead)

    # Display the expirations
    display_expirations(expirations, ticker)

    # If list-only mode, stop here
    if args.list_only:
        print(f"\n✅ Listed {len(expirations)} upcoming expirations for {ticker}")
        return

    # Download all options data
    if expirations:
        stats = download_all_options_data(ticker, client, expirations)
        print_summary(stats, ticker)
    else:
        print(f"\n⚠️  No upcoming expirations found for {ticker} - nothing to download")


if __name__ == "__main__":
    main()
