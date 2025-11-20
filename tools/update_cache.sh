#!/bin/bash

# Automated cache update script for cached-yfinance
# This script updates multiple tickers with fresh 1-minute data
# Designed to be run via cron job

# Set up environment
export PATH="/usr/local/bin:/usr/bin:/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR" || {
    echo "Error: Could not change to project directory: $PROJECT_DIR"
    exit 1
}

# Configuration
TICKERS=("IWM" "AAPL" "TSLA" "SPY" "QQQ")
DAYS=5
DELAY_BETWEEN_REQUESTS=10  # seconds
LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/cache_update_$(date +%Y%m%d).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log messages with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Function to update a single ticker
update_ticker() {
    local ticker="$1"
    log_message "Updating $ticker (${DAYS} days of 1m data)"
    
    if python tools/download_1m_data.py "$ticker" --days "$DAYS" >> "$LOG_FILE" 2>&1; then
        log_message "✅ Successfully updated $ticker"
        return 0
    else
        log_message "❌ Failed to update $ticker"
        return 1
    fi
}

# Main execution
log_message "🚀 Starting automated cache update"
log_message "📊 Tickers to update: ${TICKERS[*]}"
log_message "📅 Days of data: $DAYS"

# Track success/failure
total_tickers=${#TICKERS[@]}
successful_updates=0
failed_updates=0

# Update each ticker
for ticker in "${TICKERS[@]}"; do
    if update_ticker "$ticker"; then
        ((successful_updates++))
    else
        ((failed_updates++))
    fi
    
    # Add delay between requests to be respectful to the API
    if [ $((successful_updates + failed_updates)) -lt $total_tickers ]; then
        log_message "⏳ Waiting ${DELAY_BETWEEN_REQUESTS} seconds before next request..."
        sleep "$DELAY_BETWEEN_REQUESTS"
    fi
done

# Summary
log_message "📈 Cache update complete!"
log_message "✅ Successful updates: $successful_updates/$total_tickers"
log_message "❌ Failed updates: $failed_updates/$total_tickers"

# Exit with appropriate code
if [ "$failed_updates" -eq 0 ]; then
    log_message "🎉 All updates completed successfully"
    exit 0
else
    log_message "⚠️  Some updates failed - check logs for details"
    exit 1
fi
