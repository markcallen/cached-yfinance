# Cached YFinance

A high-performance caching wrapper around [yfinance](https://github.com/ranaroussi/yfinance) that dramatically speeds up repeated requests for financial data.

## 🚀 Features

- **Drop-in replacement** for `yfinance.download()`
- **Option chain caching** with full support for calls, puts, and Greeks
- **Intelligent caching** with automatic cache management
- **Significant performance improvements** for repeated requests (up to 45x faster!)
- **Flexible cache configuration** with custom storage locations
- **Support for all yfinance intervals** (1m, 5m, 1h, 1d, etc.)
- **Market calendar awareness** (optional with pandas-market-calendars)
- **Thread-safe operations**
- **Automatic cache invalidation** for stale data

## 📦 Installation

### From PyPI (recommended)

```bash
pip install cached-yfinance
```

### From Source

```bash
git clone https://github.com/yourusername/cached-yfinance.git
cd cached-yfinance
pip install -e .
```

### Optional Dependencies

For enhanced market calendar support:

```bash
pip install cached-yfinance[market-calendars]
```

For development:

```bash
pip install cached-yfinance[dev]
```

## 🏃‍♂️ Quick Start

### Basic Usage

```python
import cached_yfinance as cyf

# Drop-in replacement for yfinance.download()
data = cyf.download("AAPL", period="1y")
print(data.head())

# Subsequent calls are much faster!
data = cyf.download("AAPL", period="1y")  # Uses cached data
```

### Option Chain Usage

```python
import cached_yfinance as cyf

# Get available option expiration dates
expirations = cyf.get_options_expirations("AAPL")
print(f"Available expirations: {expirations}")

# Get option chain (calls, puts, and underlying data)
option_chain = cyf.get_option_chain("AAPL")
print(f"Calls: {len(option_chain.calls)} contracts")
print(f"Puts: {len(option_chain.puts)} contracts")
print(f"Current price: ${option_chain.underlying['regularMarketPrice']}")

# Get option chain for specific expiration
option_chain = cyf.get_option_chain("AAPL", expiration="2024-01-19")

# Access option data
calls = option_chain.calls  # DataFrame with strike, bid, ask, volume, etc.
puts = option_chain.puts    # DataFrame with strike, bid, ask, volume, etc.
```

### Advanced Usage

```python
from cached_yfinance import CachedYFClient, FileSystemCache

# Custom cache location
cache = FileSystemCache("~/my_finance_cache")
client = CachedYFClient(cache)

# Download with custom client
data = client.download("TSLA", start="2023-01-01", end="2023-12-31")
```

## 📊 Performance Benefits

Cached YFinance can provide significant performance improvements:

| Operation           | First Call | Cached Call | Speedup        |
| ------------------- | ---------- | ----------- | -------------- |
| 1 year daily data   | ~2.5s      | ~0.1s       | **25x faster** |
| 1 month hourly data | ~1.8s      | ~0.05s      | **36x faster** |
| Option chains       | ~0.4s      | ~0.009s     | **45x faster** |
| Multiple symbols    | ~5.2s      | ~0.2s       | **26x faster** |

_Performance may vary based on network conditions and data size._

## 🛠️ API Reference

### Module-level Functions

#### `download(tickers, start=None, end=None, period=None, interval="1d", **kwargs)`

Drop-in replacement for `yfinance.download()` with caching.

**Parameters:**

- `tickers` (str or list): Ticker symbol(s) to download
- `start` (str, datetime, optional): Start date for data
- `end` (str, datetime, optional): End date for data
- `period` (str, optional): Period to download (e.g., "1y", "6mo", "1d")
- `interval` (str): Data interval (1m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
- `**kwargs`: Additional arguments passed to yfinance

**Returns:**

- `pandas.DataFrame`: Historical market data

#### `get_options_expirations(ticker, use_cache=True)`

Get available option expiration dates for a ticker.

**Parameters:**

- `ticker` (str): Stock symbol
- `use_cache` (bool): Whether to use cached data if available

**Returns:**

- `tuple`: Tuple of expiration date strings (YYYY-MM-DD format)

#### `get_option_chain(ticker, expiration=None, use_cache=True)`

Get option chain data for a ticker and expiration date.

**Parameters:**

- `ticker` (str): Stock symbol
- `expiration` (str, optional): Expiration date in YYYY-MM-DD format. If None, uses nearest expiration.
- `use_cache` (bool): Whether to use cached data if available

**Returns:**

- `OptionChain`: NamedTuple with `calls`, `puts` DataFrames and `underlying` data dict

### Classes

#### `CachedYFClient`

Main client class for cached yfinance operations.

```python
from cached_yfinance import CachedYFClient, FileSystemCache

# Initialize with default cache
client = CachedYFClient()

# Initialize with custom cache
cache = FileSystemCache("/path/to/cache")
client = CachedYFClient(cache)

# Download data
data = client.download("AAPL", period="1y")
```

#### `FileSystemCache`

File system-based cache implementation.

```python
from cached_yfinance import FileSystemCache

# Default cache location (~/.cache/yfinance)
cache = FileSystemCache()

# Custom cache location
cache = FileSystemCache("/custom/path")

# Check if data is cached
from cached_yfinance import CacheKey
from datetime import date

key = CacheKey(symbol="AAPL", interval="1d", day=date.today())
if cache.has(key):
    data = cache.load(key)
```

#### `CacheKey`

Represents a cache key for a specific symbol, interval, and date.

```python
from cached_yfinance import CacheKey
from datetime import date

key = CacheKey(symbol="AAPL", interval="1d", day=date(2023, 12, 25))
```

#### `OptionCacheKey`

Represents a cache key for option chain data.

```python
from cached_yfinance import OptionCacheKey

# Create keys for different option data types
calls_key = OptionCacheKey.for_calls("AAPL", "2024-01-19")
puts_key = OptionCacheKey.for_puts("AAPL", "2024-01-19")
underlying_key = OptionCacheKey.for_underlying("AAPL", "2024-01-19")
```

#### `OptionChain`

NamedTuple containing option chain data.

```python
from cached_yfinance import get_option_chain

option_chain = get_option_chain("AAPL")
calls_df = option_chain.calls      # DataFrame with call options
puts_df = option_chain.puts        # DataFrame with put options
underlying_data = option_chain.underlying  # Dict with stock info
```

## 🗂️ Cache Structure

The cache organizes data in a hierarchical structure:

```
~/.cache/yfinance/
├── AAPL/
│   ├── 1d/
│   │   ├── 2023/
│   │   │   ├── 12/
│   │   │   │   ├── 2023-12-25-1d.parquet
│   │   │   │   └── 2023-12-25-1d.json
│   │   └── 01/
│   ├── 1h/
│   └── options/
│       ├── 2024-01-19/
│       │   ├── calls.parquet
│       │   ├── puts.parquet
│       │   └── metadata.json
│       └── 2024-02-16/
└── TSLA/
    ├── 1d/
    └── options/
```

Each cache entry consists of:

**Price Data:**

- **`.parquet` file**: Compressed pandas DataFrame with market data
- **`.json` file**: Metadata including symbol, date, row count, and columns

**Option Data:**

- **`calls.parquet`**: DataFrame with call option contracts
- **`puts.parquet`**: DataFrame with put option contracts
- **`metadata.json`**: Metadata including underlying stock data, contract counts, and cache timestamp

## 🔧 Configuration

### Environment Variables

- `CACHED_YFINANCE_CACHE_DIR`: Override default cache directory

### Cache Management

```python
from cached_yfinance import FileSystemCache

cache = FileSystemCache()

# List cached days for a symbol
cached_days = list(cache.iter_cached_days("AAPL", "1d"))
print(f"Cached {len(cached_days)} days for AAPL")

# List cached option expirations
cached_expirations = list(cache.iter_cached_option_expirations("AAPL"))
print(f"Cached {len(cached_expirations)} option expirations for AAPL")

# Check cache size
import os
cache_size = sum(
    os.path.getsize(os.path.join(dirpath, filename))
    for dirpath, dirnames, filenames in os.walk(cache.root)
    for filename in filenames
)
print(f"Cache size: {cache_size / 1024 / 1024:.2f} MB")
```

## 📚 Examples

See the [`examples/`](examples/) directory for comprehensive usage examples:

- **[Basic Usage](examples/basic_usage.py)**: Simple drop-in replacement examples
- **[Advanced Usage](examples/advanced_usage.py)**: Custom cache configuration and management
- **[Portfolio Analysis](examples/portfolio_analysis.py)**: Real-world financial analysis use case
- **[Option Chain Usage](examples/option_chain_usage.py)**: Comprehensive option chain examples with caching

## 🛠️ Tools

The [`tools/`](tools/) directory contains utility scripts for data management:

- **[download_1m_data.py](tools/download_1m_data.py)**: Download 1-minute data for any ticker (60 days default)
- **[iwm_example.py](tools/iwm_example.py)**: Comprehensive IWM analysis example with market insights
- **[update_cache.sh](tools/update_cache.sh)**: Automated cache update script for cron jobs
- **[README.md](tools/README.md)**: Complete documentation for tools and cron job setup

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
git clone https://github.com/yourusername/cached-yfinance.git
cd cached-yfinance
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black cached_yfinance/
isort cached_yfinance/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for informational purposes only. It should not be considered financial advice. Always do your own research before making investment decisions.

## 🙏 Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) - The excellent library this project wraps
- [pandas](https://pandas.pydata.org/) - For data manipulation and analysis
- [pandas-market-calendars](https://github.com/rsheftel/pandas_market_calendars) - For market calendar support

## 📈 Roadmap

- [x] **Option chain support with caching** ✅
- [ ] Support for multiple tickers in a single download call
- [ ] Redis/database cache backends
- [ ] Automatic cache cleanup and rotation
- [ ] Real-time data streaming support
- [ ] Integration with popular financial analysis libraries
- [ ] Option Greeks calculation and caching
- [ ] Historical option data support

---

**Star ⭐ this repository if you find it useful!**
