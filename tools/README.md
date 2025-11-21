# Cached YFinance Tools

This directory contains utility tools for downloading and managing financial data using the cached-yfinance library.

## 🛠️ Available Tools

### 1. `download_1m_data.py` - 1-Minute Data Downloader

Downloads 1-minute historical data for any ticker symbol going back a specified number of days (default: 60 days).

**Usage:**

```bash
python download_1m_data.py TICKER [--days DAYS] [--cache-dir CACHE_DIR]
```

**Examples:**

```bash
# Download 60 days of IWM data (default)
python download_1m_data.py IWM

# Download 30 days of AAPL data
python download_1m_data.py AAPL --days 30

# Use custom cache directory
python download_1m_data.py TSLA --cache-dir ~/my_finance_cache
```

**Features:**

- ✅ Downloads and caches 1-minute data efficiently
- ✅ Displays summary statistics and recent data
- ✅ Shows cache location and file count
- ✅ Handles errors gracefully
- ✅ Progress indicators

### 2. `download_options_data.py` - Options Chain Data Downloader

Downloads option chain data for any ticker symbol, including calls, puts, and underlying stock information.

**Usage:**

```bash
python download_options_data.py TICKER [--expiration EXPIRATION] [--all-expirations] [--list-expirations] [--cache-dir CACHE_DIR]
```

**Examples:**

```bash
# Download nearest expiration option chain for AAPL
python download_options_data.py AAPL

# Download specific expiration date
python download_options_data.py AAPL --expiration 2024-01-19

# Download ALL available expirations (including expired ones) using direct yfinance approach
python download_options_data.py TSLA --all-expirations

# List ALL available expiration dates (raw ticker.options result from yfinance)
python download_options_data.py IWM --list-expirations

# Use custom cache directory
python download_options_data.py AAPL --cache-dir ~/my_options_cache

# All downloads automatically include timestamps for historical tracking
python download_options_data.py AAPL

# Download all expirations (all with automatic timestamps)
python download_options_data.py SPY --all-expirations
```

**Features:**

- ✅ Downloads and caches option chain data efficiently
- ✅ Supports specific expiration dates or all available expirations
- ✅ **Automatic timestamped storage for historical options data tracking**
- ✅ Displays comprehensive option statistics (volume, open interest, IV)
- ✅ Shows at-the-money analysis and top active contracts
- ✅ Lists available expiration dates with days until expiry
- ✅ Shows cache location and file count
- ✅ Handles errors gracefully

### 3. `market_hours_collector.py` - Automated Market Hours Data Collection

**NEW!** Automated script designed for cron execution to collect options data every 15 minutes during market hours (9:30 AM - 4:00 PM EST, weekdays). Perfect for building historical options datasets.

**Usage:**

```bash
python market_hours_collector.py [--config CONFIG_FILE] [--cache-dir CACHE_DIR] [--force] [--dry-run]
```

**Examples:**

```bash
# Run with default configuration
python market_hours_collector.py

# Use custom configuration file
python market_hours_collector.py --config my_config.json

# Force execution (ignore market hours check)
python market_hours_collector.py --force

# Dry run (show what would be collected)
python market_hours_collector.py --dry-run
```

**Configuration File Format (JSON):**

```json
{
  "tickers": ["SPY", "QQQ", "IWM", "AAPL", "TSLA"],
  "cache_dir": null,
  "log_file": "/tmp/market_collector.log",
  "timezone": "America/New_York",
  "market_open": "09:30",
  "market_close": "16:00",
  "max_expirations": 5
}
```

**Features:**

- ✅ **Automatic market hours detection** (weekdays 9:30 AM - 4:00 PM EST)
- ✅ **Timestamped historical data storage** for building time series
- ✅ **Configurable ticker lists** and collection parameters
- ✅ **Comprehensive logging** with rotation support
- ✅ **Error handling and recovery** for reliable automation
- ✅ **Dry run mode** for testing configurations
- ✅ **Multiple timezone support** for different markets

### 4. `setup_cron.sh` - Easy Cron Job Setup

**NEW!** Interactive script to help set up automated options data collection via cron.

**Usage:**

```bash
./setup_cron.sh
```

