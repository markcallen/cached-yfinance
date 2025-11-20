#!/usr/bin/env python3
"""
Portfolio analysis example using cached-yfinance.

This example demonstrates how to use cached-yfinance for portfolio analysis,
showing how caching can significantly speed up repeated analysis runs.
"""

import cached_yfinance as cyf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calculate_portfolio_metrics(returns):
    """Calculate basic portfolio metrics."""
    annual_return = returns.mean() * 252
    annual_volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
    
    return {
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe_ratio
    }


def main():
    """Demonstrate portfolio analysis with cached-yfinance."""
    print("=== Portfolio Analysis Example ===\n")
    
    # Define a sample portfolio
    portfolio = {
        'AAPL': 0.25,  # 25% Apple
        'GOOGL': 0.20, # 20% Google
        'MSFT': 0.20,  # 20% Microsoft
        'TSLA': 0.15,  # 15% Tesla
        'SPY': 0.20,   # 20% S&P 500 ETF
    }
    
    print("Portfolio composition:")
    for symbol, weight in portfolio.items():
        print(f"  {symbol}: {weight*100:.1f}%")
    print()
    
    # Download data for all symbols
    print("Downloading historical data...")
    start_date = "2023-01-01"
    end_date = "2024-01-01"
    
    portfolio_data = {}
    for symbol in portfolio.keys():
        print(f"  Downloading {symbol}...")
        data = cyf.download(symbol, start=start_date, end=end_date)
        portfolio_data[symbol] = data['Close']
    
    # Combine into a single DataFrame
    prices_df = pd.DataFrame(portfolio_data)
    print(f"\nDownloaded data shape: {prices_df.shape}")
    print(f"Date range: {prices_df.index[0].date()} to {prices_df.index[-1].date()}")
    print()
    
    # Calculate returns
    returns_df = prices_df.pct_change().dropna()
    
    # Calculate individual asset metrics
    print("Individual asset performance:")
    print("-" * 60)
    print(f"{'Asset':<8} {'Annual Return':<15} {'Volatility':<12} {'Sharpe Ratio':<12}")
    print("-" * 60)
    
    asset_metrics = {}
    for symbol in portfolio.keys():
        metrics = calculate_portfolio_metrics(returns_df[symbol])
        asset_metrics[symbol] = metrics
        print(f"{symbol:<8} {metrics['annual_return']:>13.2%} {metrics['annual_volatility']:>10.2%} {metrics['sharpe_ratio']:>10.2f}")
    
    print()
    
    # Calculate portfolio returns
    portfolio_weights = pd.Series(portfolio)
    portfolio_returns = (returns_df * portfolio_weights).sum(axis=1)
    portfolio_metrics = calculate_portfolio_metrics(portfolio_returns)
    
    print("Portfolio performance:")
    print(f"  Annual Return: {portfolio_metrics['annual_return']:.2%}")
    print(f"  Annual Volatility: {portfolio_metrics['annual_volatility']:.2%}")
    print(f"  Sharpe Ratio: {portfolio_metrics['sharpe_ratio']:.2f}")
    print()
    
    # Calculate cumulative returns
    cumulative_returns = (1 + portfolio_returns).cumprod()
    total_return = cumulative_returns.iloc[-1] - 1
    
    print(f"Total portfolio return for period: {total_return:.2%}")
    print()
    
    # Correlation analysis
    print("Correlation matrix:")
    correlation_matrix = returns_df.corr()
    print(correlation_matrix.round(3))
    print()
    
    # Risk contribution analysis
    print("Risk contribution analysis:")
    portfolio_variance = np.dot(portfolio_weights, np.dot(returns_df.cov() * 252, portfolio_weights))
    
    for symbol in portfolio.keys():
        weight = portfolio_weights[symbol]
        # Marginal contribution to risk
        marginal_contrib = np.dot(returns_df.cov() * 252, portfolio_weights)[symbol]
        risk_contrib = weight * marginal_contrib / portfolio_variance
        print(f"  {symbol}: {risk_contrib:.2%} risk contribution (weight: {weight:.1%})")
    print()
    
    # Demonstrate caching benefit for repeated analysis
    print("Demonstrating caching benefit for repeated analysis...")
    import time
    
    # Simulate running the analysis multiple times (e.g., for backtesting)
    analysis_periods = [
        ("2023-01-01", "2023-06-30"),
        ("2023-07-01", "2023-12-31"),
        ("2023-04-01", "2023-09-30"),
    ]
    
    total_time = 0
    for i, (start, end) in enumerate(analysis_periods, 1):
        print(f"  Analysis run {i}: {start} to {end}")
        start_time = time.time()
        
        # Download data for this period
        period_data = {}
        for symbol in portfolio.keys():
            data = cyf.download(symbol, start=start, end=end)
            period_data[symbol] = data['Close']
        
        # Quick analysis
        period_prices = pd.DataFrame(period_data)
        period_returns = period_prices.pct_change().dropna()
        period_portfolio_returns = (period_returns * portfolio_weights).sum(axis=1)
        period_metrics = calculate_portfolio_metrics(period_portfolio_returns)
        
        elapsed = time.time() - start_time
        total_time += elapsed
        
        print(f"    Return: {period_metrics['annual_return']:>8.2%}, "
              f"Volatility: {period_metrics['annual_volatility']:>8.2%}, "
              f"Time: {elapsed:.3f}s")
    
    print(f"\nTotal time for {len(analysis_periods)} analysis runs: {total_time:.3f}s")
    print(f"Average time per analysis: {total_time/len(analysis_periods):.3f}s")
    print("\nNote: Subsequent runs will be faster due to caching!")


if __name__ == "__main__":
    main()
