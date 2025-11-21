# Cached YFinance

A high-performance caching wrapper around [yfinance](https://github.com/ranaroussi/yfinance) that dramatically speeds up repeated requests for financial data.

## 🚀 Features

- **Drop-in replacement** for `yfinance.download()`
- **Option chain caching** with full support for calls, puts, and Greeks
- **Intelligent caching** with automatic cache management
- **Significant performance improvements** for repeated requests (up to 45x faster!)
- **Flexible cache configuration** with custom storage locations
- **Support for all yfinance intervals** (1m, 5m, 1h, 1d, etc.)
- **Market calendar awareness** with pandas-market-calendars
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

#### Examples Dependencies

For running the examples with visualization support:

```bash
pip install cached-yfinance[examples]
# or
uv add cached-yfinance[examples]
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

## 🐳 Docker Usage

You can run the data download tool using Docker without installing Python dependencies locally.

### Using Pre-built Images

Pre-built Docker images are available on Docker Hub for both AMD64 and ARM64 architectures:

```bash
# Pull the latest version
docker pull markcallen/cached-yfinance:latest

# Or pull a specific version
docker pull markcallen/cached-yfinance:v0.1.0
```

### Building the Docker Image Locally

If you prefer to build the image yourself:

#### Basic Build

```bash
docker build -t cached-yfinance:local .
```

This will create an image with version label "local".

### Environment Variables

The Docker container accepts the following environment variables:

- **`TICKER`** (required): Stock ticker symbol (e.g., "AAPL", "IWM", "TSLA")
- **`INTERVAL`** (optional): Data interval, default "1d"
  - Valid values: 1m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo, 3mo
- **`DAYS`** (optional): Number of days to go back, default "60"
  - Maximum 60 for intraday intervals (intervals ending with 'm' or 'h')
- **`CACHE_DIR`** (optional): Cache directory path inside container, default "/cache"

### Usage Examples

#### Basic Usage - Daily Data

```bash
docker run --rm \
  -e TICKER=AAPL \
  -v $(pwd)/cache:/cache \
  markcallen/cached-yfinance:latest
```

#### Download 1-minute Data for 30 Days

```bash
docker run --rm \
  -e TICKER=IWM \
  -e INTERVAL=1m \
  -e DAYS=30 \
  -v $(pwd)/cache:/cache \
  markcallen/cached-yfinance:latest
```

#### Download Hourly Data for 90 Days

```bash
docker run --rm \
  -e TICKER=TSLA \
  -e INTERVAL=1h \
  -e DAYS=90 \
  -v $(pwd)/cache:/cache \
  markcallen/cached-yfinance:latest
```

#### Using Custom Cache Directory

```bash
docker run --rm \
  -e TICKER=MSFT \
  -e INTERVAL=1d \
  -e DAYS=365 \
  -v /path/to/your/cache:/cache \
  markcallen/cached-yfinance:latest
```

### Volume Mounting

Always mount a volume to `/cache` to persist the downloaded data:

```bash
-v $(pwd)/cache:/cache
```

This ensures that:

1. Downloaded data persists after the container stops
2. Subsequent runs can reuse cached data for better performance
3. You can access the cached data from your host system

### Container Output

The container provides detailed output including:

- Configuration summary
- Download progress
- Data statistics
- Cache information

Example output:

```
🐳 Starting download with:
   TICKER: AAPL
   INTERVAL: 1d
   DAYS: 60
   CACHE_DIR: /cache

📈 Downloading 60-day 1d data for AAPL...
📁 Using custom cache directory: /cache
📅 Date range: 2024-09-22 to 2024-11-21
✅ Successfully downloaded data for AAPL
📊 Data points: 43
📅 Date range: 2024-09-23 09:30 to 2024-11-20 16:00
💰 Price range: $213.92 - $237.49
📈 Latest close: $229.87
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

- **[download_data.py](tools/download_data.py)**: Download historical data for any ticker with configurable intervals
- **[iwm_example.py](tools/iwm_example.py)**: Comprehensive IWM analysis example with market insights
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
# Run all tests with coverage
uv run pytest tests/ --cov=cached_yfinance --cov-report=term-missing --cov-report=html

# Run specific test file
uv run pytest tests/test_cache.py -v

# Run specific test
uv run pytest tests/test_cache.py::TestCacheKey::test_cache_key_creation -v
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