**Features:**

- ✅ **Interactive setup** with validation
- ✅ **Automatic cron job generation** (every 15 minutes during market hours)
- ✅ **Configuration testing** before installation
- ✅ **Backup existing crontab** for safety
- ✅ **Helpful monitoring commands** and next steps

## 🔄 Automated Data Updates with Cron

To keep your cache up-to-date with fresh data, you can set up automated downloads using cron jobs.

### Quick Setup (Recommended)

**Use the automated setup script for options data collection:**

```bash
./setup_cron.sh
```

This will set up the `market_hours_collector.py` to run every 15 minutes during market hours, automatically building historical options datasets.

### Manual Cron Setup

1. **Open your crontab for editing:**

   ```bash
   crontab -e
   ```

2. **Add cron job entries** (choose the schedule that fits your needs):

#### Intraday Options Collection (NEW - Recommended for Historical Data)

Collect options data every 15 minutes during market hours to build comprehensive historical datasets:

```bash
# Automated market hours collection (every 15 minutes, 9:30 AM - 4:00 PM EST, weekdays)
*/15 9-16 * * 1-5 cd path_to_directory/cached-yfinance && python tools/market_hours_collector.py --config tools/market_collector_config.json >> /tmp/market_collector.log 2>&1
```

#### Daily Updates (Traditional)

Download fresh data every weekday at 6 PM ET (after market close):

```bash
# Download IWM data daily at 6 PM ET (weekdays only)
0 18 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py IWM --days 5 >> /tmp/iwm_download.log 2>&1

# Download multiple tickers daily
0 18 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py AAPL --days 5 >> /tmp/aapl_download.log 2>&1
0 19 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py TSLA --days 5 >> /tmp/tsla_download.log 2>&1

# Download options data daily (after market close) - timestamps are automatic
0 18 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_options_data.py AAPL >> /tmp/aapl_options.log 2>&1
0 19 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_options_data.py TSLA --all-expirations >> /tmp/tsla_options.log 2>&1
```

#### Weekly Updates

Download a full week of data every Sunday at 8 PM:

```bash
# Weekly full refresh on Sundays
0 20 * * 0 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py IWM --days 7 >> /tmp/iwm_weekly.log 2>&1
```

#### Hourly Updates (During Market Hours)

For real-time trading applications, update every hour during market hours:

```bash
# Update every hour during market hours (9:30 AM - 4 PM ET, weekdays)
30 9-16 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py IWM --days 1 >> /tmp/iwm_hourly.log 2>&1
```

### 📝 Cron Schedule Format

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### 🔧 Advanced Cron Setup

#### Using a Wrapper Script

Create a wrapper script for more complex logic:

```bash
# Create wrapper script
cat > path_to_directory/cached-yfinance/tools/update_cache.sh << 'EOF'
#!/bin/bash

# Set up environment
export PATH="/usr/local/bin:/usr/bin:/bin"

# Get the directory where this script is located and go to parent directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# List of tickers to update
TICKERS=("IWM" "AAPL" "TSLA" "SPY" "QQQ")

# Log file with timestamp
LOG_FILE="/tmp/cache_update_$(date +%Y%m%d).log"

echo "$(date): Starting cache update" >> "$LOG_FILE"

# Update each ticker (1-minute data)
for ticker in "${TICKERS[@]}"; do
    echo "$(date): Updating 1m data for $ticker" >> "$LOG_FILE"
    python tools/download_1m_data.py "$ticker" --days 5 >> "$LOG_FILE" 2>&1

    # Add delay between requests to be respectful to the API
    sleep 10
done

# Update options data for key tickers
OPTIONS_TICKERS=("AAPL" "TSLA" "SPY")
for ticker in "${OPTIONS_TICKERS[@]}"; do
    echo "$(date): Updating options data for $ticker" >> "$LOG_FILE"
    python tools/download_options_data.py "$ticker" >> "$LOG_FILE" 2>&1

    # Add delay between requests to be respectful to the API
    sleep 15
done

echo "$(date): Cache update complete" >> "$LOG_FILE"
EOF

# Make it executable
chmod +x path_to_directory/cached-yfinance/tools/update_cache.sh
```

