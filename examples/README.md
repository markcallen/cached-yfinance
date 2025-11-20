# Cached YFinance Examples

This directory contains examples demonstrating how to use the `cached-yfinance` package.

## Examples Overview

### 1. Basic Usage (`basic_usage.py`)
Demonstrates the simplest way to use cached-yfinance as a drop-in replacement for `yfinance.download()`.

**Features shown:**
- Simple stock data download
- Using different time periods and date ranges
- Intraday data fetching
- Caching performance benefits

**Run with:**
```bash
python basic_usage.py
```

### 2. Advanced Usage (`advanced_usage.py`)
Shows more advanced features and configuration options.

**Features shown:**
- Custom cache locations
- Using the `CachedYFClient` class directly
- Cache inspection and management
- Working with cache keys
- Performance comparisons
- Cache statistics

**Run with:**
```bash
python advanced_usage.py
```

### 3. Portfolio Analysis (`portfolio_analysis.py`)
Demonstrates using cached-yfinance for financial analysis and portfolio management.

**Features shown:**
- Multi-asset portfolio analysis
- Performance metrics calculation
- Correlation analysis
- Risk contribution analysis
- Repeated analysis with caching benefits

**Run with:**
```bash
python portfolio_analysis.py
```

### 4. Advanced IWM ETF Analysis (`iwm_analysis.py`)
Comprehensive analysis of IWM (iShares Russell 2000 ETF) using high-frequency data.

**Features shown:**
- High-frequency 1-minute data analysis (60 days)
- Daily aggregation and trend analysis
- Intraday trading patterns by hour
- Volatility and performance metrics
- Cache optimization for large datasets
- Market hours analysis
- Professional formatted output

**Run with:**
```bash
python iwm_analysis.py
```

**Detailed Features:**
- 📊 Basic price and volume statistics
- 📈 Daily trend analysis with returns and volatility
- ⏰ Intraday patterns by hour (market hours analysis)
- 💾 Cache usage information and optimization
- 🎯 Educational example for small-cap ETF analysis

## Prerequisites

Before running the examples, make sure you have installed the package:

```bash
# Install from PyPI (when published)
pip install cached-yfinance

# Or install in development mode
pip install -e .
```

## Additional Dependencies

Some examples may require additional packages for enhanced functionality:

```bash
# For market calendar support (optional)
pip install pandas-market-calendars

# For numerical analysis (used in portfolio example)
pip install numpy
```

## Notes

- The first time you run an example, it may take longer as data is fetched from Yahoo Finance
- Subsequent runs will be much faster due to caching
- Cache files are stored in `~/.cache/yfinance/` by default
- You can customize the cache location as shown in the advanced usage example

## Troubleshooting

If you encounter issues:

1. **Import errors**: Make sure the package is properly installed
2. **Network errors**: Check your internet connection for initial data fetching
3. **Permission errors**: Ensure you have write permissions to the cache directory
4. **Data errors**: Some symbols or date ranges may not be available from Yahoo Finance

## Contributing

Feel free to contribute additional examples! Examples should:
- Be well-documented with comments
- Include error handling where appropriate
- Demonstrate specific features or use cases
- Be runnable as standalone scripts
