#!/usr/bin/env python3
"""
Advanced IWM ETF Analysis Example using cached-yfinance.

This example demonstrates advanced usage of cached-yfinance for comprehensive
financial analysis of IWM (iShares Russell 2000 ETF), including:
- High-frequency 1-minute data analysis
- Daily aggregation and trend analysis
- Intraday trading patterns
- Volatility and performance metrics
- Cache optimization for large datasets

IWM tracks the Russell 2000 Index, which measures the performance of the
small-cap segment of the U.S. equity universe.

Usage:
    python iwm_analysis.py
"""

from datetime import datetime, timedelta

import pandas as pd

import cached_yfinance as cyf


def analyze_iwm_data() -> bool:
    """Download and analyze IWM 1-minute data."""
    print("🏦 IWM (iShares Russell 2000 ETF) Analysis")
    print("=" * 50)

    # Initialize cached client
    client = cyf.CachedYFClient()

    # Download 60 days of 1-minute data for IWM
    print("📈 Downloading 60 days of 1-minute data for IWM...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    try:
        data = client.download(
            "IWM", start=start_date, end=end_date, interval="1m", progress=True
        )

        if data.empty:
            print("❌ No data found for IWM")
            return False

        print(f"✅ Downloaded {len(data):,} data points")
        print(f"📅 Date range: {data.index[0]} to {data.index[-1]}")

        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        # Basic statistics
        print("\n📊 Basic Statistics:")
        print(f"   Current Price: ${data['Close'].iloc[-1]:.2f}")
        print(f"   60-day High:   ${data['High'].max():.2f}")
        print(f"   60-day Low:    ${data['Low'].min():.2f}")
        print(f"   Average Volume: {data['Volume'].mean():,.0f}")
        print(f"   Total Volume:   {data['Volume'].sum():,.0f}")

        # Daily aggregation for trend analysis
        print("\n📈 Daily Trend Analysis:")
        daily_data = (
            data.resample("D")
            .agg(
                {
                    "Open": "first",
                    "High": "max",
                    "Low": "min",
                    "Close": "last",
                    "Volume": "sum",
                }
            )
            .dropna()
        )

        # Calculate daily returns
        daily_data["Daily_Return"] = daily_data["Close"].pct_change()
        daily_data["Daily_Range"] = daily_data["High"] - daily_data["Low"]

        print(f"   Trading Days: {len(daily_data)}")
        print(f"   Avg Daily Return: {daily_data['Daily_Return'].mean()*100:.2f}%")
        print(f"   Daily Volatility: {daily_data['Daily_Return'].std()*100:.2f}%")
        print(f"   Avg Daily Range: ${daily_data['Daily_Range'].mean():.2f}")

        # Recent performance
        print("\n📋 Last 5 Trading Days:")
        recent_daily = daily_data.tail().round(2)
        recent_daily["Return_%"] = (recent_daily["Daily_Return"] * 100).round(2)
        print(recent_daily[["Open", "High", "Low", "Close", "Volume", "Return_%"]])

        # Intraday patterns
        print("\n⏰ Intraday Patterns (Average by Hour):")
        data["Hour"] = data.index.to_series().dt.hour
        hourly_avg = (
            data.groupby("Hour")
            .agg({"Volume": "mean", "High": "mean", "Low": "mean", "Close": "mean"})
            .round(2)
        )

        # Show market hours only (9:30 AM - 4:00 PM ET)
        market_hours = hourly_avg.loc[9:16]  # 9 AM to 4 PM
        print("   Hour  | Avg Volume | Avg High | Avg Low  | Avg Close")
        print("   ------|------------|----------|----------|----------")
        for hour, row in market_hours.iterrows():
            hour_display = f"{hour}:30" if hour == 9 else f"{hour}:00"
            print(
                f"   {hour_display:5} | {row['Volume']:10,.0f} | ${row['High']:7.2f} | ${row['Low']:7.2f} | ${row['Close']:8.2f}"
            )

        # Cache information
        cache_path = client.cache.root / "IWM" / "1m"
        if cache_path.exists():
            cache_files = list(cache_path.rglob("*.parquet"))
            total_size = sum(f.stat().st_size for f in cache_files)
            print("\n💾 Cache Information:")
            print(f"   Location: {cache_path}")
            print(f"   Files: {len(cache_files)} parquet files")
            print(f"   Size: {total_size / 1024 / 1024:.1f} MB")

        print("\n🎯 Analysis Complete!")
        print(
            "💡 Tip: Run this script again to see how caching speeds up data retrieval!"
        )

    except Exception as e:
        print(f"❌ Error analyzing IWM data: {e}")
        return False

    return True


def main() -> None:
    """Main entry point."""
    print("=== Advanced IWM ETF Analysis Example ===\n")
    print("This example demonstrates advanced cached-yfinance usage with:")
    print("- High-frequency 1-minute data (60 days)")
    print("- Comprehensive financial analysis")
    print("- Intraday trading pattern analysis")
    print("- Cache optimization for large datasets")
    print()

    success = analyze_iwm_data()

    if success:
        print("\n" + "=" * 50)
        print("🚀 Example completed successfully!")
        print("📚 This demonstrates how cached-yfinance can handle")
        print("   large datasets efficiently with intelligent caching.")
    else:
        print("\n❌ Example failed. Please check your internet connection")
        print("   and ensure the cached-yfinance package is properly installed.")


if __name__ == "__main__":
    main()