Then add to crontab:

```bash
# Run wrapper script daily at 6 PM
0 18 * * 1-5 path_to_directory/cached-yfinance/tools/update_cache.sh
```

#### Environment Variables for Cron

If you need custom cache directories or other settings:

```bash
# Set environment variables in crontab
CACHED_YFINANCE_CACHE_DIR=/custom/cache/path
0 18 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py IWM --days 5
```

### 📊 Monitoring Cron Jobs

1. **Check cron logs:**

   ```bash
   # View system cron logs (macOS)
   log show --predicate 'process == "cron"' --last 1d

   # View your custom log files
   tail -f /tmp/iwm_download.log
   ```

2. **Test your cron job manually:**

   ```bash
   # Run the exact command from your crontab
   cd path_to_directory/cached-yfinance && python tools/download_1m_data.py IWM --days 5
   ```

3. **List active cron jobs:**
   ```bash
   crontab -l
   ```

### 🚨 Important Notes

- **Market Hours:** US stock markets are typically open 9:30 AM - 4:00 PM ET, Monday-Friday
- **Holidays:** Markets are closed on federal holidays - your cron jobs will still run but may not get new data
- **Rate Limiting:** Be respectful to Yahoo Finance's servers - don't run jobs too frequently
- **Disk Space:** Monitor your cache directory size, especially with frequent updates
- **Timezone:** Cron runs in your system's local timezone - adjust times accordingly

### 🎯 Recommended Setup

For most users, we recommend:

1. **Daily updates** after market close (6 PM ET)
2. **5-day lookback** to ensure you have recent data
3. **Separate log files** for each ticker
4. **Weekly cleanup** of old log files

```bash
# Add these to your crontab
0 18 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py IWM --days 5 >> /tmp/iwm_$(date +\%Y\%m\%d).log 2>&1

# Clean up old logs weekly (keep last 30 days)
0 2 * * 0 find /tmp -name "iwm_*.log" -mtime +30 -delete
```

This setup ensures you always have fresh data while being respectful to the data provider and managing disk space efficiently.

## 📈 Historical Options Data Structure

All options data is now automatically stored with timestamps for historical analysis:

### Directory Structure

```
~/.cache/yfinance/
├── AAPL/
│   └── options/
│       └── 2024-01-19/           # Expiration date
│           ├── calls.parquet     # Current data (no timestamp)
│           ├── puts.parquet
│           ├── metadata.json
│           └── historical/       # Timestamped historical data
│               └── 2024-01-15/   # Collection date
│                   ├── calls_093000.parquet    # 9:30 AM
│                   ├── puts_093000.parquet
│                   ├── metadata_093000.json
│                   ├── calls_094500.parquet    # 9:45 AM
│                   ├── puts_094500.parquet
│                   └── metadata_094500.json
```

### Accessing Historical Data

```python
import cached_yfinance as cyf

client = cyf.CachedYFClient()

# Get current data (latest)
current = client.get_option_chain("AAPL", "2024-01-19")

# Get historical data with specific timestamp
historical = client.get_option_chain("AAPL", "2024-01-19",
                                   timestamp="2024-01-15T09:30:00")

# List available timestamps
cache = client.cache
timestamps = cache.iter_cached_option_timestamps("AAPL", "2024-01-19")
print(list(timestamps))
```

## 🔧 Advanced Troubleshooting

### Market Hours Collector Issues

1. **Market hours detection problems:**

   ```bash
   # Test market hours detection
   python tools/market_hours_collector.py --dry-run

   # Force execution for testing
   python tools/market_hours_collector.py --force --dry-run
   ```

2. **Missing dependencies:**

   ```bash
   pip install pytz  # Required for timezone handling
   ```

3. **Configuration validation:**
   ```bash
   # Validate your config file
   python -m json.tool tools/market_collector_config.json
   ```

### Performance Monitoring

```bash
# Monitor historical data growth
du -sh ~/.cache/yfinance/*/options/*/historical/

# Count total historical snapshots
find ~/.cache/yfinance -name "*_*.parquet" | wc -l

# Check collection success rate
grep "Collection Summary" /tmp/market_collector.log | tail -10
```
