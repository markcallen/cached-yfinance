#!/usr/bin/env python3
"""
Example Usage of Options Data Retrieval

This example shows how to use the get_all_options.py script and
the cached_yfinance library to work with options data.
"""

import sys
from pathlib import Path


# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

import cached_yfinance as cyf


def example_options_workflow():
    """Example workflow for working with options data."""

    print("🚀 Options Data Workflow Example")
    print("=" * 50)

    # Initialize client
    client = cyf.CachedYFClient()
    ticker = "AAPL"

    # Step 1: Get available expiration dates
    print(f"\n📅 Step 1: Getting expiration dates for {ticker}")
    expirations = client.get_options_expirations(ticker)
    print(f"Found {len(expirations)} expiration dates")

    if expirations:
        print("First 5 expirations:", expirations[:5])

        # Step 2: Get options data for the nearest expiration
        print(f"\n📊 Step 2: Getting options data for {expirations[0]}")
        option_chain = client.get_option_chain(ticker, expirations[0])

        print(f"Calls: {len(option_chain.calls)} contracts")
        print(f"Puts: {len(option_chain.puts)} contracts")

        # Step 3: Analyze the data
        if not option_chain.calls.empty:
            print("\n🔍 Step 3: Sample analysis")
            underlying_price = option_chain.underlying.get("regularMarketPrice", 0)
            print(f"Underlying price: ${underlying_price}")

            # Find ATM options
            calls_df = option_chain.calls.copy()
            calls_df["distance_from_atm"] = abs(calls_df["strike"] - underlying_price)
            atm_call = calls_df.loc[calls_df["distance_from_atm"].idxmin()]

            print(f"ATM Call Strike: ${atm_call['strike']}")
            print(f"ATM Call Last Price: ${atm_call['lastPrice']}")
            print(f"ATM Call Volume: {atm_call['volume']}")

            # Show top 5 calls by volume
            top_calls = option_chain.calls.nlargest(5, "volume")
            print("\nTop 5 calls by volume:")
            for _, call in top_calls.iterrows():
                print(
                    f"  ${call['strike']}: Vol={call['volume']}, Price=${call['lastPrice']}"
                )


if __name__ == "__main__":
    example_options_workflow()
