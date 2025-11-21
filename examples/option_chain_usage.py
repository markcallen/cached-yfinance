#!/usr/bin/env python3
"""
Option Chain Usage Examples

This example demonstrates how to use cached-yfinance to fetch and cache option chain data.
Option chains include calls, puts, and underlying stock information for various expiration dates.
"""


import cached_yfinance as cyf


def basic_option_chain_example() -> None:
    """Basic option chain usage - fetch nearest expiration."""
    print("=== Basic Option Chain Example ===")

    # Get option chain for AAPL (nearest expiration)
    option_chain = cyf.get_option_chain("AAPL")

    print(f"Calls: {len(option_chain.calls)} contracts")
    print(f"Puts: {len(option_chain.puts)} contracts")
    print(
        f"Underlying price: ${option_chain.underlying.get('regularMarketPrice', 'N/A')}"
    )

    if not option_chain.calls.empty:
        print("\nSample call options:")
        print(
            option_chain.calls[
                ["strike", "lastPrice", "bid", "ask", "volume", "openInterest"]
            ].head()
        )

    if not option_chain.puts.empty:
        print("\nSample put options:")
        print(
            option_chain.puts[
                ["strike", "lastPrice", "bid", "ask", "volume", "openInterest"]
            ].head()
        )


def expiration_dates_example() -> None:
    """Get available expiration dates for a ticker."""
    print("\n=== Available Expiration Dates ===")

    # Get all available expiration dates
    expirations = cyf.get_options_expirations("AAPL")
    print(f"Available expirations for AAPL: {len(expirations)} dates")
    print("First 5 expirations:", expirations[:5])

    # Get option chain for specific expiration
    if len(expirations) > 1:
        specific_exp = expirations[1]  # Second expiration
        print(f"\nOption chain for {specific_exp}:")
        option_chain = cyf.get_option_chain("AAPL", expiration=specific_exp)
        print(f"  Calls: {len(option_chain.calls)} contracts")
        print(f"  Puts: {len(option_chain.puts)} contracts")


def advanced_option_analysis() -> None:
    """Advanced option chain analysis."""
    print("\n=== Advanced Option Analysis ===")

    # Get option chain
    option_chain = cyf.get_option_chain("AAPL")

    if option_chain.calls.empty or option_chain.puts.empty:
        print("No option data available")
        return

    # Find at-the-money options
    current_price = option_chain.underlying.get("regularMarketPrice", 0)
    if current_price:
        print(f"Current stock price: ${current_price:.2f}")

        # Find closest strike to current price
        calls = option_chain.calls.copy()
        puts = option_chain.puts.copy()

        calls["distance_from_atm"] = abs(calls["strike"] - current_price)
        puts["distance_from_atm"] = abs(puts["strike"] - current_price)

        atm_call = calls.loc[calls["distance_from_atm"].idxmin()]
        atm_put = puts.loc[puts["distance_from_atm"].idxmin()]

        print(f"\nAt-the-money call (${atm_call['strike']:.2f} strike):")
        print(f"  Last Price: ${atm_call['lastPrice']:.2f}")
        print(f"  Bid/Ask: ${atm_call['bid']:.2f}/${atm_call['ask']:.2f}")
        print(f"  Volume: {atm_call['volume']}")
        print(f"  Open Interest: {atm_call['openInterest']}")
        print(f"  Implied Volatility: {atm_call['impliedVolatility']:.4f}")

        print(f"\nAt-the-money put (${atm_put['strike']:.2f} strike):")
        print(f"  Last Price: ${atm_put['lastPrice']:.2f}")
        print(f"  Bid/Ask: ${atm_put['bid']:.2f}/${atm_put['ask']:.2f}")
        print(f"  Volume: {atm_put['volume']}")
        print(f"  Open Interest: {atm_put['openInterest']}")
        print(f"  Implied Volatility: {atm_put['impliedVolatility']:.4f}")


def option_chain_with_custom_cache() -> None:
    """Use option chains with custom cache configuration."""
    print("\n=== Custom Cache Configuration ===")

    # Create custom cache
    from cached_yfinance import CachedYFClient, FileSystemCache

    cache = FileSystemCache("~/my_options_cache")
    client = CachedYFClient(cache)

    # Get option chain using custom client
    option_chain = client.get_option_chain("TSLA")

    print("TSLA option chain (custom cache):")
    print(f"  Calls: {len(option_chain.calls)} contracts")
    print(f"  Puts: {len(option_chain.puts)} contracts")

    # List cached expiration dates
    cached_expirations = list(cache.iter_cached_option_expirations("TSLA"))
    print(f"  Cached expirations: {cached_expirations}")


def option_greeks_analysis() -> None:
    """Analyze option Greeks and other metrics."""
    print("\n=== Option Greeks Analysis ===")

    option_chain = cyf.get_option_chain("AAPL")

    if option_chain.calls.empty:
        print("No call options available")
        return

    calls = option_chain.calls.copy()

    # Filter for options with reasonable volume
    active_calls = calls[calls["volume"] > 0].copy()

    if active_calls.empty:
        print("No active call options found")
        return

    print(f"Active call options: {len(active_calls)}")
    print("\nTop 5 by volume:")
    top_volume = active_calls.nlargest(5, "volume")
    print(
        top_volume[
            ["strike", "lastPrice", "volume", "openInterest", "impliedVolatility"]
        ]
    )

    print("\nTop 5 by open interest:")
    top_oi = active_calls.nlargest(5, "openInterest")
    print(
        top_oi[["strike", "lastPrice", "volume", "openInterest", "impliedVolatility"]]
    )


def caching_performance_demo() -> None:
    """Demonstrate caching performance benefits."""
    print("\n=== Caching Performance Demo ===")

    import time

    # First call (will fetch from yfinance)
    start_time = time.time()
    option_chain1 = cyf.get_option_chain("AAPL", use_cache=False)
    first_call_time = time.time() - start_time

    # Second call (will use cache)
    start_time = time.time()
    option_chain2 = cyf.get_option_chain("AAPL", use_cache=True)
    second_call_time = time.time() - start_time

    print(f"First call (no cache): {first_call_time:.3f} seconds")
    print(f"Second call (cached): {second_call_time:.3f} seconds")

    if second_call_time > 0:
        speedup = first_call_time / second_call_time
        print(f"Speedup: {speedup:.1f}x faster")

    # Verify data is identical
    calls_equal = option_chain1.calls.equals(option_chain2.calls)
    puts_equal = option_chain1.puts.equals(option_chain2.puts)
    print(f"Data integrity: Calls match: {calls_equal}, Puts match: {puts_equal}")


if __name__ == "__main__":
    print("Cached YFinance - Option Chain Examples")
    print("=" * 50)

    try:
        basic_option_chain_example()
        expiration_dates_example()
        advanced_option_analysis()
        option_chain_with_custom_cache()
        option_greeks_analysis()
        caching_performance_demo()

    except Exception as e:
        print(f"Error running examples: {e}")
        print(
            "Make sure you have an internet connection and the required dependencies installed."
        )

    print("\n" + "=" * 50)
    print("Examples completed!")
