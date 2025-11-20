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

## 🔄 Automated Data Updates with Cron

To keep your cache up-to-date with fresh data, you can set up automated downloads using cron jobs.

### Setting Up Cron Jobs

1. **Open your crontab for editing:**

   ```bash
   crontab -e
   ```

2. **Add cron job entries** (choose the schedule that fits your needs):

#### Daily Updates (Recommended)

Download fresh data every weekday at 6 PM ET (after market close):

```bash
# Download IWM data daily at 6 PM ET (weekdays only)
0 18 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py IWM --days 5 >> /tmp/iwm_download.log 2>&1

# Download multiple tickers daily
0 18 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py AAPL --days 5 >> /tmp/aapl_download.log 2>&1
0 19 * * 1-5 cd path_to_directory/cached-yfinance && python tools/download_1m_data.py TSLA --days 5 >> /tmp/tsla_download.log 2>&1
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

# Update each ticker
for ticker in "${TICKERS[@]}"; do
    echo "$(date): Updating $ticker" >> "$LOG_FILE"
    python tools/download_1m_data.py "$ticker" --days 5 >> "$LOG_FILE" 2>&1

    # Add delay between requests to be respectful to the API
    sleep 10
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
