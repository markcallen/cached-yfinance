#!/usr/bin/env python3
"""
Historical Options Analysis Example

This example demonstrates how to work with historical options data
collected using the timestamped storage feature.

Usage:
    python historical_options_analysis.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# Add the parent directory to the path so we can import cached_yfinance
sys.path.insert(0, str(Path(__file__).parent.parent))

import cached_yfinance as cyf


def analyze_historical_options(ticker: str = "AAPL", expiration: str = None):
    """
    Analyze historical options data for a ticker.

    Args:
        ticker: Stock ticker symbol
        expiration: Options expiration date (YYYY-MM-DD format)
    """
    print(f"🔍 Analyzing historical options data for {ticker}")
    print("=" * 50)

    # Initialize client
    client = cyf.CachedYFClient()

    # Get available expirations if not specified
    if expiration is None:
        expirations = client.get_options_expirations(ticker)
        if not expirations:
            print(f"❌ No options data found for {ticker}")
            return
        expiration = expirations[0]  # Use nearest expiration
        print(f"📅 Using nearest expiration: {expiration}")

    # Get available historical timestamps
    timestamps = list(client.cache.iter_cached_option_timestamps(ticker, expiration))

    if not timestamps:
        print(f"⚠️  No historical data found for {ticker} {expiration}")
        print(
            "   Try running the market_hours_collector.py first to collect historical data"
        )
        return

    print(f"📊 Found {len(timestamps)} historical snapshots")
    print(f"   Date range: {min(timestamps)[:10]} to {max(timestamps)[:10]}")
    print()

    # Analyze data over time
    historical_data = []

    for timestamp in timestamps[:10]:  # Limit to first 10 for demo
        try:
            option_chain = client.get_option_chain(
                ticker, expiration, timestamp=timestamp
            )

            if option_chain.calls.empty and option_chain.puts.empty:
                continue

            # Get underlying price
            underlying_price = option_chain.underlying.get("regularMarketPrice", 0)

            # Calculate some metrics
            calls_volume = (
                option_chain.calls["volume"].sum()
                if not option_chain.calls.empty
                else 0
            )
            puts_volume = (
                option_chain.puts["volume"].sum() if not option_chain.puts.empty else 0
            )
            total_volume = calls_volume + puts_volume

            # Find ATM options
            if not option_chain.calls.empty and underlying_price > 0:
                calls_df = option_chain.calls.copy()
                calls_df["distance_from_atm"] = abs(
                    calls_df["strike"] - underlying_price
                )
                atm_call = calls_df.loc[calls_df["distance_from_atm"].idxmin()]
                atm_call_iv = atm_call.get("impliedVolatility", 0)
            else:
                atm_call_iv = 0

            historical_data.append(
                {
                    "timestamp": timestamp,
                    "underlying_price": underlying_price,
                    "calls_volume": calls_volume,
                    "puts_volume": puts_volume,
                    "total_volume": total_volume,
                    "put_call_ratio": (
                        puts_volume / calls_volume if calls_volume > 0 else 0
                    ),
                    "atm_call_iv": atm_call_iv,
                }
            )

        except Exception as e:
            print(f"⚠️  Error processing {timestamp}: {e}")
            continue

    if not historical_data:
        print("❌ No valid historical data found")
        return

    # Convert to DataFrame for analysis
    df = pd.DataFrame(historical_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    print("📈 Historical Analysis Summary:")
    print("-" * 30)
    print(f"Average underlying price: ${df['underlying_price'].mean():.2f}")
    print(
        f"Price range: ${df['underlying_price'].min():.2f} - ${df['underlying_price'].max():.2f}"
    )
    print(f"Average total volume: {df['total_volume'].mean():,.0f}")
    print(f"Average put/call ratio: {df['put_call_ratio'].mean():.2f}")
    print(f"Average ATM call IV: {df['atm_call_iv'].mean():.4f}")
    print()

    # Show recent data
    print("🕒 Recent Snapshots:")
    print("-" * 20)
    for _, row in df.tail(5).iterrows():
        time_str = row["timestamp"].strftime("%Y-%m-%d %H:%M")
        print(
            f"{time_str}: ${row['underlying_price']:.2f}, Vol: {row['total_volume']:,.0f}, P/C: {row['put_call_ratio']:.2f}"
        )

    # Simple visualization if matplotlib is available
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))

        # Underlying price over time
        ax1.plot(df["timestamp"], df["underlying_price"])
        ax1.set_title(f"{ticker} Underlying Price")
        ax1.set_ylabel("Price ($)")
        ax1.tick_params(axis="x", rotation=45)

        # Volume over time
        ax2.plot(df["timestamp"], df["total_volume"])
        ax2.set_title("Total Options Volume")
        ax2.set_ylabel("Volume")
        ax2.tick_params(axis="x", rotation=45)

        # Put/Call Ratio
        ax3.plot(df["timestamp"], df["put_call_ratio"])
        ax3.set_title("Put/Call Ratio")
        ax3.set_ylabel("P/C Ratio")
        ax3.tick_params(axis="x", rotation=45)

        # Implied Volatility
        ax4.plot(df["timestamp"], df["atm_call_iv"])
        ax4.set_title("ATM Call Implied Volatility")
        ax4.set_ylabel("IV")
        ax4.tick_params(axis="x", rotation=45)

        plt.tight_layout()
        plt.savefig(f"/tmp/{ticker}_options_analysis.png", dpi=150, bbox_inches="tight")
        print(f"📊 Chart saved to: /tmp/{ticker}_options_analysis.png")

    except ImportError:
        print("📊 Install matplotlib to see visualizations: pip install matplotlib")
    except Exception as e:
        print(f"⚠️  Chart generation failed: {e}")


def compare_current_vs_historical(ticker: str = "AAPL"):
    """Compare current options data with historical average."""
    print(f"\n🔄 Comparing current vs historical data for {ticker}")
    print("=" * 50)

    client = cyf.CachedYFClient()

    # Get current data
    current_chain = client.get_option_chain(ticker)
    if current_chain.calls.empty and current_chain.puts.empty:
        print(f"❌ No current options data for {ticker}")
        return

    current_price = current_chain.underlying.get("regularMarketPrice", 0)
    current_volume = (
        current_chain.calls["volume"].sum() + current_chain.puts["volume"].sum()
    )

    print("📊 Current Data:")
    print(f"   Price: ${current_price:.2f}")
    print(f"   Total Volume: {current_volume:,}")

    # Get historical average (if available)
    expirations = client.get_options_expirations(ticker)
    if expirations:
        timestamps = list(
            client.cache.iter_cached_option_timestamps(ticker, expirations[0])
        )
        if timestamps:
            print(f"   Historical snapshots available: {len(timestamps)}")
            print(f"   Date range: {min(timestamps)[:10]} to {max(timestamps)[:10]}")
        else:
            print("   No historical data available for comparison")
    else:
        print("   No expiration data available")


if __name__ == "__main__":
    # Example usage
    print("🚀 Historical Options Analysis Example")
    print("=====================================")

    # Analyze AAPL historical data
    analyze_historical_options("AAPL")

    # Compare current vs historical
    compare_current_vs_historical("AAPL")

    print("\n💡 Tips:")
    print("1. Run market_hours_collector.py to collect historical data automatically")
    print(
        "2. All downloads now automatically include timestamps for historical tracking"
    )
    print("3. Historical data builds up over time - be patient!")
    print("4. Install matplotlib for visualizations: pip install matplotlib")
