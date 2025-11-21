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

## 📦 Installation

### From PyPI (recommended)

```bash
pip install cached-yfinance
```

or

```bash
uv add cached-yfinance
```

### From Source

```bash
git clone https://github.com/markcallen/cached-yfinance.git
cd cached-yfinance
uv pip install -e .
```

### From Built Distribution

If you have the distribution files:

```bash
# Install from wheel (recommended)
pip install cached_yfinance-0.1.0-py3-none-any.whl

# Or install from source distribution
pip install cached_yfinance-0.1.0.tar.gz
```

### Building from Source

#### Prerequisites

- Python 3.8 or higher
- pip (latest version recommended)

#### Build Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/markcallen/cached-yfinance.git
   cd cached-yfinance
   ```

2. **Install build dependencies:**

   ```bash
   pip install build
   ```

3. **Build the package:**

   ```bash
   python -m build
   ```

4. **Install the built package:**
   ```bash
   pip install dist/cached_yfinance-0.1.0-py3-none-any.whl
   ```

### Optional Dependencies

#### Market Calendar Support

For enhanced market calendar functionality:

```bash
pip install pandas-market-calendars
# or
uv add cached-yfinance[market-calendars]
```

#### Development Dependencies

For contributing to the project:

```bash
pip install -e .[dev]
# or
uv add cached-yfinance[dev]
```

This installs:

- pytest (testing)
- pytest-cov (coverage)
- black (code formatting)
- mypy (type checking)
- ruff (linting and import sorting)

### Installation Verification

After installation, verify everything works:

```python
import cached_yfinance as cyf
print(f"Cached YFinance version: {cyf.__version__}")

# Test basic functionality
data = cyf.download("AAPL", period="5d")
print(f"Downloaded {len(data)} rows of AAPL data")
```

### Troubleshooting

#### Common Issues

1. **Import Error: No module named 'cached_yfinance'**
   - Ensure the package is installed: `pip list | grep cached-yfinance`
   - Try reinstalling: `pip uninstall cached-yfinance && pip install cached-yfinance`

2. **Permission Denied (Cache Directory)**
   - The default cache location is `~/.cache/yfinance/`
   - Ensure you have write permissions to your home directory
   - Or use a custom cache location:
     ```python
     from cached_yfinance import CachedYFClient, FileSystemCache
     cache = FileSystemCache("/path/to/writable/directory")
     client = CachedYFClient(cache)
     ```

3. **Network Errors**
   - Cached YFinance requires internet access for initial data fetching
   - Subsequent calls use cached data and don't require network access
   - Check your internet connection and firewall settings

4. **Dependency Conflicts**
   - Use a virtual environment to avoid conflicts:
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     pip install cached-yfinance
     ```

### Uninstallation

To remove the package:

```bash
pip uninstall cached-yfinance
```

Note: This will not remove cached data. To clean up cache files:

```python
import shutil
from pathlib import Path

# Remove default cache directory
cache_dir = Path.home() / ".cache" / "yfinance"
if cache_dir.exists():
    shutil.rmtree(cache_dir)
    print(f"Removed cache directory: {cache_dir}")
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

## 📖 Documentation

For detailed technical information, see:

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete API reference, cache structure, and system architecture with diagrams

## 🔧 Configuration

### Environment Variables

- `CACHED_YFINANCE_CACHE_DIR`: Override default cache directory

For detailed cache management examples, see [ARCHITECTURE.md](ARCHITECTURE.md#configuration).

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
uv pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black cached_yfinance/
ruff check --fix cached_yfinance/
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
- [ ] Integration with popular financial analysis libraries
- [ ] Option Greeks calculation and caching

---

**Star ⭐ this repository if you find it useful!**
