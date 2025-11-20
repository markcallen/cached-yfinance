# Installation Guide

## Quick Installation

### From PyPI (Recommended - when published)

```bash
pip install cached-yfinance
```

### From Source (Development)

```bash
git clone https://github.com/yourusername/cached-yfinance.git
cd cached-yfinance
pip install -e .
```

### From Built Distribution

If you have the distribution files:

```bash
# Install from wheel (recommended)
pip install cached_yfinance-0.1.0-py3-none-any.whl

# Or install from source distribution
pip install cached_yfinance-0.1.0.tar.gz
```

## Building from Source

### Prerequisites

- Python 3.8 or higher
- pip (latest version recommended)

### Build Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/cached-yfinance.git
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

## Optional Dependencies

### Market Calendar Support

For enhanced market calendar functionality:

```bash
pip install pandas-market-calendars
```

### Development Dependencies

For contributing to the project:

```bash
pip install -e .[dev]
```

This installs:
- pytest (testing)
- pytest-cov (coverage)
- black (code formatting)
- isort (import sorting)
- mypy (type checking)
- ruff (linting)

## Verification

After installation, verify everything works:

```python
import cached_yfinance as cyf
print(f"Cached YFinance version: {cyf.__version__}")

# Test basic functionality
data = cyf.download("AAPL", period="5d")
print(f"Downloaded {len(data)} rows of AAPL data")
```

## Troubleshooting

### Common Issues

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

### Getting Help

- Check the [examples](examples/) directory for usage patterns
- Review the [README.md](README.md) for API documentation
- Open an issue on GitHub for bugs or feature requests

## Uninstallation

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
