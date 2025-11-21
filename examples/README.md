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
# Using uv (recommended)
uv run python basic_usage.py

# Or with regular Python
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
# Using uv (recommended)
uv run python advanced_usage.py

# Or with regular Python
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
# Using uv (recommended)
uv run python portfolio_analysis.py

# Or with regular Python
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
# Using uv (recommended)
uv run python iwm_analysis.py

# Or with regular Python
python iwm_analysis.py
```

**Detailed Features:**

- 📊 Basic price and volume statistics
- 📈 Daily trend analysis with returns and volatility
- ⏰ Intraday patterns by hour (market hours analysis)
- 💾 Cache usage information and optimization
- 🎯 Educational example for small-cap ETF analysis

### 5. Options Chain Analysis (`option_chain_usage.py`)

Demonstrates working with options data and option chains.

**Features shown:**

- Fetching options expirations
- Getting option chains for specific expirations
- Analyzing calls and puts data
- Finding at-the-money options
- Options volume and open interest analysis

**Run with:**

```bash
# Using uv (recommended)
uv run python option_chain_usage.py

# Or with regular Python
python option_chain_usage.py
```

### 6. Historical Options Analysis (`historical_options_analysis.py`)

Advanced example showing how to analyze historical options data over time using the timestamped storage feature.

**Features shown:**

- Working with historical options snapshots
- Analyzing options data trends over time
- Put/call ratio calculations
- Implied volatility tracking
- Underlying price correlation with options metrics
- Data visualization with matplotlib

**Prerequisites:**

This example requires matplotlib for visualizations. Install it using:

```bash
# Install examples dependencies (includes matplotlib)
uv sync --extra examples

# Or install matplotlib directly
uv add matplotlib
```

**Run with:**

```bash
# Using uv (recommended)
uv run python historical_options_analysis.py

# Or with regular Python (after installing dependencies)
python historical_options_analysis.py
```

**Detailed Features:**

- 📊 Historical options data analysis across multiple timestamps
- 📈 Underlying price tracking over time
- 📉 Options volume analysis (calls vs puts)
- 🔄 Put/call ratio calculations and trends
- 💹 At-the-money (ATM) implied volatility tracking
- 📊 Multi-panel visualization charts
- ⏰ Timestamp-based data retrieval
- 🔍 Current vs historical data comparison

**Note:** This example works best when you have historical data collected. Run the `market_hours_collector.py` tool first to automatically collect timestamped options data throughout trading hours.

## Installing Dependencies

### Core Dependencies

The basic examples work with just the core package:

```bash
# Install the package with core dependencies
uv sync
```

### Examples with Visualization

For examples that include charts and visualizations (like `historical_options_analysis.py`):

```bash
# Install with examples dependencies (includes matplotlib)
uv sync --extra examples
```

### Development Dependencies

For development work:

```bash
# Install with development dependencies
uv sync --extra dev
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
